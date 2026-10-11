"""Recorder-confirmed evaluation adapter; no scientific detector implementation changes."""
from __future__ import annotations
import hashlib
import json
import logging
from pathlib import Path
import httpx
import soundfile as sf
from speecheval.human_takes import (digest,validate_human_inputs,normalize_upload,
    expanded_transcript,submit,trim_state,dashboard_link,missing_rehearsal_baselines)
from speecheval.human_grounding import grounded_regions,compare_grounded
from speecheval.verify import _write_json

LOGGER=logging.getLogger(__name__)
MATCHERS=('primary','historical_pause_policy','secondary')
V2_LABEL='post-hoc v2; test split was seen with v1, so results are optimistic'


def modes_for(case: dict, detail: dict) -> tuple[str,...]:
    """A every take; B02/B03; C additionally for explicitly unscored take04."""
    if detail.get('excluded_from_scoring'):return ('A','C')
    return ('A','B') if case['take_number'] in (2,3) else ('A',)


def publish_v2(root: Path, result: dict, source: dict) -> dict:
    """Publish an already-computed frozen v2 result to existing completed-job UI."""
    from speecheval.service import save_json
    identity={'detector':'post-hoc-v2','source_job':source['analysis_id'],
              'analysis_sha256':hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()}
    aid=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:24]
    job={'analysis_id':aid,'status':'done','analysis':result,'identity':identity,
         'created_order':source['created_order']+1}
    path=root/'data/app/jobs'/f'{aid}.json'
    if path.exists():
        if json.loads(path.read_text())!=job:raise ValueError('Existing v2 completed job differs')
    else:save_json(path,job)
    return job


def make_row(root: Path, case: dict, detail: dict, job: dict, alignment: dict,
             units: list[dict], state: dict, qa: dict, detector: str, dashboard: str) -> dict:
    """Score only declared ground truth; unknown readings never become clean negatives."""
    result=job['analysis'];excluded=detail.get('excluded_from_scoring',False)
    truth,unit_truth,basis=grounded_regions(case['take_id'],detail,alignment,units)
    return {'take_id':case['take_id'],'source':'recorder-confirmed genuine user recording',
        'detector':detector,'detector_label':'frozen v1; primary' if detector=='v1' else V2_LABEL,
        'mode':result['mode'],'job_id':job['analysis_id'],'recording_id':result['recording_id'],
        'dashboard_url':dashboard_link(dashboard,job['analysis_id']),
        'excluded_from_scoring':excluded,'exclusion_reason':detail.get('exclusion_reason'),
        'labelled_flaws':None if excluded else len(truth),'slips':detail['slips'],
        'intended_regions':None if excluded else truth,'secondary_unit_regions':None if excluded else unit_truth,
        'notes_basis':basis,'comparison':None if excluded else compare_grounded(result['regions'],truth,unit_truth),
        'regions':result['regions'],'flag_count':len(result['regions']),
        'duration_s':result['duration_s'],'qa':qa,'trim_start_s':state['trim_start_s'],
        'trim_end_s':state['trim_end_s'],'aligner':alignment['aligner'],
        'scores':result['scores'],'expert_readers':result['reference'].get('n_readers'),
        'warnings':result['warnings'],'detector_identity':result['detector']}


def pooled(rows: list[dict]) -> list[dict]:
    """Pool current-recording seconds only; exclude unknown takes from every denominator."""
    result=[]
    for detector,mode in sorted({(r['detector'],r['mode']) for r in rows if not r['excluded_from_scoring']}):
        selected=[r for r in rows if r['detector']==detector and r['mode']==mode and not r['excluded_from_scoring']]
        minutes=sum(r['duration_s'] for r in selected)/60
        for matcher in MATCHERS:
            counts={k:sum(r['comparison'][matcher][k] for r in selected) for k in ('hits','misses','false_positives')}
            result.append({'detector':detector,'mode':mode,'matcher':matcher,
                'current_takes':len(selected),'labelled_flaws':sum(r['labelled_flaws'] for r in selected),
                'duration_min':minutes,**counts,'false_positives_per_min':counts['false_positives']/minutes})
    return result


