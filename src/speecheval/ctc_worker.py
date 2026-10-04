"""Isolated CPU CTC scorer; does not initialize ASR libraries."""
import json
import sys
from pathlib import Path
import yaml
from speecheval.calibrated import LocalScorer, score_pair
from speecheval.verify import _write_json

if __name__=='__main__':
    request=json.loads(Path(sys.argv[1]).read_text());root=Path(request['root'])
    settings=yaml.safe_load((root/'configs/default.yaml').read_text())['transcript_verification']
    scorer=LocalScorer(root,settings);results=[]
    for n,job in enumerate(request['jobs'],1):
        results.append(score_pair(root,scorer,job['recording_id'],job['window']))
        if n%25==0:print(f'Isolated CPU CTC {n}/{len(request["jobs"])}',flush=True)
    _write_json(Path(sys.argv[2]),results)
