"""Consented human-take workflow; synthetic smoke inputs never become human results."""
from __future__ import annotations
import hashlib
import json
import logging
import math
from pathlib import Path
import re
import subprocess
import time

import httpx
import soundfile as sf

LOGGER=logging.getLogger(__name__)
TEXTS=('gettysburg','reagan_challenger')
TYPES={'rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause'}


def digest(path: Path) -> str:
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def discover_takes(root: Path) -> list[dict]:
    """Find only the eight requested raw filenames; do not invent missing takes."""
    cases=[];folder=root/'data/human/raw'
    for text in TEXTS:
        for n in range(1,5):
            rid=f'{text}__user__take{n:02d}';audio=folder/f'{rid}.wav'
            if audio.is_file():
                if audio.is_symlink() or not audio.resolve().is_relative_to(folder.resolve()):
                    raise ValueError('Raw human recording symlink escapes input folder')
                cases.append({'take_id':rid,'text_id':text,'audio':audio,
                              'transcript':root/'data/human/transcripts'/f'{rid}.txt','take_number':n})
    return cases


def missing_rehearsal_baselines(cases: list[dict]) -> list[str]:
    """List missing own take01 baselines instead of silently omitting Mode B."""
    available={(c['text_id'],c['take_number']) for c in cases}
    return [f'{c["take_id"]}: Mode B blocked; own take01 of {c["text_id"]} is missing.'
            for c in cases if c['take_number'] in (2,3) and (c['text_id'],1) not in available]


def validate_human_inputs(root: Path) -> tuple[list[dict],dict]:
    """Require consent, explicit notes and as-spoken text, never infer them from flags."""
    cases=discover_takes(root)
    if not cases: return [],{'takes':{}}
    consent=root/'data/human/CONSENT.md'
    if not consent.is_file() or not consent.read_text().strip():
        raise ValueError('Missing nonempty data/human/CONSENT.md; no genuine takes processed')
    notes_path=root/'data/human/raw/notes.md'
    if not notes_path.is_file(): raise ValueError('Missing data/human/raw/notes.md')
    match=re.search(r'```json\s*(.*?)\s*```',notes_path.read_text(),re.S)
    if not match: raise ValueError('notes.md needs an explicit JSON annotation block; see docs/HUMAN_TAKES.md')
    try: notes=json.loads(match.group(1))
    except json.JSONDecodeError as exc: raise ValueError('Invalid notes JSON') from exc
    if not isinstance(notes,dict) or not isinstance(notes.get('takes'),dict):
        raise ValueError('Notes JSON must be a dictionary with a dictionary-valued takes field')
    for case in cases:
        detail=notes.get('takes',{}).get(case['take_id'])
        excluded=isinstance(detail,dict) and detail.get('excluded_from_scoring') is True
        if not isinstance(detail,dict) or 'slips' not in detail or (not excluded and not isinstance(detail.get('flaws'),list)):
            raise ValueError(f'Explicit intended flaws and slips missing for {case["take_id"]}')
        if excluded and (detail.get('flaws') is not None or not detail.get('exclusion_reason')):
            raise ValueError('Excluded takes require unknown flaws (null) and an explicit exclusion reason')
        if not case['transcript'].is_file() or not expanded_transcript(case['transcript'].read_text()).strip():
            raise ValueError(f'Missing as-spoken transcript: {case["transcript"]}')
        info=sf.info(case['audio']);duration=info.duration
        if not 0<duration<=600 or case['audio'].stat().st_size>25*1024*1024:
            raise ValueError('Human WAV exceeds duration/size limits (600 seconds, 25 MiB)')
        if info.format!='WAV' or info.subtype!='PCM_16' or info.channels!=1:
            raise ValueError('Human raw input must be mono PCM16 WAV')
        for note in detail['flaws'] or []:
            if not isinstance(note,dict) or note.get('type') not in TYPES:
                raise ValueError('Invalid intended flaw note type')
            if 'sentence' in note:
                if not isinstance(note['sentence'],int) or note['sentence']<1:
                    raise ValueError('Invalid intended flaw sentence')
            elif not all(isinstance(note.get(k),(int,float)) and math.isfinite(note[k]) for k in ('start','end')) or not 0<=note['start']<note['end']<=duration:
                raise ValueError('Invalid intended flaw raw-time interval')
    return cases,notes


