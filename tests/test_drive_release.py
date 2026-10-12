"""Drive transport and optional takes fail closed at the release boundary."""
import json
import shutil
import sys
import hashlib
import zipfile
from types import SimpleNamespace

import pytest

from test_dataset_release import fixture_release, script


def drive_config(root):
    path = root / 'configs/dataset.yaml'
    config = json.loads(path.read_text())
    config['drive_file_id'] = 'public-main-id'
    path.write_text(json.dumps(config))
    return path, config


def test_drive_id_imports_verified_payload(tmp_path, monkeypatch):
    root, archive, payload = fixture_release(tmp_path)
    drive_config(root)
    def download(*, id, output, **kwargs):
        if id != 'public-main-id': raise AssertionError('Wrong Drive file ID')
        shutil.copyfile(archive, output)
        return output
    monkeypatch.setitem(sys.modules, 'gdown', SimpleNamespace(download=download))
    assert script('fetch_data').fetch(root) == 2
    for name, body in payload.items():
        assert (root / 'data' / name).read_bytes() == body


def test_bad_drive_download_installs_nothing(tmp_path, monkeypatch):
    root, _, _ = fixture_release(tmp_path)
    drive_config(root)
    def download(*, output, **kwargs):
        from pathlib import Path
        Path(output).write_bytes(b'Google HTML error or wrong archive')
        return output
    monkeypatch.setitem(sys.modules, 'gdown', SimpleNamespace(download=download))
    with pytest.raises(ValueError, match='SHA'):
        script('fetch_data').fetch(root)
    assert not (root / 'data/raw').exists()


def test_rejected_human_link_is_actionable_even_if_main_is_present(tmp_path):
    root, archive, _ = fixture_release(tmp_path)
    module = script('fetch_data')
    module.fetch(root, archive)
    path, config = drive_config(root)
    config['human_takes'] = {'status': 'upload_required'}
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='human.*from-local|from-local.*human'):
        module.fetch(root, with_human_takes=True)


@pytest.mark.parametrize('corrupt', [False, True])
def test_owner_confirmed_takes_still_require_valid_download_hash(tmp_path, monkeypatch, corrupt):
    root, main, _ = fixture_release(tmp_path)
    module = script('fetch_data')
    module.fetch(root, main)
    payload = {'human/raw/take.wav': b'consented take'}
    inventory = {'schema': 'dataset-inventory/v1', 'files': {
        name: {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
        for name, body in payload.items()}}
    archive = tmp_path / 'human.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('release_manifest.json', json.dumps(inventory))
        for name, body in payload.items(): z.writestr(name, body)
    (root / 'data/release/human.json').write_text(json.dumps(inventory))
    path, config = drive_config(root)
    config['human_takes'] = {'status': 'owner_confirmed', 'drive_file_id': 'public-human-id',
        'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'bytes': archive.stat().st_size,
        'inventory': 'data/release/human.json'}
    path.write_text(json.dumps(config))
    def download(*, id, output, **kwargs):
        if id != 'public-human-id': raise AssertionError('Wrong human Drive file ID')
        from pathlib import Path
        if corrupt: Path(output).write_bytes(b'wrong upload')
        else: shutil.copyfile(archive, output)
        return output
    monkeypatch.setitem(sys.modules, 'gdown', SimpleNamespace(download=download))
    if corrupt:
        with pytest.raises(ValueError, match='SHA'): module.fetch(root, with_human_takes=True)
        assert not (root / 'data/human').exists()
    else:
        assert module.fetch(root, with_human_takes=True) == 1
        assert (root / 'data/human/raw/take.wav').read_bytes() == b'consented take'
