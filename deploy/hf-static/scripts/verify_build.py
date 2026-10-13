"""Check every shipped JSON byte against its pinned stored-output hash."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
DEMO=Path(__file__).resolve().parents[1]
ROOT=DEMO.parents[1]

def verify(build: Path, require_sources: bool=False) -> int:
    """Fail on changed, absent or extra JSON files; return the verified count."""
    manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (DEMO/'MANIFEST.sha256').read_text().splitlines()}
    source_map=json.loads((DEMO/'SOURCE_MAP.js').read_text().removeprefix('export default ').strip().removesuffix(';'))
    actual={str(p.relative_to(build)) for p in build.rglob('*.json')}
    if actual != set(manifest):raise ValueError(f'JSON inventory differs: extra={actual-set(manifest)}, missing={set(manifest)-actual}')
    for rel,expected in manifest.items():
        blob=(build/rel).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=expected:raise ValueError(f'Changed shipped bytes: {rel}')
        src=ROOT/source_map[rel]['source']
        if src.exists():
            if src.read_bytes()!=blob:raise ValueError(f'Stored-output byte mismatch: {rel}')
        elif require_sources:raise FileNotFoundError(src)
    print(f'PASS: {len(actual)}/{len(actual)} JSON files exactly match MANIFEST.sha256'+(' and every stored source' if require_sources else ''))
    return len(actual)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=DEMO/'dist')
    parser.add_argument('--require-sources',action='store_true')
    args=parser.parse_args();verify(args.build,args.require_sources)
