"""Validate all real Step 7a templates and a byte-identical cached rerun."""
import hashlib
import json
from pathlib import Path
from praatio import textgrid
from speecheval.gold import prepare_gold

root=Path.cwd();todo=root/'data/gold/alignment/todo'
selection=json.loads((todo/'selection.json').read_text())
assert selection['status']=='unreviewed_template_not_gold'
assert len(selection['recordings'])==3
for filename,sha in selection['input_hashes'].items():
    assert hashlib.sha256((root/filename).read_bytes()).hexdigest()==sha
for rid,plan in selection['recordings'].items():
    assert len(plan['items'])==20
    path=todo/f'{rid}.TextGrid'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==selection['template_hashes'][path.name]
    tg=textgrid.openTextgrid(str(path),includeEmptyIntervals=False)
    assert tg.tierNames==('gold',)
    entries=tg.getTier('gold').entries
    assert len(entries)==20
    for item,entry in zip(plan['items'],entries):
        assert (entry.start,entry.end,entry.label)==(item['start'],item['end'],item['text'])
        assert 0<=entry.start<entry.end<=plan['duration_s']
        assert item['mfa_end']-item['mfa_start']>=.15-1e-9
        assert item['whisperx_end']-item['whisperx_start']>=.15-1e-9
        assert item['start']==round(max(0.,(item['mfa_start']+item['whisperx_start'])/2-.15),3)
        assert item['end']==round(min(plan['duration_s'],(item['mfa_end']+item['whisperx_end'])/2+.15),3)
        for name in ('mfa','whisperx'):
            payload=json.loads((root/'data/alignment'/name/f'{rid}.json').read_text())
            assert item['word_index'] not in payload['uncertain_words']
            assert not any(w['type']=='interpolated' and w['word']==item['word_index'] for w in payload['warnings'])
before={p.name:p.read_bytes() for p in todo.iterdir() if p.is_file()}
prepare_gold(root)
assert before=={p.name:p.read_bytes() for p in todo.iterdir() if p.is_file()}
assert not list(todo.parent.glob('*.TextGrid'))
print('PASS: 3 templates / 60 intervals, symmetric padded averages, no uncertain/interpolated words, exact rerun; no human gold')