def expanded_transcript(text: str) -> str:
    """Expand written numbers while retaining punctuation and sentence boundaries."""
    from speecheval.evaluate import expand_numbers
    from speecheval.transcripts import _body_text
    return expand_numbers(_body_text(text))[0].strip()


def normalize_upload(raw: Path, output: Path) -> dict:
    """Format-normalise to mono PCM16/44100 Hz; no loudness/gain normalisation."""
    info=sf.info(raw);before=digest(raw)
    if output.resolve()==raw.resolve(): raise ValueError('Raw recording is immutable; output must differ')
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(raw),
                    '-vn','-ac','1','-ar','44100','-c:a','pcm_s16le',str(output)],check=True)
    prepared=sf.info(output)
    if digest(raw)!=before: raise ValueError('Immutable raw recording changed')
    if prepared.samplerate!=44100 or prepared.channels!=1 or prepared.subtype!='PCM_16':
        raise ValueError('Unexpected normalized upload format')
    return {'raw_sha256':before,'upload_sha256':digest(output),'original_sample_rate':info.samplerate,
            'original_channels':info.channels,'raw_duration_s':round(info.duration,3),
            'upload_sample_rate':44100,'gain_normalization':False}


def intended_regions(detail: dict, alignment: dict, trim_start_s: float) -> tuple[list[dict],list[str]]:
    """Map declared raw-second or sentence intent into trimmed participant seconds."""
    regions=[];basis=[]
    for note in detail['flaws']:
        if note.get('type') not in TYPES: raise ValueError('Unknown intended flaw type')
        if 'sentence' in note:
            sentence=next((s for s in alignment['sentences'] if s['i']==int(note['sentence'])-1),None)
            if sentence is None: raise ValueError('Intended sentence is absent from the as-spoken alignment')
            start,end=sentence['start'],sentence['end']
            basis.append('intended sentence interval, not independent timed ground truth')
        else:
            start=float(note['start'])-trim_start_s;end=float(note['end'])-trim_start_s
            basis.append('raw-time note')
        if not math.isfinite(start) or not math.isfinite(end) or not 0<=start<end<=alignment['duration_s']:
            raise ValueError('Intended note interval is outside trimmed audio; do not silently clip labels')
        regions.append({'type':note['type'],'start':round(start,3),'end':round(end,3)})
    return regions,basis


def compare_regions(predicted: list[dict], truth: list[dict]) -> dict:
    """One-to-one hits/misses/FP: strict IoU .3 plus disclosed synthetic pause rule."""
    from speecheval.evaluate import match_regions
    # Re-tag types only inside this call to apply the same greedy IoU matcher to
    # pause intervals too, without changing the frozen evaluator's pause policy.
    intervals=lambda rows:[{**r,'type':'interval:'+r['type']} for r in rows]
    strict=match_regions(intervals(predicted),intervals(truth),.3,.25)
    historical=match_regions(predicted,truth,.3,.25)
    def counts(pairs): return {'hits':len(pairs),'misses':len(truth)-len(pairs),
                               'false_positives':len(predicted)-len(pairs)}
    return {'strict_iou':counts(strict),'synthetic_policy':counts(historical)}


def submit(client: httpx.Client, audio: Path, text: str, transcript: str,
           mode: str='A', previous: str='', timeout_s: float=900) -> dict:
    """Submit a real MFA job and wait for its completed dashboard analysis."""
    with audio.open('rb') as stream:
        response=client.post('/api/analyses',files={'audio':(audio.name,stream,'audio/wav')},
            data={'text_id':text,'mode':mode,'transcript':transcript,'previous_analysis_id':previous})
    response.raise_for_status();job=response.json();deadline=time.monotonic()+timeout_s
    # POST returns only an ID/status even for cached completed jobs.
    response=client.get('/api/analyses/'+job['analysis_id']);response.raise_for_status();job=response.json()
    while job['status'] in ('queued','running'):
        if time.monotonic()>deadline: raise TimeoutError(f'Analysis did not complete: {job["analysis_id"]}')
        time.sleep(1)
        response=client.get('/api/analyses/'+job['analysis_id']);response.raise_for_status();job=response.json()
    if job['status']!='done': raise ValueError('Real analysis failed: '+job.get('error','unknown'))
    LOGGER.info('Completed %s %s: %s',text,mode,job['analysis_id'])
    return job


