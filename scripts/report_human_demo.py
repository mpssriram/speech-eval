"""Add read-only genuine-take diagnostics without inference or label changes."""
import json
import argparse
import httpx
from pathlib import Path
from speecheval.human_demo_evidence import collect_evidence, breakdown_markdown, hit_rows, hits_markdown
from speecheval.human_confirmed_workflow import verify_inputs
from speecheval.verify import _write_json

root = Path.cwd()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--hits',action='store_true',help='Include live dashboard explanations of strict primary hits')
parser.add_argument('--base-url',default='http://localhost:8080')
args = parser.parse_args()
verify_inputs(root, json.loads((root/'data/human/review/confirmation.json').read_text()))
evidence = collect_evidence(root)
if args.hits:
    payload = json.loads((root/'data/human/evaluation.json').read_text())
    hits = []
    with httpx.Client(base_url=args.base_url,timeout=120) as client:
        for row in payload['results']:
            if row['mode'] not in ('A','B') or row['excluded_from_scoring']:
                continue
            response = client.get('/api/analyses/'+row['job_id'])
            response.raise_for_status()
            hits.extend(hit_rows(row,response.json()['analysis']['regions']))
    evidence['primary_hits'] = hits
_write_json(root/'data/human/demo_evidence.json', evidence)
path = root/'reports/phase10_human_takes.md'
marker = '\n## False-alarm breakdown (primary IoU >=0.3)'
base = path.read_text().split(marker)[0].rstrip()
path.write_text(base+'\n\n'+breakdown_markdown(evidence)+
                ('\n'+hits_markdown(evidence['primary_hits']) if args.hits else ''))
print(json.dumps({'pooled_false_alarms':evidence['pooled_false_alarms'],
                  'reference_readers':evidence['reference_readers'],
                  'take_timings':evidence['take_timings']}, indent=2))