def verify_inputs(root: Path, confirmation: dict) -> None:
    """Enforce pre-result transcript/notes/protocol, immutable audio and detector hashes."""
    from speecheval.evaluate_v2 import verify_hashes
    paths={'data/human/raw/notes.md':confirmation['notes_sha256'],
           'data/human/CONSENT.md':confirmation['consent_sha256'],
           'data/human/review/transcript_units.json':confirmation['transcript_units_sha256'],
           'data/human/review/CONFIRMED_PROTOCOL.md':confirmation['label_protocol_sha256'],
           'data/review/detector_v2_test_started.json':confirmation['one_shot_marker_sha256']}
    paths.update({f'data/human/transcripts/{rid}.txt':sha for rid,sha in confirmation['transcript_hashes'].items()})
    units=json.loads((root/'data/human/review/transcript_units.json').read_text())['takes']
    for rid,item in units.items():
        text_id=rid.split('__',1)[0]
        paths[f'data/transcripts/canonical/{text_id}.txt']=item['canonical_sha256']
        paths[f'data/human/asr_drafts/{rid}.txt']=item['asr_sha256']
    manifest=json.loads((root/'data/human/import_manifest.json').read_text())
    for take in manifest['takes']:
        for key in ('original','wav'):
            item=take[key];paths[item['relative_path']]=item['sha256']
    verify_hashes(root,{**confirmation['frozen_code_and_config_hashes'],**paths})


