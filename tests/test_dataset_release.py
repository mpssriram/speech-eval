"""Release imports fail closed, without replacing users' data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import functools
import http.server
import threading
import subprocess
import sys
import csv

import pytest


def script(name):
    path = Path(__file__).resolve().parents[1] / 'scripts' / f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_release(tmp_path, members=None):
    payload = {'raw/sample.wav': b'licensed audio', 'transcripts/sample.txt': b'hello'}
    inventory = {'schema': 'dataset-inventory/v1', 'files': {
        n: {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)} for n, b in payload.items()}}
    archive = tmp_path / 'release.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('release_manifest.json', json.dumps(inventory, sort_keys=True))
        for n, b in (members or payload).items(): z.writestr(n, b)
    root = tmp_path / 'clone'
    (root / 'configs').mkdir(parents=True)
    (root / 'data/release').mkdir(parents=True)
    (root / 'data/release/inventory.json').write_text(json.dumps(inventory))
    config = {'url': 'UPLOAD_URL_PENDING', 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'inventory': 'data/release/inventory.json'}
    (root / 'configs/dataset.yaml').write_text(json.dumps(config))
    return root, archive, payload


def test_import_and_idempotence(tmp_path):
    root, archive, payload = fixture_release(tmp_path)
    module = script('fetch_data')
    assert module.fetch(root, archive) == 2
    assert module.fetch(root) == 0
    for n, b in payload.items(): assert (root / 'data' / n).read_bytes() == b


def test_outer_corruption_installs_nothing(tmp_path):
    root, archive, _ = fixture_release(tmp_path)
    with archive.open('ab') as f: f.write(b'corruption')
    with pytest.raises(ValueError, match='SHA'): script('fetch_data').fetch(root, archive)
    assert not (root / 'data/raw').exists()


@pytest.mark.parametrize('name', ['../escape.wav', '/escape.wav', 'raw\\escape.wav', 'raw/C:escape.wav'])
def test_unsafe_or_unlisted_member_installs_nothing(tmp_path, name):
    root, archive, _ = fixture_release(tmp_path, {name: b'bad'})
    with pytest.raises(ValueError): script('fetch_data').fetch(root, archive)
    assert not (root / 'data/raw').exists()


def test_inner_corruption_installs_nothing(tmp_path):
    root, archive, _ = fixture_release(tmp_path, {'raw/sample.wav': b'changed', 'transcripts/sample.txt': b'hello'})
    with pytest.raises(ValueError): script('fetch_data').fetch(root, archive)
    assert not (root / 'data/raw').exists()


def test_existing_conflict_preserves_everything(tmp_path):
    root, archive, _ = fixture_release(tmp_path)
    existing = root / 'data/transcripts/sample.txt'
    existing.parent.mkdir(); existing.write_bytes(b'user content')
    with pytest.raises(ValueError, match='Existing'): script('fetch_data').fetch(root, archive)
    assert existing.read_bytes() == b'user content'
    assert not (root / 'data/raw').exists()


def test_symlink_parent_cannot_escape(tmp_path):
    root, archive, _ = fixture_release(tmp_path)
    outside = tmp_path / 'outside'; outside.mkdir()
    (root / 'data/raw').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'): script('fetch_data').fetch(root, archive)
    assert list(outside.iterdir()) == []


def test_missing_url_is_actionable(tmp_path):
    root, _, _ = fixture_release(tmp_path)
    with pytest.raises(ValueError, match='from-local'): script('fetch_data').fetch(root)


def test_builder_is_byte_deterministic(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'hello.txt').write_bytes(b'hello')
    module = script('build_release')
    one = tmp_path / 'one.zip'; two = tmp_path / 'two.zip'
    inventory = module.inventory_for(source, ['hello.txt'])
    module.write_archive(source, one, inventory)
    (source / 'hello.txt').touch()
    module.write_archive(source, two, inventory)
    assert one.read_bytes() == two.read_bytes()


def test_unknown_audio_provenance_is_rejected():
    with pytest.raises(ValueError, match='provenance'):
        script('build_release').audio_source('audio/hq/private__user__take01.wav', {})


def test_private_fixture_metadata_and_audio_are_excluded():
    module = script('build_release')
    assert module.release_candidate('audio/hq/gettysburg__lv_fb__orig.wav')
    assert not module.release_candidate('audio/hq/gettysburg__user__input_246ca9e90194.flac')
    assert not module.release_candidate('transcripts/as_spoken/gettysburg__user__input_246ca9e90194.txt')
    assert not module.release_candidate('human/raw/gettysburg__user__take01.wav')


@pytest.mark.parametrize('kind', ['duplicate', 'symlink'])
def test_duplicate_or_symlink_archive_is_rejected(tmp_path, kind):
    root, archive, _ = fixture_release(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        if kind == 'duplicate':
            with pytest.warns(UserWarning): z.writestr('raw/sample.wav', b'duplicate')
        else:
            # Replace the complete archive with a same-name symlink entry.
            pass
    if kind == 'symlink':
        with zipfile.ZipFile(archive) as z: payload = {i.filename: z.read(i) for i in z.infolist()}
        with zipfile.ZipFile(archive, 'w') as z:
            for name, body in payload.items():
                info = zipfile.ZipInfo(name)
                if name == 'raw/sample.wav': info.external_attr = 0o120777 << 16
                z.writestr(info, body)
    config_path = root / 'configs/dataset.yaml'
    config = json.loads(config_path.read_text())
    config['sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError): script('fetch_data').fetch(root, archive)
    assert not (root / 'data/raw').exists()


def test_download_from_config_verifies_and_installs(tmp_path):
    root, archive, payload = fixture_release(tmp_path)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    config_path = root / 'configs/dataset.yaml'
    config = json.loads(config_path.read_text())
    config['url'] = f'http://127.0.0.1:{server.server_port}/{archive.name}'
    config_path.write_text(json.dumps(config))
    try:
        assert script('fetch_data').fetch(root) == len(payload)
    finally:
        server.shutdown(); server.server_close(); thread.join()


def test_killed_install_can_be_retried_without_partial_destination(tmp_path):
    root, archive, payload = fixture_release(tmp_path)
    module_path = Path(__file__).resolve().parents[1] / 'scripts/fetch_data.py'
    program = '''
import importlib.util, os, pathlib, shutil, signal, sys
spec=importlib.util.spec_from_file_location('fetcher',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
original=shutil.copyfileobj
def interrupted(source,destination,*args):
    if str(destination.name).startswith(str(pathlib.Path(sys.argv[2])/'data')):
        destination.write(b'partial');destination.flush()
        os.kill(os.getpid(),signal.SIGKILL)
    return original(source,destination,*args)
shutil.copyfileobj=interrupted
module.fetch(pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]))
'''
    result = subprocess.run([sys.executable, '-c', program, str(module_path), str(root), str(archive)])
    assert result.returncode != 0
    for name in payload: assert not (root / 'data' / name).exists()
    assert script('fetch_data').fetch(root, archive) == len(payload)


def test_missing_required_measurement_provenance_blocks_archive(tmp_path, monkeypatch):
    module = script('build_release'); data = tmp_path / 'data'
    rid = 'gettysburg__lv_fb__orig'
    for name, body in {
        'release/licences.json': json.dumps({'included': [{'source_id': 'licensed', 'evidence_urls': ['https://example.org']}]}),
        'review/final_evaluation.json': '{"inputs": {}}',
        'raw/source.mp3': 'audio', 'audio/hq/' + rid + '.wav': 'audio',
        'features/speaker_stats/' + rid + '.json': '{}',
        **{f'features/{folder}/{rid}.parquet': 'features' for folder in ('frames', 'words', 'windows', 'sentences')}
    }.items():
        path = data / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(body)
    manifest = data / 'manifest'; manifest.mkdir()
    with (manifest / 'raw_files.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=['recording_id', 'source_id', 'raw_path', 'sha256']); w.writeheader()
        w.writerow({'recording_id': rid, 'source_id': 'licensed', 'raw_path': 'data/raw/source.mp3',
                    'sha256': hashlib.sha256(b'audio').hexdigest()})
    with (manifest / 'dataset_index.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=['recording_id', 'audio_path']); w.writeheader()
        w.writerow({'recording_id': rid, 'audio_path': 'data/audio/hq/' + rid + '.wav'})
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *a, **k: b'')
    with pytest.raises(ValueError, match='provenance'):
        module.build(tmp_path, tmp_path / 'release.zip', write_metadata=False)
    alignment = data / 'alignment' / f'{rid}.json'; alignment.parent.mkdir()
    alignment.write_text(json.dumps({'audio': f'data/audio/hq/{rid}.wav'}))
    proof = {'inputs': {'recordings': {rid: {
        'audio': module.sha(data / 'audio/hq' / f'{rid}.wav'), 'alignment': module.sha(alignment)}}},
        'artifacts': {f'data/features/{folder}/{rid}.{extension}': module.sha(data / 'features' / folder / f'{rid}.{extension}')
                      for folder, extension in [('frames', 'parquet'), ('words', 'parquet'), ('windows', 'parquet'),
                                                ('sentences', 'parquet'), ('speaker_stats', 'json')]}}
    (data / 'features/provenance.json').write_text(json.dumps(proof))
    assert module.build(tmp_path, tmp_path / 'covered.zip', write_metadata=False)['payload_files'] >= 9
