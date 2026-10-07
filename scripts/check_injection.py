"""Verify rendered synthetic bundles and optionally fresh deterministic replay."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from speecheval.align.base import Alignment
from speecheval.inject import Label, inject_preview, map_time


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fresh',action='store_true');args=parser.parse_args()
    root=Path.cwd();audit=json.loads(Path('data/flawed/effect_checks.json').read_text())
    assert audit['passed'] and len(audit['checks'])==105
    assert len(json.loads(Path('data/flawed/preview/manifest.json').read_text())['items'])==35
    hashes={}
    for item in audit['checks']:
        rid=item['recording_id'];label=json.loads((root/'data/labels'/f'{rid}.json').read_text());Label.model_validate(label)
        oracle=json.loads((root/'data/alignment/oracle'/f'{rid}.json').read_text());Alignment.model_validate(oracle)
        source=json.loads((root/'data/alignment'/f"{label['reference_id']}.json").read_text())
        mapping=json.loads((root/'data/flawed/timemaps'/f'{rid}.json').read_text())['breakpoints']
        assert np.all(np.diff(np.asarray(mapping),axis=0)>=-1e-9)
        slopes=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(mapping,mapping[1:]) if b[0]>a[0]]
        # Source/map/target times are each rounded to 1 ms. Stretch amplifies
        # source-coordinate rounding; the combined bound is not a fixed 1 ms.
        tolerance=.001+.0005*max(slopes)+1e-8
        assert oracle.get('uncertain_words',[])==source.get('uncertain_words',[])
        for before,after in zip(source['words'],oracle['words']):
            assert abs(map_time(before['start'],mapping)-after['start'])<=tolerance
            assert abs(map_time(before['end'],mapping,side='left')-after['end'])<=tolerance
        for folder,sr in [('hq',44100),('align16k',16000)]:
            path=root/'data/flawed'/folder/f'{rid}.flac';y,rate=sf.read(path)
            assert rate==sr and y.ndim==1 and abs(len(y)/sr-oracle['duration_s'])<=.0011
            assert np.max(np.abs(y))<1
        record=json.loads((root/'data/flawed/provenance'/f'{rid}.json').read_text())
        for path,expected in record['artifacts'].items():
            actual=hashlib.sha256((root/path).read_bytes()).hexdigest();assert actual==expected;hashes[path]=actual
    inject_preview(force=args.fresh)
    assert hashes=={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in hashes}
    print(f'PASS: 105 effects, 525 artifact hashes, 35 preview rows, oracle/time-map consistency, {"fresh" if args.fresh else "cached"} replay')


if __name__=='__main__':main()
