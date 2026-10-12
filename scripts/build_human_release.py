"""Build the separate consented takes release; never touch the main dataset ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def canonical(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build(root: Path, output: Path) -> dict:
    """Package eight raw WAVs, transcripts, consent, notes and frozen timed labels."""
    if output.name == 'speech-eval-dataset-v1.zip':
        raise ValueError('Never replace the immutable main dataset archive')
    data = root / 'data'
    takes = [f'{text}__user__take{n:02}' for text in ('gettysburg', 'reagan_challenger')
             for n in range(1, 5)]
    names = ['human/CONSENT.md', 'human/raw/notes.md', 'human/evaluation.json']
    names += [f'human/{folder}/{rid}.{ext}' for rid in takes
              for folder, ext in (('raw', 'wav'), ('transcripts', 'txt'))]
    names += [p.relative_to(data).as_posix() for p in sorted((data / 'human/review').glob('*'))
              if p.is_file()]
    # Verify all inputs before producing derived metadata or opening a ZIP.
    for name in names:
        path = data / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing or unsafe human input: {name}')
    results = json.loads((data / 'human/evaluation.json').read_text())['results']
    selected = [r for r in results if r['mode'] == 'A' and r['detector'] == 'v1']
    if len(selected) != 8 or {r['take_id'] for r in selected} != set(takes):
        raise ValueError('Expected one frozen v1 A label record for each of eight takes')
    for row in selected:
        name = f"human/labels/{row['take_id']}.json"
        path = data / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # A copy of the pre-existing confirmed intervals, never new annotation.
        path.write_bytes(canonical({'schema': 'human-release-labels/v1',
            'take_id': row['take_id'], 'alignment_recording_id': row['recording_id'],
            'timeline': 'trimmed participant seconds', 'raw_offset_s': row['trim_start_s'],
            'excluded_from_scoring': row['excluded_from_scoring'],
            'unknown_flaws': row['excluded_from_scoring'],
            'independent_annotation': False, 'flaws': row['intended_regions'],
            'source': 'frozen data/human/evaluation.json; v1 A intended_regions'}))
        names.append(name)
    hashes = ''.join(f'{sha(data / name)}  {name}\n' for name in sorted(names))
    (data / 'human/hashes.sha256').write_text(hashes, encoding='utf-8', newline='\n')
    names.append('human/hashes.sha256')
    inventory = {'schema': 'dataset-inventory/v1', 'files': {
        name: {'sha256': sha(data / name), 'bytes': (data / name).stat().st_size}
        for name in sorted(names)}}
    (data / 'release/human_takes_inventory.json').write_bytes(canonical(inventory))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', allowZip64=True) as z:
        for name in sorted([*names, 'release_manifest.json']):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED if name.endswith('.wav') else zipfile.ZIP_DEFLATED
            with z.open(info, 'w', force_zip64=True) as target:
                if name == 'release_manifest.json': target.write(canonical(inventory))
                else:
                    with (data / name).open('rb') as source:
                        shutil.copyfileobj(source, target, 1024 * 1024)
            if name in names and sha(data / name) != inventory['files'][name]['sha256']:
                raise ValueError(f'Human input changed during build: {name}')
    result = {'archive': output.name, 'bytes': output.stat().st_size,
              'sha256': sha(output), 'payload_files': len(names),
              'inventory': 'data/release/human_takes_inventory.json'}
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(args.root, args.output or args.root / 'data/release/speech-eval-human-takes-v1.zip')
