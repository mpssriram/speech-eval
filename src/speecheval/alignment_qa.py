"""Primary alignment quality assurance."""
import csv
import json
from pathlib import Path
import yaml
from speecheval.align.base import Alignment
from speecheval.evaluate import load_recordings, validate_dataset
from speecheval.verify import _write_json


def qa_row(payload: dict, flags: str) -> dict:
    """Counts, seconds and words/second; sentence-final long words are excluded."""
    words=payload['words'];final={s['word_end'] for s in payload['sentences']}
    oov={w['text'] for w in payload['warnings'] if w['type']=='oov'}
    interpolated={w['word'] for w in payload['warnings'] if w['type']=='interpolated'}
    return {'recording_id':payload['recording_id'],'duration_s':payload['duration_s'],'words':len(words),
        'speech_rate_wps':round(len(words)/payload['duration_s'],3),'interpolated':len(interpolated),
        'oov':sum(bool(set(w['norm'].split()) & oov) for w in words),
        'short_words':sum(w['end']-w['start']<.040-1e-8 for w in words),
        'long_words':sum(w['end']-w['start']>1.5+1e-8 and w['i'] not in final for w in words),
        'uncertain_words':len(payload.get('uncertain_words',[])),'qa_flags':flags}


def report_alignment(root: Path | None = None) -> None:
    """Validate promoted current alignments and generate Step 8 QA without human claims."""
    root=root or Path.cwd();config=yaml.safe_load((root/'configs/default.yaml').read_text())
    primary=config['alignment']['primary']
    if primary not in ('mfa','whisperx'):raise ValueError('Primary aligner not selected')
    manifest=list(csv.DictReader((root/'data/manifest/recordings.csv').open()))
    validate_dataset(root,config,load_recordings(root,[r['recording_id'] for r in manifest]))
    rows=[]
    for recording in manifest:
        rid=recording['recording_id'];path=root/'data/alignment'/f'{rid}.json'
        if path.read_bytes()!=(root/'data/alignment'/primary/path.name).read_bytes():raise ValueError('Stale promotion')
        payload=json.loads(path.read_text());Alignment.model_validate(payload)
        rows.append(qa_row(payload,recording.get('qa_flags','')))
    flagged=[r['recording_id'] for r in rows if any(r[k] for k in ('interpolated','short_words','long_words'))]
    _write_json(root/'data/review/alignment_qa.json',{'primary':primary,'rows':rows,'flagged':flagged,'human_spot_check':'PENDING'})
    lines=['# Day 1 alignment QA','',f'Primary: {primary}. Human Praat spot-check: **PENDING**. No listening review is claimed.',
        '', 'Speech rate uses all transcript words divided by full clip duration (descriptive QA only, not reference statistics). Uncertain words remain excluded from later reference/evaluation aggregates.',
        '', '| Recording | Duration s | Words | Speech rate wps | Interpolated | OOV | Short <40 ms | Long >1.5 s, non-final | Uncertain | QA flags |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in rows:lines.append('| '+' | '.join(str(r[k]) for k in ('recording_id','duration_s','words','speech_rate_wps','interpolated','oov','short_words','long_words','uncertain_words','qa_flags'))+' |')
    lines.extend(['','## Flagged recordings','',*['- '+rid for rid in flagged],'', 'Human review remains pending; flags are retained for that review, not auto-cleared.',''])
    (root/'reports/day01_alignment_qa.md').write_text('\n'.join(lines))