def trim_state(root: Path, rid: str) -> dict:
    """Locate the real producer's recorded trim bounds, never assume zero offset."""
    prefix=rid.split('__input_',1)[-1]
    states=list((root/'data/.cache/participants').glob(prefix+'*/state.json'))
    if len(states)!=1: raise ValueError('Missing/ambiguous participant trimming provenance')
    return json.loads(states[0].read_text())


def dashboard_link(base_url: str, job_id: str, dashboard_url: str | None=None) -> str:
    """Separate browser-visible host address from container-only API DNS."""
    return (dashboard_url or base_url).rstrip('/')+'/results/'+job_id


def execute_cases(root: Path, cases: list[dict], notes: dict, base_url: str, fixture: bool=False,
                  dashboard_url: str | None=None) -> list[dict]:
    """A for each available take, B02/B03 against completed A01 of the same text."""
    results=[];baseline={};configs={n:digest(root/'configs'/n) for n in ('default.yaml','detector.yaml','rubric.yaml')}
    with httpx.Client(base_url=base_url,timeout=120) as client:
        for case in cases:
            work=root/'data/.cache/human-work'/case['take_id'];upload=work/'upload.wav'
            qa=normalize_upload(case['audio'],upload)
            transcript=expanded_transcript(case['transcript'].read_text())
            for mode in ('A','B') if case['take_number'] in (2,3) and case['text_id'] in baseline else ('A',):
                job=submit(client,upload,case['text_id'],transcript,mode,baseline.get(case['text_id'],'') if mode=='B' else '')
                analysis=job['analysis'];alignment=json.loads((root/'data/alignment'/f'{analysis["recording_id"]}.json').read_text())
                state=trim_state(root,analysis['recording_id']);trim=state['trim_start_s']
                truth,basis=intended_regions(notes['takes'][case['take_id']],alignment,trim)
                if mode=='A' and case['take_number']==1: baseline[case['text_id']]=job['analysis_id']
                results.append({'take_id':case['take_id'],'source':'synthetic workflow fixture' if fixture else 'user recording',
                    'mode':mode,'job_id':job['analysis_id'],'recording_id':analysis['recording_id'],
                    'dashboard_url':dashboard_link(base_url,job['analysis_id'],dashboard_url),
                    'notes_basis':basis,'slips':notes['takes'][case['take_id']]['slips'],
                    'intended_regions':truth,'comparison':compare_regions(analysis['regions'],truth),
                    'qa':qa,'trim_start_s':trim,'trim_end_s':state['trim_end_s'],
                    'aligner':alignment['aligner'],'scores':analysis['scores'],
                    'expert_readers':analysis['reference']['n_readers'],'warnings':analysis['warnings']})
                if not fixture:
                    prepared=root/'data/human/prepared'/f'{case["take_id"]}.flac';prepared.parent.mkdir(parents=True,exist_ok=True)
                    wave,sr=sf.read(root/alignment['audio']);sf.write(prepared,wave,sr,subtype='PCM_16')
            if digest(case['audio'])!=qa['raw_sha256']: raise ValueError('Raw take changed during analysis')
    if configs!={n:digest(root/'configs'/n) for n in configs}: raise ValueError('Frozen configuration changed; no tuning allowed')
    return results


def synthetic_cases(root: Path) -> tuple[list[dict],dict]:
    """Two licensed matching-word crops, outside human/raw, exercising real A/B MFA."""
    source='gettysburg__lv_fb__orig';flawed='gettysburg__lv_fb__rushing_s3_01'
    inventory=json.loads((root/'data/release/inventory.json').read_text())
    label=json.loads((root/'data/labels'/f'{flawed}.json').read_text())['flaws'][0]
    first=max(0,label['word_start']-3);last=label['word_end']+3
    cases=[];notes={'takes':{}}
    for n,rid in enumerate((source,flawed),1):
        alignment=json.loads((root/'data/alignment'/f'{rid}.json').read_text());words=alignment['words']
        end_index=min(last,len(words)-1);start=words[first]['start'];end=words[end_index]['end']
        original=root/alignment['audio'];relative=str(original.relative_to(root/'data'))
        if relative not in inventory['audio_sources'] or digest(original)!=inventory['files'][relative]['sha256']:
            raise ValueError('Fixture audio is not a verified licensed release member')
        work=root/'data/.cache/human-fixture';work.mkdir(parents=True,exist_ok=True)
        name=f'workflow_fixture_{n}';audio=work/f'{name}.wav';transcript=work/f'{name}.txt'
        wave,sr=sf.read(original);sf.write(audio,wave[round(start*sr):round(end*sr)],sr,subtype='PCM_16')
        transcript.write_text(' '.join(w['text'] for w in words[first:end_index+1])+'\n')
        cases.append({'take_id':name,'text_id':'gettysburg','audio':audio,'transcript':transcript,'take_number':n})
        notes['takes'][name]={'flaws':[] if n==1 else [{'type':label['type'],'start':label['start']-start,'end':label['end']-start}],
                             'slips':'synthetic fixture; not a user take'}
    return cases,notes


