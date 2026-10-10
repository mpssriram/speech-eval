"""Copy only ignored measured inputs into a separate clone, never source caches/models.

Usage: python scripts/restore_local_data.py /path/to/prepared/repo /path/to/fresh/clone
This is a local-data alternative until the user publishes the dataset archive.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import shutil


def restore(source: Path, target: Path) -> int:
    """Copy indexed HQ audio, feature bundles and JSON producer proof, without raw writes."""
    source=source.resolve();target=target.resolve()
    if source==target or not (target/'.git').is_dir():
        raise ValueError('Target must be a separate fresh Git clone')
    rows=list(csv.DictReader((source/'data/manifest/dataset_index.csv').open()))
    files=set()
    # Phase 8's freeze also binds excluded-source audio and 16 kHz synthetic files.
    frozen=json.loads((source/'data/review/final_evaluation.json').read_text())
    files.update(frozen['inputs'])
    for row in rows:
        rid=row['recording_id'];files.add(row['audio_path'])
        files.update(f'data/features/{folder}/{rid}.parquet' for folder in ('frames','words','windows','sentences'))
        files.add(f'data/features/speaker_stats/{rid}.json')
        text,speaker,_=rid.split('__',2)
        proof=f'data/.cache/dataset/{text}__{speaker}__orig/features.json'
        if (source/proof).is_file():files.add(proof)
    missing=[name for name in sorted(files) if not (source/name).is_file()]
    if missing:raise FileNotFoundError(f'Missing measured input: {missing[0]} ({len(missing)} missing)')
    for name in sorted(files):
        original=source/name;destination=target/name
        if not original.resolve().is_relative_to(source) or not destination.resolve().is_relative_to(target):
            raise ValueError(f'Input escapes clone: {name}')
        if destination.exists():
            # A fresh clone includes tracked speaker_stats JSON. Never overwrite it.
            if original.read_bytes()!=destination.read_bytes():raise ValueError(f'Existing clone input differs: {name}')
            continue
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,destination)
    return len(files)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('target',type=Path)
    args=parser.parse_args();print(f'Restored {restore(args.source,args.target)} measured input files')
