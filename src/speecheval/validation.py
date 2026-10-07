"""Rubric validation on frozen detectors; human and Docker evidence is never fabricated."""
from __future__ import annotations
import csv
import hashlib
import json
import logging
from pathlib import Path
import numpy as np
import yaml
from scipy.stats import spearmanr

LOGGER=logging.getLogger(__name__)
CATEGORY={'rushing':'pace','dragging':'pace','monotone':'pitch','too_quiet':'volume',
          'mumbling':'clarity','awkward_pause':'pauses','missing_pause':'pauses'}


def scoring_freeze(root: Path) -> dict:
    """Require genuine unchanged Phase 6 evidence and bind rubric/validator versions."""
    from speecheval.calibration import implementation_identity,evaluation_input_identity,reuse_final_result
    path=root/'data/review/final_evaluation.json'
    if not path.exists():raise ValueError('Missing frozen Phase 6 evaluation')
    saved=json.loads(path.read_text())
    if saved.get('schema')!='detection_final/v1' or not saved.get('evaluated_commit') or not saved.get('settings'):
        raise ValueError('Invalid frozen Phase 6 evaluation')
    if yaml.safe_load((root/'configs/detector.yaml').read_text())!=saved['config']:raise ValueError('Changed frozen detector configuration')
    actual=evaluation_input_identity(root)
    # Later unrelated products (e.g. Mode C norms) are not inputs to the frozen
    # Phase 6 result; every originally evaluated input must still match.
    reuse_final_result(saved,implementation_identity(root),{key:actual.get(key) for key in saved['inputs']})
    return {'phase6_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'rubric_sha256':hashlib.sha256((root/'configs/rubric.yaml').read_bytes()).hexdigest(),
            'score_code_sha256':hashlib.sha256(Path(__file__).with_name('score.py').read_bytes()).hexdigest(),
            'validation_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def coverage_series(expected: list[tuple[str,str]], groups: dict) -> tuple[dict,list[dict]]:
    """Account for every frozen source/type, including completely absent series."""
    complete={};missing=[]
    for source,kind in sorted(expected):
        values=groups.get((source,kind),{})
        absent=sorted(set(range(1,6))-set(values))
        if absent:missing.append({'source':source,'type':kind,'missing_severities':absent})
        else:complete[(source,kind)]=[values[i] for i in range(1,6)]
    return complete,missing


def compare_analysis_outputs(root: Path,a: dict,b: dict,before: bytes) -> dict:
    """Compare the actual second result file, even when its content-addressed ID differs."""
    after=(root/'data/analyses'/f"{b['analysis_id']}.json").read_bytes()
    return {'identical':before==after and a==b,'first_difference':first_difference(a,b),
            'first_sha256':hashlib.sha256(before).hexdigest(),'second_sha256':hashlib.sha256(after).hexdigest(),
            'analysis_id':a['analysis_id'],'second_analysis_id':b['analysis_id']}


def monotonic_summary(series: list[list[float]]) -> dict:
    """Summarize five injected-severity scores; constant series have undefined correlation."""
    if any(len(row)!=5 for row in series):raise ValueError('Every severity series must contain five scores')
    correlations=[float(spearmanr(range(1,6),row).statistic) for row in series if len(set(row))>1]
    return {'series':len(series),'constant_series':sum(len(set(row))==1 for row in series),
            'median_spearman':float(np.median(correlations)) if correlations else None,
            'non_increasing_percent':100*sum(all(a>=b for a,b in zip(row,row[1:])) for row in series)/len(series) if series else None}


def first_difference(a: object,b: object,path: str = '$') -> str | None:
    """Return the first differing JSON field, not a generic reproducibility failure."""
    if type(a)!=type(b):return path
    if isinstance(a,dict):
        if a.keys()!=b.keys():return path
        for key in sorted(a):
            diff=first_difference(a[key],b[key],path+'.'+key)
            if diff:return diff
        return None
    if isinstance(a,list):
        if len(a)!=len(b):return path
        for i,(left,right) in enumerate(zip(a,b)):
            diff=first_difference(left,right,f'{path}[{i}]')
            if diff:return diff
        return None
    return None if a==b else path


def test_analysis(root: Path,row: dict) -> dict:
    """Analyze a test row with frozen rules; never tune thresholds from scores."""
    from speecheval.pipeline import analyze
    text=row['text_id'];speaker=row['speaker_slug']
    if text in ('jfk_rice','reagan_challenger'):
        return analyze(root/row['audio_path'],text,mode='B',previous=root/'data/audio/hq'/f'{text}__{speaker}__orig.wav',root=root)
    return analyze(root/row['audio_path'],text,exclude_speaker=speaker,root=root)


def validate_severity(root: Path | None = None) -> dict:
    """Measure score-vs-injected-severity series on test data after the Phase 6 freeze."""
    from speecheval.verify import _write_json
    root=root or Path.cwd()
    freeze=scoring_freeze(root)
    rows=list(csv.DictReader((root/'data/manifest/dataset_index.csv').open()));groups={}
    for row in rows:
        if row['split']!='test' or row['kind']!='synthetic' or '__mixed_' in row['recording_id']:continue
        label=json.loads((root/row['label_path']).read_text());flaw=label['flaws'][0]
        result=test_analysis(root,row);key=(label['reference_id'],flaw['type'])
        groups.setdefault(key,{})[flaw['severity']]=result['scores'][CATEGORY[flaw['type']]]
    sources=yaml.safe_load((root/'configs/splits.yaml').read_text())['test']
    complete,incomplete=coverage_series([(source,kind) for source in sources for kind in CATEGORY],groups)
    series={kind:[] for kind in CATEGORY}
    for (_,kind),values in complete.items():series[kind].append(values)
    result={'schema':'severity_validation/v1','types':{kind:monotonic_summary(values) for kind,values in series.items()},
            'series':series,'incomplete_series':incomplete,'freeze':freeze,'human_agreement':'PENDING actual independent ratings'}
    _write_json(root/'data/review/severity_validation.json',result)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axis=plt.subplots(figsize=(10,6))
    for kind,values in series.items():
        if not values:continue
        array=np.asarray(values);mean=array.mean(axis=0);sd=array.std(axis=0)
        axis.plot(range(1,6),mean,marker='o',label=kind);axis.fill_between(range(1,6),mean-sd,mean+sd,alpha=.1)
    axis.set(xlabel='Injected severity',ylabel='Category score (0–10)',ylim=(0,10));axis.legend(fontsize=8);fig.tight_layout()
    directory=root/'reports/img';directory.mkdir(parents=True,exist_ok=True);fig.savefig(directory/'score_vs_severity.png',dpi=130);plt.close(fig)
    write_validation_report(root);LOGGER.info('Severity validation completed: %d complete series',sum(len(v) for v in series.values()))
    return result


def validate_repro(root: Path | None = None) -> dict:
    """Compare two actual host analysis runs on ten seeded test files; Docker remains separate."""
    from speecheval.verify import _write_json
    root=root or Path.cwd()
    freeze=scoring_freeze(root)
    rows=[r for r in csv.DictReader((root/'data/manifest/dataset_index.csv').open()) if r['split']=='test']
    selected=np.random.default_rng(20261001).choice(len(rows),min(10,len(rows)),replace=False);results=[]
    for i in selected:
        row=rows[i];a=test_analysis(root,row);path=root/'data/analyses'/f"{a['analysis_id']}.json";before=path.read_bytes()
        b=test_analysis(root,row)
        results.append({'recording_id':row['recording_id'],**compare_analysis_outputs(root,a,b,before)})
    result={'schema':'repro_validation/v1','host_identical':sum(r['identical'] for r in results),'files':results,'freeze':freeze,
            'docker_status':'PENDING Phase 9 CPU image test; host-only evidence is not cross-environment proof'}
    _write_json(root/'data/review/repro_validation.json',result);write_validation_report(root)
    return result


def write_validation_report(root: Path) -> None:
    """Generate only measured score validation results and explicit missing evidence."""
    audits=[json.loads(path.read_text()) for path in (root/'data/review/severity_validation.json',root/'data/review/repro_validation.json') if path.exists()]
    if len(audits)==2 and audits[0]['freeze']!=audits[1]['freeze']:raise ValueError('Cannot combine score validation results from different freezes')
    lines=['# Phase 7 scoring validation','',
           'Scores are deterministic penalties, not a validated perceptual scale. Configurable design weights: pace/pitch 0.25 each, pauses 0.20, volume/clarity 0.15 each; pace/pitch are emphasized because of their perceived delivery importance, not an external standard. Decimal ROUND_HALF_UP is used, with overall computed from rounded category scores.','',
           'Worked example: severity-3 rushing over 10% of speech gives pace = 10 − 3×0.10×10 = 7.0.','']
    path=root/'data/review/severity_validation.json'
    if path.exists():
        result=json.loads(path.read_text());lines.extend(['## Severity monotonicity','',
            '| Type | Complete series | Median Spearman | Non-increasing % | Constant series |','|---|---:|---:|---:|---:|'])
        for kind,m in result['types'].items():lines.append(f"| {kind} | {m['series']} | {m['median_spearman']} | {m['non_increasing_percent']} | {m['constant_series']} |")
        lines.extend(['','Constant series have undefined Spearman; non-increasing alone does not demonstrate sensitivity.',
                      f"Incomplete five-severity series excluded: {len(result['incomplete_series'])}.",'','![Score vs severity](img/score_vs_severity.png)',''])
    path=root/'data/review/repro_validation.json'
    if path.exists():
        result=json.loads(path.read_text());lines.extend(['## Reproducibility','',
            f"Actual two-run host byte identity: {result['host_identical']}/{len(result['files'])}.",result['docker_status'],''])
    lines.extend(['## Independent human agreement','',
                  'PENDING: actual user takes and independent ratings from at least three raters. No inter-rater alpha, system–human correlation or confidence interval can be claimed yet.',''])
    directory=root/'reports';directory.mkdir(parents=True,exist_ok=True);(directory/'phase07_validation.md').write_text('\n'.join(lines),encoding='utf-8')
