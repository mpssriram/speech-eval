"""Score the custom-dictionary candidate against exactly the frozen gold words."""
import copy
import json
import yaml
from pathlib import Path
from speecheval.evaluate import error_metrics, mapped_boundary, load_recordings, validate_dataset
from speecheval.align.mfa import adoption_identity
from speecheval.alignment_analysis import custom_acceptable
from speecheval.verify import _write_json
root=Path.cwd();before=json.loads((root/'data/review/before_custom_dictionary/alignment_bakeoff.json').read_text())
config=yaml.safe_load((root/'configs/default.yaml').read_text())
ids=[p.stem for p in sorted((root/'data/alignment/mfa').glob('*__orig.json'))]
validate_dataset(root,config,load_recordings(root,ids))
starts=[];ends=[]
for d in before['details']:
    if d['aligner']!='mfa':continue
    payload=json.loads((root/'data/alignment/mfa'/f"{d['recording_id']}.json").read_text())
    start,end=mapped_boundary(payload['words'],d['current_indices'])
    starts.append(start-d['gold_start']);ends.append(end-d['gold_end'])
after={'start':error_metrics(starts),'end':error_metrics(ends),'overall':error_metrics(starts+ends)}
after['oov_words']=0
for rid in ids:
    payload=json.loads((root/'data/alignment/mfa'/f'{rid}.json').read_text())
    oov={w['text'] for w in payload['warnings'] if w['type']=='oov'}
    after['oov_words']+=sum(bool(set(w['norm'].split()) & oov) for w in payload['words'])
accepted=custom_acceptable(before['evidence']['mfa'],after)
_write_json(root/'data/review/custom_dictionary_comparison.json',{'before':before['evidence']['mfa'],
    'after':after,'accepted':accepted,'rule':'zero OOV; start/end/pooled mean and median do not worsen',
    'gold_words':len(starts),'gold_edges':len(starts)+len(ends),
    'artifact_hashes':adoption_identity(root,config['alignment']['mfa'])})
print(json.dumps({'after':after,'accepted':accepted},indent=2))
if not accepted:raise SystemExit('Custom dictionary rejected: do not adopt or promote')
