"""Audit already-patched number rendering and regenerate affected mask/window metadata."""
import csv
import json
import re
from pathlib import Path
import yaml
from speecheval.evaluate import expand_numbers
from speecheval.transcripts import _body_text, normalize_tokens
from speecheval.verify import _hash_bytes, _refresh_output_windows, _write_json

root=Path.cwd();archive=root/'data/review/before_number_expansion'
config=yaml.safe_load((root/'configs/default.yaml').read_text())
records={};changed=[]
for path in sorted((archive/'transcripts').glob('*.txt')):
    rid=path.stem;old=path.read_text();expected,mapping=expand_numbers(old)
    current=root/'data/transcripts/as_spoken'/path.name
    assert current.read_text()==expected, f'Unexpected transcript changes: {rid}'
    old_mask=json.loads((archive/'uncertain'/f'{rid}.json').read_text())
    assert old_mask['transcript_sha256']==_hash_bytes(path.read_bytes())
    sha=_hash_bytes(current.read_bytes())
    old_mask['transcript_sha256']=sha
    old_mask['uncertain_words']=sorted({new for i in old_mask['uncertain_words'] for new in mapping[i]})
    _write_json(root/'data/transcripts/uncertain'/f'{rid}.json',old_mask)
    if expected!=old:
        changed.append(rid)
        assert normalize_tokens(_body_text(old))==normalize_tokens(_body_text(expected)),rid
    records[rid]={'input_sha256':_hash_bytes(path.read_bytes()),'output_sha256':sha,
        'changed':expected!=old,'old_to_new':mapping,
        'old_numbers':re.findall(r'\d+(?:,\d{3})*',_body_text(old)),
        'normalized_token_sequence_unchanged':normalize_tokens(_body_text(old))==normalize_tokens(_body_text(expected))}
_write_json(root/'data/review/number_expansion.json',{'schema':'number_expansion/v1','recordings':records,
    'changed_recordings':changed,'scope':'numeric rendering only; no new transcript truth claims',
    'prior_calibrated_audit':'frozen historical result against pre-number transcripts; not overwritten'})
_refresh_output_windows(root,config,{'transcripts':{rid:True for rid in changed}})
print('Updated masks and regenerated windows:',', '.join(changed))
