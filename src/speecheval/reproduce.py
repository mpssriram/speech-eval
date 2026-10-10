"""CPU recomputation of published detection/rubric numbers from frozen measurements.

This does not pretend to download an unpublished release or rebuild raw/ASR data.
Missing measured audio, Parquet or producer provenance is a hard failure.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
import logging
from pathlib import Path
import re
import tempfile
import time

import numpy as np
import yaml

LOGGER=logging.getLogger(__name__)
QUICK_SPEAKERS=('lv_sa','lv_tg','lv_wt')


def selected_rows(rows: list[dict], quick: bool) -> list[dict]:
    """Select all test variants, or exactly the three frozen Gettysburg test readers."""
    selected=[r for r in rows if r['split']=='test' and
              (not quick or r['text_id']=='gettysburg' and r['speaker_slug'] in QUICK_SPEAKERS)]
    if quick and {r['speaker_slug'] for r in selected}!=set(QUICK_SPEAKERS):
        raise ValueError('Quick reproduction requires all three frozen Gettysburg test readers')
    if not selected:raise ValueError('No frozen test rows are available')
    return selected


def numeric_claims(markdown: str) -> list[str]:
    """Return report numbers in order, excluding URLs, image filenames and code IDs."""
    body=re.sub(r'!?\[[^\]]*\]\([^)]*\)|`[^`]*`','',markdown)
    return re.findall(r'(?<![\w])[-+]?\d+(?:\.\d+)?(?:e[+-]?\d+)?(?![\w])',body)


def compare_report_numbers(expected: Path, actual: Path) -> None:
    """Fail with the first differing number; additions/deletions are differences too."""
    left=numeric_claims(expected.read_text());right=numeric_claims(actual.read_text())
    for i in range(max(len(left),len(right))):
        a=left[i] if i<len(left) else '<missing>'
        b=right[i] if i<len(right) else '<missing>'
        if a!=b:raise ValueError(f'{expected.name}: number {i+1} differs: expected {a}, actual {b}')


def file_sha(path: Path) -> str:
    """Stream SHA-256; audio must not be loaded into memory just to hash it."""
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def comparison_items(root: Path, rows: list[dict], setting: str) -> list[dict]:
    """Build the same frozen z tables, without opening out-of-scope test readers."""
    from speecheval.reference import build_reference,recording_values,map_words
    from speecheval.detect import z_table
    references={};items=[]
    for row in rows:
        text=row['text_id'];speaker=row['speaker_slug']
        if setting=='A-LOSO' and text not in ('gettysburg','o_captain'):continue
        if setting=='B-same-speaker' and text not in ('jfk_rice','reagan_challenger'):continue
        key=(text,speaker)
        if key not in references:
            references[key]=build_reference(text,speaker if setting=='A-LOSO' else None,root,
                f'{text}__{speaker}__orig' if setting=='B-same-speaker' else None)
        reference=references[key];alignment,values=recording_values(root,row['recording_id'])
        truth=json.loads((root/row['label_path']).read_text())['flaws'] if row['label_path'] else []
        uncertain=set(alignment.get('uncertain_words',[]))
        excluded=[f for f in truth if any(i in uncertain for i in range(f['word_start'],f['word_end']+1))]
        items.append({'recording_id':row['recording_id'],'table':z_table(alignment,values,reference,
                      map_words([w['norm'] for w in alignment['words']],reference['words'])),
                      'truth':[f for f in truth if f not in excluded],'excluded_truth':excluded,
                      'excluded_uncertain_truth':len(excluded),'duration_s':alignment['duration_s'],
                      'clean':row['kind']=='source'})
    if not items:raise ValueError(f'No measured rows for {setting}')
    return items


def recompute(root: Path, rows: list[dict], settings: dict, quick: bool) -> tuple[dict,dict]:
    """Actually rerun detection, bootstrap CIs and severity scores; never reuse results."""
    from speecheval.calibration import evaluate_settings
    from speecheval.evaluate import bootstrap_detection
    from speecheval.detect import detect
    from speecheval.score import rubric_scores
    from speecheval.validation import CATEGORY,coverage_series,monotonic_summary
    rubric=yaml.safe_load((root/'configs/rubric.yaml').read_text())
    result={};groups={};by_id={r['recording_id']:r for r in rows}
    for setting in ('A-LOSO',) if quick else ('A-LOSO','B-same-speaker'):
        items=comparison_items(root,rows,setting);metrics,evaluated=evaluate_settings(items,settings)
        result[setting]={'files':len(items),'metrics':metrics,'confidence_intervals':bootstrap_detection(evaluated),
                         'excluded_uncertain_truth':sum(i['excluded_uncertain_truth'] for i in items)}
        for item in items:
            row=by_id[item['recording_id']]
            if row['kind']!='synthetic' or '__mixed_' in row['recording_id']:continue
            label=json.loads((root/row['label_path']).read_text());flaw=label['flaws'][0]
            alignment=json.loads((root/'data/alignment'/f"{row['recording_id']}.json").read_text())
            words=alignment['words'];duration=Decimal(str(words[-1]['end']))-Decimal(str(words[0]['start']))
            scores=rubric_scores(detect(item['table'],item['duration_s'],settings),duration,rubric)
            groups.setdefault((label['reference_id'],flaw['type']),{})[flaw['severity']]=scores[CATEGORY[flaw['type']]]
    sources=[r['recording_id'] for r in rows if r['kind']=='source']
    complete,incomplete=coverage_series([(source,kind) for source in sources for kind in CATEGORY],groups)
    series={kind:[] for kind in CATEGORY}
    for (_,kind),values in complete.items():series[kind].append(values)
    severity={'types':{kind:monotonic_summary(values) for kind,values in series.items()},
              'series':series,'incomplete_series':incomplete}
    return result,severity


def cold_feature_checks(root: Path, rows: list[dict], output: Path) -> list[dict]:
    """Re-extract held-out source features on CPU in scratch, compare all five files."""
    from speecheval.features import extract_features
    settings=yaml.safe_load((root/'configs/default.yaml').read_text())['features'];checks=[]
    with tempfile.TemporaryDirectory(prefix='features-',dir=output) as temporary:
        scratch=Path(temporary)
        for row in rows:
            if row['kind']!='source':continue
            alignment=json.loads((root/'data/alignment'/f"{row['recording_id']}.json").read_text())
            hashes=extract_features(scratch,root/row['audio_path'],alignment,settings)
            for name,sha in hashes.items():
                if sha!=file_sha(root/name):raise ValueError(f'CPU feature bytes differ: {name}')
            checks.append({'recording_id':row['recording_id'],'artifacts':hashes})
    return checks


def run(root: Path, quick: bool = False, record_baseline: bool = False) -> dict:
    """Recompute report evidence; quick is one text/three test readers, max 900 seconds."""
    from speecheval.verify import _write_json
    from speecheval.validation import first_difference
    started=time.monotonic();output=root/'reports/reproduced';output.mkdir(parents=True,exist_ok=True)
    rows=list(csv.DictReader((root/'data/manifest/dataset_index.csv').open()))
    chosen=selected_rows(rows,quick);settings=yaml.safe_load((root/'configs/detector.yaml').read_text())
    frozen=json.loads((root/'data/review/final_evaluation.json').read_text())
    from speecheval.calibration import implementation_identity
    if frozen['implementation']!=implementation_identity(root) or frozen['config']!=settings:
        raise ValueError('Frozen detector implementation/configuration changed; do not tune on test')
    score_freeze=json.loads((root/'data/review/severity_validation.json').read_text())['freeze']
    for key,path in [('phase6_sha256',root/'data/review/final_evaluation.json'),
                     ('rubric_sha256',root/'configs/rubric.yaml'),
                     ('score_code_sha256',root/'src/speecheval/score.py'),
                     ('validation_code_sha256',root/'src/speecheval/validation.py')]:
        if file_sha(path)!=score_freeze[key]:raise ValueError(f'Frozen scoring input changed: {path}')
    feature_checks=cold_feature_checks(root,chosen,output)
    detection,severity=recompute(root,chosen,settings,quick)
    payload={'schema':'numeric-reproduction/v1','settings':detection,'severity':severity,
             'cold_cpu_features':feature_checks}
    if quick:
        baseline=root/'reports/reproduction_quick_expected.json'
        if record_baseline:_write_json(baseline,payload)
        else:
            difference=first_difference(json.loads(baseline.read_text()),payload)
            if difference:raise ValueError(f'Quick CPU result differs: {difference}')
        if time.monotonic()-started>=900:raise ValueError('Quick reproduction exceeded 15 minutes')
        destination=output/'quick.json'
    else:
        for name in detection:
            difference=first_difference(frozen['settings'][name],detection[name])
            if difference:raise ValueError(f'{name} differs from published evidence: {difference}')
        saved=json.loads((root/'data/review/severity_validation.json').read_text())
        difference=first_difference({k:saved[k] for k in severity},severity)
        if difference:raise ValueError(f'Severity validation differs: {difference}')
        payload['reproducibility']=rerun_identity(root)
        write_full_reports(root,output,frozen,detection,severity,payload['reproducibility'],rows,settings)
        payload['mode_C']=rerun_mode_c(root,output)
        destination=output/'full.json'
    _write_json(destination,payload)
    _write_json(output/('quick_runtime.json' if quick else 'full_runtime.json'),
                {'elapsed_seconds':round(time.monotonic()-started,3),'cpu_only':True,'test_rows':len(chosen)})
    LOGGER.info('REPRODUCED OK (%s, %.1f seconds)', 'quick' if quick else 'all Phase 6/7/8 numbers',time.monotonic()-started)
    return payload


def rerun_identity(root: Path) -> dict:
    """Run both analyses afresh and compare CPU bytes to committed host SHA-256s."""
    from speecheval.validation import test_analysis,compare_analysis_outputs
    saved=json.loads((root/'data/review/repro_validation.json').read_text())
    rows={r['recording_id']:r for r in csv.DictReader((root/'data/manifest/dataset_index.csv').open())};checks=[]
    for expected in saved['files']:
        row=rows[expected['recording_id']];a=test_analysis(root,row)
        before=(root/'data/analyses'/f"{a['analysis_id']}.json").read_bytes();b=test_analysis(root,row)
        actual=compare_analysis_outputs(root,a,b,before)
        if not actual['identical'] or actual['first_sha256']!=expected['first_sha256']:
            raise ValueError(f'CPU/host analysis bytes differ: {row["recording_id"]}')
        checks.append({'recording_id':row['recording_id'],**actual})
    return {'host_identical':sum(c['identical'] for c in checks),'files':checks,
            'docker_status':saved['docker_status']}


def rerun_mode_c(root: Path, output: Path) -> dict:
    """Recompute the published no-reference comparison using its unchanged evaluator."""
    from speecheval.mode_c import evaluate_mode_c
    from speecheval.validation import first_difference
    saved_path=root/'data/review/mode_c_evaluation.json'
    report=root/'reports/phase08_mode_c.md'
    saved_bytes=saved_path.read_bytes();report_bytes=report.read_bytes()
    # The evaluator writes its normal artifacts. Restore the originals even on failure.
    try:
        actual=evaluate_mode_c(root)
        difference=first_difference(json.loads(saved_bytes),actual)
        if difference:raise ValueError(f'Mode C comparison differs: {difference}')
        reproduced=output/'phase08_mode_c.md';reproduced.write_bytes(report.read_bytes())
        with tempfile.TemporaryDirectory(prefix='mode-c-report-',dir=output) as temporary:
            expected=Path(temporary)/report.name;expected.write_bytes(report_bytes)
            compare_report_numbers(expected,reproduced)
        return actual
    finally:
        saved_path.write_bytes(saved_bytes);report.write_bytes(report_bytes)


def write_full_reports(root: Path, output: Path, frozen: dict, detection: dict, severity: dict,
                       repro: dict, rows: list[dict], settings: dict) -> None:
    """Render fresh reports then compare every numeric literal, not just headline F1."""
    from speecheval.calibration import write_results_report,evaluate_settings
    from speecheval.validation import write_validation_report
    from speecheval.verify import _write_json
    audit=json.loads((root/'data/review/detector_calibration.json').read_text())
    dev_items=comparison_items(root,[r for r in rows if r['split']=='dev'],'A-LOSO')
    dev_metrics,_=evaluate_settings(dev_items,settings)
    alarm=dev_metrics['overall']['false_alarms_per_minute'];budget=audit['clean_alarm_budget']
    with tempfile.TemporaryDirectory(prefix='reports-',dir=output) as temporary:
        scratch=Path(temporary);write_results_report(scratch,{**frozen,'settings':detection})
        phase6=scratch/'reports/phase06_results.md';body=phase6.read_text()
        guard=f'The DEV clean-alarm guard was **{"met" if alarm<=budget else "not met"}**: {alarm:.3f} alarms/min versus the requested ≤{budget:g}. This is an acceptance limitation, not a passing result. See [DEV calibration](phase06_calibration.md).\n'
        phase6.write_text(body.replace('Learned detector:',guard+'Learned detector:',1))
        freeze=json.loads((root/'data/review/severity_validation.json').read_text())['freeze']
        _write_json(scratch/'data/review/severity_validation.json',{**severity,'freeze':freeze})
        _write_json(scratch/'data/review/repro_validation.json',{**repro,'freeze':freeze})
        write_validation_report(scratch)
        for name in ('phase06_results.md','phase07_validation.md'):
            actual=scratch/'reports'/name;compare_report_numbers(root/'reports'/name,actual)
            (output/name).write_text(actual.read_text())


def main() -> None:
    """Run the numeric release checks on CPU; fail loudly rather than print fake success."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick',action='store_true')
    parser.add_argument('--record-quick-baseline',action='store_true',help='Developer-only: record measured host subset evidence')
    args=parser.parse_args()
    if args.record_quick_baseline and not args.quick:parser.error('Recording a baseline requires --quick')
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    try:run(Path.cwd(),args.quick,args.record_quick_baseline)
    except (FileNotFoundError,ValueError) as exc:
        LOGGER.error('REPRODUCTION FAILED: %s. Restore frozen prepared audio, features and producer JSON provenance; see docs/DOCKER.md.',exc)
        raise SystemExit(1) from exc


if __name__=='__main__':main()
