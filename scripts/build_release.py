"""Deterministic archive of licensed frozen inputs; never package private uploads."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

AUDIO = {'.wav', '.flac', '.mp3', '.ogg', '.m4a'}


def release_candidate(name: str) -> bool:
    return '__user__' not in name and not name.startswith(('human/', 'app/', 'rating_pack/'))


def source_proof_covers(data: Path, rid: str) -> bool:
    path = data / 'features/provenance.json'
    if not path.is_file(): return False
    saved = json.loads(path.read_text())
    recording = saved.get('inputs', {}).get('recordings', {}).get(rid)
    if recording is None: return False
    alignment_path = data / 'alignment' / f'{rid}.json'
    alignment = json.loads(alignment_path.read_text())
    if recording != {'alignment': sha(alignment_path), 'audio': sha(data.parent / alignment['audio'])}:
        return False
    outputs = [f'data/features/{folder}/{rid}.parquet' for folder in ('frames', 'words', 'windows', 'sentences')]
    outputs.append(f'data/features/speaker_stats/{rid}.json')
    return all(saved.get('artifacts', {}).get(name) == sha(data.parent / name) for name in outputs)


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def audio_source(name: str, originals: dict) -> str:
    if name.startswith('raw/'):
        candidates = [row['source_id'] for row in originals.values() if row['raw_path'] == 'data/' + name]
        if len(set(candidates)) == 1: return candidates[0]
    else:
        parts = Path(name).stem.split('__', 2)
        if len(parts) == 3:
            original = f'{parts[0]}__{parts[1]}__orig'
            if original in originals: return originals[original]['source_id']
    raise ValueError(f'No approved audio provenance: {name}')


def inventory_for(data: Path, names: list[str]) -> dict:
    files = {}
    for name in sorted(set(names)):
        path = data / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(data.resolve()):
            raise ValueError(f'Missing or unsafe release input: {name}')
        files[name] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    return {'schema': 'dataset-inventory/v1', 'files': files}


def canonical(payload):
    return (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def write_archive(data: Path, output: Path, inventory: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', allowZip64=True) as z:
        for name in sorted([*inventory['files'], 'release_manifest.json']):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            # Compressed audio stays stored; metadata/Parquet deflates deterministically.
            info.compress_type = zipfile.ZIP_STORED if Path(name).suffix in AUDIO else zipfile.ZIP_DEFLATED
            with z.open(info, 'w', force_zip64=True) as destination:
                if name == 'release_manifest.json': destination.write(canonical(inventory))
                else:
                    import shutil
                    with (data / name).open('rb') as source: shutil.copyfileobj(source, destination, 1024 * 1024)
            if name in inventory['files'] and sha(data / name) != inventory['files'][name]['sha256']:
                raise ValueError(f'Release input changed during archive build: {name}')


def build(root: Path, output: Path, write_metadata: bool = True) -> dict:
    data = root / 'data'
    ledger = json.loads((data / 'release/licences.json').read_text())
    approved = {s['source_id'] for s in ledger['included'] if s['evidence_urls']}
    originals = {r['recording_id']: r for r in csv.DictReader((data / 'manifest/raw_files.csv').open())}
    rows = list(csv.DictReader((data / 'manifest/dataset_index.csv').open()))
    frozen = json.loads((data / 'review/final_evaluation.json').read_text())
    names = {n.removeprefix('data/') for n in frozen['inputs']}
    tracked = subprocess.check_output(['git', 'ls-files', '-z', 'data'], cwd=root).decode().split('\0')
    permitted = ('data/manifest/', 'data/transcripts/', 'data/alignment/', 'data/labels/',
                 'data/flawed/timemaps/', 'data/reference/', 'data/dictionaries/', 'data/gold/', 'data/review/')
    names.update(n.removeprefix('data/') for n in tracked if n.startswith(permitted))
    names.add('release/licences.json')
    for row in originals.values():
        if row['source_id'] in approved:
            name = row['raw_path'].removeprefix('data/')
            if sha(data / name) != row['sha256']: raise ValueError(f'Immutable raw checksum differs: {name}')
            names.add(name)
    for row in rows:
        rid = row['recording_id']; names.add(row['audio_path'].removeprefix('data/'))
        names.update(f'features/{folder}/{rid}.parquet' for folder in ('frames', 'words', 'windows', 'sentences'))
        names.add(f'features/speaker_stats/{rid}.json')
        text, speaker, _ = rid.split('__', 2)
        proof = f'.cache/dataset/{text}__{speaker}__orig/features.json'
        if (data / proof).is_file(): names.add(proof)
        elif source_proof_covers(data, rid): names.add('features/provenance.json')
        else:
            raise ValueError(f'Missing required measurement provenance: {proof}')
    # The old freeze enumerated an unused participant fixture as well as dataset
    # inputs. It has no source licence/consent and is not used by numeric reruns.
    names = {name for name in names if release_candidate(name)}
    provenance = {}
    for name in sorted(names):
        if not (data / name).resolve().is_relative_to(data.resolve()): raise ValueError(f'Escaped input: {name}')
        if Path(name).suffix.lower() in AUDIO:
            source = audio_source(name, originals)
            if source not in approved: raise ValueError(f'No licence evidence: {source}, {name}')
            provenance[name] = source
    inventory = inventory_for(data, sorted(names))
    for path, expected in frozen['inputs'].items():
        if not release_candidate(path.removeprefix('data/')): continue
        if inventory['files'][path.removeprefix('data/')]['sha256'] != expected:
            raise ValueError(f'Frozen input changed: {path}')
    inventory['audio_sources'] = provenance
    write_archive(data, output, inventory)
    result = {'archive': output.name, 'sha256': sha(output), 'bytes': output.stat().st_size,
              'payload_files': len(inventory['files'])}
    if write_metadata:
        (data / 'release/inventory.json').write_bytes(canonical(inventory))
        (root / 'configs/dataset.yaml').write_bytes(canonical({
            'schema': 'dataset-release/v1', 'url': 'UPLOAD_URL_PENDING', **result,
            'inventory': 'data/release/inventory.json'}))
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-write-metadata', action='store_true')
    args = parser.parse_args()
    build(args.root, args.output or args.root / 'data/release/speech-eval-dataset-v1.zip', not args.no_write_metadata)