def report_text(payload: dict) -> str:
    """Produce full honest per-take evidence without independent annotation/rating claims."""
    lines=['# Phase 10 — genuine recorder-confirmed takes','',
        f'{payload["status"].upper()}: {payload["genuine_takes_processed"]} distinct take(s) have completed analysis with real CPU MFA. Frozen v1 is primary; v2 is secondary.',
        V2_LABEL+'.','',
        'Labels come from the recorder\'s 2026-10-12 confirmation of the planned script, not independent annotation or listening. The confirmation replaces manual TAKES_REVIEW markers. Severity was not supplied and is not invented.',
        'Transcripts use canonical words with ASR whole-word insertions, omissions and repetitions; same-position substitutions keep canonical words, contractions follow ASR, and mumbling units retain canonical words. Numbers are expanded. These rule-authorised transcripts are not independently verified verbatim. Canonical units remain Gettysburg 1–10 and Reagan 1–17, stopping at “discover its truths.” Structural edits: `data/human/review/TRANSCRIPT_DIFFS.md`.',
        'The predeclared six scored takes contain 13 declared flaws. Both spontaneous take04s have unknown flaws and are excluded from all hit/miss/FP calculations, not labelled clean. Requested scope is A for eight takes, B02/03 versus own01, and C for both take04s. Completed jobs are listed below; any processing failure makes the workflow INCOMPLETE. B never counts reference durations.',
        'Localized spans are fixed from MFA word times: larger|sense, were|daring; units 8/9 and 14/15; last four words for trail-off; have thus far for dragging; whole unit otherwise. Gaps below 30 ms use a centred 30 ms event, declared before inference to match the frozen detector event representation. No detection results are used to place labels.',
        'Primary: same type, one-to-one greedy IoU ≥ 0.3 for all types. Historical pause policy additionally uses pause-centre distance ≤ 0.25 s. Secondary: same type, any positive overlap with the labelled canonical unit, one-to-one. Raw/trim offsets and exact spans are in `data/human/evaluation.json`.',
        'Native 48 kHz mono PCM16 raw WAVs and original ALAC files remain byte-unchanged. Upload conversion is 44.1 kHz mono PCM16, without gain, loudness normalization or filtering; prepared audio is lossless FLAC. Import QA: `data/human/import_manifest.json`. No detector thresholds, bins, weights or rules were tuned on these takes.',
        'Independent human agreement is pending: the rating pack and scripts are ready, zero responses. No AI or self-ratings are rater data. Reagan has one expert reader, not a multi-reader empirical distribution.','']
    for detector in ('v1','v2'):
        subset=[r for r in payload['results'] if r['detector']==detector]
        if not subset:continue
        lines.extend(['## '+('Frozen v1 — primary' if detector=='v1' else V2_LABEL),'',
            '| Take | Mode | Labels | Flags | Primary H/M/FP | Historical H/M/FP | Secondary H/M/FP | Dashboard |',
            '|---|---|---:|---:|---|---|---|---|'])
        for r in subset:
            values=lambda k:'excluded' if r['comparison'] is None else '/'.join(str(r['comparison'][k][n]) for n in ('hits','misses','false_positives'))
            labels='unknown; excluded' if r['labelled_flaws'] is None else str(r['labelled_flaws'])
            lines.append(f'| {r["take_id"]} | {r["mode"]} | {labels} | {r["flag_count"]} | {values("primary")} | {values("historical_pause_policy")} | {values("secondary")} | [Open]({r["dashboard_url"]}) |')
        lines.append('')
    lines.extend(['## Pooled scored takes','',
        'The complete protocol has six distinct scored takes (01–03 of both texts) in A and four current takes in B, using two of those six as references. Actual completed denominators are shown below. If INCOMPLETE, these are partial pools, not full-cohort claims. A and B are separate evaluations, not ten independent recordings.',
        '', '| Detector | Mode | Matcher | Current takes | Labels | Hits | Misses | FP | Minutes | FP/min |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|'])
    for p in payload['pooled']:
        lines.append(f'| {p["detector"]} | {p["mode"]} | {p["matcher"]} | {p["current_takes"]} | {p["labelled_flaws"]} | {p["hits"]} | {p["misses"]} | {p["false_positives"]} | {p["duration_min"]:.2f} | {p["false_positives_per_min"]:.3f} |')
    lines.extend(['','Take01 flags are reported explicitly in the Flags column and count as false positives because those takes are declared natural readings with no delivery-flaw labels. Slips and mispronunciations are not automatically delivery flaws.',
        '', '## Provenance and reproducibility','',
        f'Input/protocol freeze commit: `{payload["input_freeze_commit"]}`. Confirmation SHA256: `{payload["confirmation_sha256"]}`.',
        'Frozen code/config hashes, one-shot benchmark marker and all 16 original/raw hashes verified before and after inference. The existing v2 benchmark one-shot was not rerun. Genuine human inference is separate from the synthetic test benchmark. Human audio remains git-ignored and excluded from the public archive.',
        'The real API jobs persist under data/app/jobs; v2 results are published as separately identified completed jobs without changing their scientific JSON. The dashboard displays the user\'s prepared waveform/audio, not reference audio; the same-words baseline is a separate playback.', ''])
    if payload['blockers']:lines.extend(['## Processing problems','',*['- '+s for s in payload['blockers']],''])
    return '\n'.join(lines)