def write_report(root: Path, results: list[dict], fixture: bool, blockers: list[str]) -> None:
    """Write only the authorised Phase10 report, keeping fixture and human evidence separate."""
    lines=['# Phase 10 human takes','',
           '**Genuine human takes: pending**' if fixture or blockers or not results else 'Consented user recordings processed.',
           '', 'No detector thresholds, bins, rubric weights or frozen scientific implementation were tuned.',
           'Format normalisation is mono PCM16/44.1 kHz conversion, not loudness normalisation. Raw audio remains unchanged.',
           'Alignment uses real CPU MFA on supplied as-spoken text with number expansion. Trim offsets come from producer provenance.',
           '', 'Primary interval matching: same type, one-to-one greedy IoU >= 0.3 for every type. Historical synthetic matching uses IoU >= 0.3 for regions but centre distance <= 0.25 s for pause events; its counts are shown separately.',
           'Sentence-only notes are intended intervals, not independent time-labelled perceptual ground truth. Slips must be reflected in the supplied transcript; no automatic listening/review is claimed.', '']
    if blockers: lines.extend(['## Pending inputs','',*['- '+b for b in blockers],''])
    if results:
        lines.extend(['## Synthetic workflow verification — not human results' if fixture else '## User takes', '',
            '| Take | Mode | IoU hits / misses / FP | Synthetic-policy hits / misses / FP | Dashboard |',
            '|---|---|---|---|---|'])
        for result in results:
            values=lambda k:' / '.join(str(result['comparison'][k][n]) for n in ('hits','misses','false_positives'))
            lines.append(f'| {result["take_id"]} | {result["mode"]} | {values("strict_iou")} | {values("synthetic_policy")} | [Open]({result["dashboard_url"]}) |')
        lines.extend(['','QA, hashes, exact declared label basis, trim bounds, aligner and score evidence: '+
                      ('`data/human/fixture_verification.json` (explicitly synthetic).' if fixture else '`data/human/evaluation.json`.'),
                      'Jobs are real completed API jobs, visible via their dashboard links and the existing previous-take history. Fixture jobs must not be presented as the user\'s recordings.'])
    lines.extend(['','Actual notes/consent/recordings and independent raters remain user actions. No human accuracy, rehearsal improvement or agreement claim is available until genuine input exists.',''])
    (root/'reports/phase10_human_takes.md').write_text('\n'.join(lines))


def run(root: Path, base_url: str='http://localhost:8080', fixture: bool=False,
        dashboard_url: str | None=None) -> dict:
    """Run genuine available takes, or an explicitly requested isolated fixture smoke."""
    from speecheval.verify import _write_json
    blockers=[]
    try: cases,notes=validate_human_inputs(root)
    except ValueError as exc: cases=[];notes={'takes':{}};blockers.append(str(exc))
    if not cases and not blockers: blockers.append('No requested WAVs, notes.md or consent have been supplied in data/human/.')
    if cases: blockers.extend(missing_rehearsal_baselines(cases))
    if fixture: cases,notes=synthetic_cases(root)
    results=execute_cases(root,cases,notes,base_url,fixture,dashboard_url) if cases else []
    payload={'schema':'human-takes-workflow/v1','source':'synthetic fixture' if fixture else 'consented user takes',
             'genuine_takes_processed':0 if fixture else len({r['take_id'] for r in results}),
             'threshold_tuning':False,'results':results,'blockers':blockers}
    if results:
        _write_json(root/('data/.cache/human-fixture/results.json' if fixture else 'data/human/evaluation.json'),payload)
        if fixture: _write_json(root/'data/human/fixture_verification.json',payload)
    write_report(root,results,fixture,blockers)
    if blockers:
        path=root/'docs/BLOCKERS.md';marker='## Item B — genuine take analysis inputs'
        if marker not in path.read_text(): path.write_text(path.read_text()+'\n'+marker+'\n\n'+ '\n'.join('- '+b for b in blockers)+'\n')
    return payload