def run_confirmed(root: Path, base_url: str, dashboard_url: str | None,
                  detector: str='both') -> dict:
    """Validate fixed inputs, run real v1 MFA A/B/C, then frozen post-hoc v2 A/B."""
    from speecheval.detector_v2 import analyze_v2
    if detector not in ('v1','v2','both'):raise ValueError('Detector must be v1, v2 or both')
    root=root.resolve();cases,notes=validate_human_inputs(root)
    confirmation_path=root/'data/human/review/confirmation.json'
    confirmation=json.loads(confirmation_path.read_text());verify_inputs(root,confirmation)
    if len(cases)!=8:raise ValueError('Confirmed eight-take protocol requires all eight WAVs')
    missing=missing_rehearsal_baselines(cases)
    if missing:raise ValueError('; '.join(missing))
    unit_map=json.loads((root/'data/human/review/transcript_units.json').read_text())['takes']
    baseline={};rows=[];blockers=[];dashboard=dashboard_url or base_url
    progress_path=root/'data/human/workflow_progress.json'
    with httpx.Client(base_url=base_url,timeout=120) as client:
        for case in cases:
            detail=notes['takes'][case['take_id']];units=unit_map[case['take_id']]['units']
            upload=root/'data/.cache/human-work'/case['take_id']/'upload.wav'
            qa=normalize_upload(case['audio'],upload)
            transcript=expanded_transcript(case['transcript'].read_text())
            for mode in modes_for(case,detail):
                try:
                    if mode=='B' and case['text_id'] not in baseline:
                        raise ValueError('Mode B blocked: own take01 did not complete successfully')
                    job=submit(client,upload,case['text_id'],transcript,mode,
                               baseline[case['text_id']]['analysis_id'] if mode=='B' else '')
                    stored=json.loads((root/'data/app/jobs'/f'{job["analysis_id"]}.json').read_text())
                    result=stored['analysis'];rid=result['recording_id']
                    alignment=json.loads((root/'data/alignment'/f'{rid}.json').read_text())
                    if alignment['aligner']['name']!='mfa':raise ValueError('Real MFA required')
                    state=trim_state(root,rid)
                    if mode=='A' and case['take_number']==1:baseline[case['text_id']]=stored
                    if detector in ('v1','both') or mode=='C':
                        rows.append(make_row(root,case,detail,stored,alignment,units,state,qa,'v1',dashboard))
                    if detector in ('v2','both') and mode!='C':
                        previous=None
                        if mode=='B':
                            previous_id=baseline[case['text_id']]['analysis']['recording_id']
                            previous=root/json.loads((root/'data/alignment'/f'{previous_id}.json').read_text())['audio']
                        v2=analyze_v2(root/alignment['audio'],case['text_id'],mode,previous=previous,root=root)
                        if v2['recording_id']!=rid:raise ValueError('v2 did not reuse the same MFA evidence')
                        rows.append(make_row(root,case,detail,publish_v2(root,v2,stored),alignment,units,state,qa,'v2',dashboard))
                    prepared=root/'data/human/prepared'/f'{case["take_id"]}.flac';prepared.parent.mkdir(parents=True,exist_ok=True)
                    wave,sr=sf.read(root/alignment['audio']);sf.write(prepared,wave,sr,subtype='PCM_16')
                    _write_json(progress_path,{'results':rows,'blockers':blockers})
                except (ValueError,TimeoutError,httpx.HTTPError) as exc:
                    message=f'{case["take_id"]} Mode {mode}: {exc}';LOGGER.exception(message);blockers.append(message)
                    _write_json(progress_path,{'results':rows,'blockers':blockers})
                    path=root/'docs/BLOCKERS.md';entry='\n- Human confirmed workflow: '+message+'\n'
                    if entry not in path.read_text():path.write_text(path.read_text()+entry)
    verify_inputs(root,confirmation)
    expected={'v1':14,'v2':14,'both':26}[detector]
    if len(rows)!=expected:blockers.append(f'Incomplete requested cohort: {len(rows)} completed rows, expected {expected}')
    payload={'schema':'human-recorder-confirmed-evaluation/v1','status':'incomplete' if blockers else 'complete',
        'genuine_takes_processed':len({r['take_id'] for r in rows}),
        'input_freeze_commit':'c1a6a02','confirmation_sha256':digest(confirmation_path),
        'threshold_tuning':False,'independent_annotation':False,'rater_responses':0,
        'results':rows,'pooled':pooled(rows),'blockers':blockers}
    _write_json(root/'data/human/evaluation.json',payload)
    (root/'reports/phase10_human_takes.md').write_text(report_text(payload))
    LOGGER.info('Human workflow finished: %d rows, %d problems',len(rows),len(blockers))
    return payload
