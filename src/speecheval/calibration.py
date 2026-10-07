"""Development-only calibration; held-out data never selects detector settings."""
from __future__ import annotations
import copy
import csv
import hashlib
import itertools
import json
import logging
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
import yaml

from speecheval.detect import detect,z_table
from speecheval.evaluate import FLAW_TYPES,detection_metrics,match_regions,bootstrap_detection
from speecheval.reference import build_reference,recording_values,map_words

LOGGER=logging.getLogger(__name__)


def write_results_report(root: Path, result: dict) -> None:
    """Write measured held-out results; unavailable human evidence stays explicit."""
    def number(value):return 'N/A' if value is None else f'{value:.3f}'
    def interval(value):return 'N/A' if value is None else f'[{value[0]:.3f}, {value[1]:.3f}]'
    lines=['# Phase 6 detection results','',f"Evaluated code commit: `{result['evaluated_commit']}`.",'',
           'Detector settings were selected on DEV only. These are synthetic-effect labels, not human judgments of speaking quality.',
           f"Learned detector: {result['learned_detector']}.",'']
    for setting,entry in result['settings'].items():
        lines.extend([f'## {setting}','',f"Files: {entry['files']}; uncertain truth regions excluded: {entry['excluded_uncertain_truth']}.",'',
                      '| Type | Precision | Recall (95% CI) | F1 (95% CI) | Onset ms | Offset ms | Clean alarms/min |',
                      '|---|---:|---|---|---:|---:|---:|'])
        for kind in (*FLAW_TYPES,'overall'):
            m=entry['metrics'][kind];ci=entry['confidence_intervals'][kind]
            lines.append(f"| {kind} | {number(m['precision'])} | {number(m['recall'])} {interval(ci['recall_95ci'])} | {number(m['f1'])} {interval(ci['f1_95ci'])} | {number(m['onset_median_ms'])} | {number(m['offset_median_ms'])} | {number(m['false_alarms_per_minute'])} |")
        valid=[(entry['metrics'][k]['recall'],k) for k in FLAW_TYPES if entry['metrics'][k]['recall'] is not None]
        if valid:
            weakest=min(valid);strongest=max(valid)
            lines.extend(['',f"Highest measured recall: {strongest[1]} ({strongest[0]:.3f}); lowest: {weakest[1]} ({weakest[0]:.3f}). This is conditional on this dataset, aligner and injected effects—not a human realism claim.",''])
        lines.extend([f'![Severity recall](img/recall_vs_severity_{setting}.png)',f'![Wrong-type confusion](img/confusion_{setting}.png)',''])
    for key,title in (('human_A','Human-A'),('human_B','Human-B')):
        lines.extend([f'## {title}','',result[key]['status'], 'No recordings, labels, or scores were invented.',''])
    lines.extend(['## Limitations','',
                  'File-level bootstrap CIs use 1,000 resamples with a fixed seed. Reference models use train speakers only. Uncertain truth regions and overlapping predictions are excluded symmetrically. Visual gold boundaries have a pending human spot-check. Missing human settings prevent full Phase 6 acceptance.',''])
    directory=root/'reports';directory.mkdir(parents=True,exist_ok=True)
    (directory/'phase06_results.md').write_text('\n'.join(lines),encoding='utf-8')


def exclude_uncertain_predictions(predictions: list[dict], excluded: list[dict]) -> list[dict]:
    """Ignore predicted fragments overlapping a truth region removed for uncertainty."""
    return [p for p in predictions if not any(
        max(p['word_start'],t['word_start'])<=min(p['word_end'],t['word_end'])
        for t in excluded)]


def evaluation_input_identity(root: Path) -> dict[str,str]:
    """Bind held-out reuse to exact dataset, reference and measurement bytes."""
    inputs={}
    for folder in ('data/manifest','data/labels','data/alignment','data/features','data/reference','data/transcripts/canonical',
                   'data/audio/hq','data/flawed/hq','data/flawed/align16k'):
        directory=root/folder
        if not directory.exists():continue
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.suffix in ('.json','.yaml','.csv','.parquet','.txt','.wav','.flac'):
                with path.open('rb') as stream:inputs[str(path.relative_to(root))]=hashlib.file_digest(stream,'sha256').hexdigest()
    return inputs


def implementation_identity(root: Path) -> dict[str,str]:
    """Frozen detection/calibration implementation, independent of report-only commits."""
    names=('calibration.py','evaluate.py','detect.py','reference.py','features.py','transcripts.py')
    return {name:hashlib.sha256((root/'src/speecheval'/name).read_bytes()).hexdigest()
            for name in names if (root/'src/speecheval'/name).exists()}


def calibration_identity(root: Path) -> dict:
    """Fingerprint only train/dev measurement and label dependencies; never open test evidence."""
    inputs={};index=root/'data/manifest/dataset_index.csv'
    if index.exists():
        rows=list(csv.DictReader(index.open()))
        for row in rows:
            if row['split'] not in ('train','dev'):continue
            rid=row['recording_id'];paths=[row['audio_path'],row.get('label_path',''),f'data/alignment/{rid}.json']
            paths.extend(f'data/features/{folder}/{rid}.parquet' for folder in ('words','windows'))
            for relative in paths:
                path=root/relative
                if relative and path.is_file():
                    with path.open('rb') as stream:inputs[relative]=hashlib.file_digest(stream,'sha256').hexdigest()
    for relative in ('configs/default.yaml','configs/splits.yaml'):
        path=root/relative
        if path.exists():inputs[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted((root/'data/transcripts/canonical').glob('*.txt')):
        inputs[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'inputs':inputs,'implementation':implementation_identity(root)}


def validate_calibration_freeze(root: Path, audit: dict) -> None:
    """Reject changed dev/training evidence before any held-out evaluation."""
    if audit.get('freeze')!=calibration_identity(root):raise ValueError('Stale calibration: training/dev evidence or detector code changed')


def reuse_final_result(previous: dict, implementation: dict, inputs: dict) -> dict:
    """Never silently repeat held-out evaluation after code/data changes."""
    if previous.get('implementation')!=implementation or previous.get('inputs')!=inputs:
        raise ValueError('Held-out freeze changed; an explicit authorized rerun reason is required')
    return previous


def repair_alarm_budget(items: list[dict], settings: dict, budget: float = .5) -> dict:
    """Establish clean-dev feasibility before F1 optimization, allowing improving intermediate moves."""
    current=copy.deepcopy(settings)
    for _ in range(len(FLAW_TYPES)*3):
        rate=evaluate_settings(items,current)[0]['overall']['false_alarms_per_minute']
        if rate is None:raise ValueError('Clean development evidence is required')
        if rate<=budget:return current
        choices=[]
        for kind in FLAW_TYPES:
            for k in np.arange(1.5,3.5001,.25):
                trial=copy.deepcopy(current);trial['k'][kind]=float(k)
                alarm=evaluate_settings(items,trial)[0]['overall']['false_alarms_per_minute']
                choices.append((alarm,-float(k),kind,trial))
        best=min(choices,key=lambda x:x[:3])
        if best[0]>=rate:break
        current=best[3]
    return current


def choose_threshold(candidates: list[dict], budget: float = .5) -> dict:
    """Maximize type F1 under the combined clean alarm budget; ties prefer higher k."""
    feasible=[c for c in candidates if c['false_alarms_per_minute'] is not None and c['false_alarms_per_minute']<=budget]
    return max(feasible,key=lambda c:((c['f1'] if c['f1'] is not None else -1.),c['k'])) if feasible else max(candidates,key=lambda c:c['k'])


def fit_severity_bins(z: list[float], target: list[int], original: list[float]) -> tuple[list[float],float | None]:
    """Fit four increasing cuts on matched dev pairs; fixed quantile grid and stable tie-breaking."""
    x=np.asarray(z,dtype=float);y=np.asarray(target)
    if len(x)<5 or len(set(y))<2 or len(set(x))<2:return original,None
    candidates=sorted(set(np.quantile(x,np.linspace(.05,.95,19)).tolist()+original[1:]))
    candidates=[v for v in candidates if v>original[0]]
    best=None
    for cuts in itertools.combinations(candidates,4):
        bins=[original[0],*cuts];predicted=np.clip(np.searchsorted(bins,x,side='right'),1,5)
        if len(set(predicted))<2:continue
        rho=float(spearmanr(predicted,y).statistic)
        key=(rho,-sum(abs(a-b) for a,b in zip(bins,original)),tuple(-v for v in bins))
        if best is None or key>best[0]:best=(key,bins)
    return (best[1],best[0][0]) if best else (original,None)


def comparison_items(root: Path,split: str,setting: str = 'A-LOSO') -> list[dict]:
    """Load real features and reference evidence once; exclude uncertain truth/evidence words."""
    if split not in ('train','dev','test'):raise ValueError('Invalid split')
    rows=list(csv.DictReader((root/'data/manifest/dataset_index.csv').open()));references={};items=[]
    for row in rows:
        if row['split']!=split:continue
        text=row['text_id'];speaker=row['speaker_slug']
        if setting=='A-LOSO':
            if text not in ('gettysburg','o_captain'):continue
            key=(text,speaker);previous=None
        elif setting=='B-same-speaker':
            if text not in ('jfk_rice','reagan_challenger'):continue
            previous=f'{text}__{speaker}__orig';key=(text,previous)
        else:raise ValueError('Unknown evaluation setting')
        if key not in references:references[key]=build_reference(text,speaker if setting=='A-LOSO' else None,root,previous)
        reference=references[key];alignment,values=recording_values(root,row['recording_id'])
        mapping=map_words([w['norm'] for w in alignment['words']],reference['words']);table=z_table(alignment,values,reference,mapping)
        truth=json.loads((root/row['label_path']).read_text())['flaws'] if row['label_path'] else []
        uncertain=set(alignment.get('uncertain_words',[]))
        excluded=[f for f in truth if any(i in uncertain for i in range(f['word_start'],f['word_end']+1))]
        truth=[f for f in truth if f not in excluded]
        items.append({'recording_id':row['recording_id'],'split':split,'truth':truth,'excluded_truth':excluded,'excluded_uncertain_truth':len(excluded),
                      'duration_s':alignment['duration_s'],'clean':row['kind']=='source','table':table})
    if not items:raise ValueError(f'No {split} files in {setting}')
    return items


def evaluate_settings(items: list[dict], settings: dict) -> tuple[dict,list[dict]]:
    evaluated=[{**item,'predicted':exclude_uncertain_predictions(detect(item['table'],item['duration_s'],settings),item.get('excluded_truth',[]))} for item in items]
    return detection_metrics(evaluated),evaluated


def calibrate(root: Path | None = None) -> dict:
    """Coordinate sweep per type under the GLOBAL clean-dev false-alarm guard; no test access."""
    from speecheval.verify import _write_json
    root=root or Path.cwd();build=json.loads((root/'data/manifest/dataset_build.json').read_text())
    if build['partial_sources'] or not build['features_completed']:raise ValueError('Full synthetic dataset must complete before calibration')
    path=root/'configs/detector.yaml';original=yaml.safe_load(path.read_text());settings=copy.deepcopy(original)
    settings['engine']='rules';settings['k']={kind:3.5 for kind in FLAW_TYPES}
    items=comparison_items(root,'dev');history=[]
    settings=repair_alarm_budget(items,settings)
    # Deterministic coordinate search accounts for cross-type suppression; exhaustive
    # 9**7 search is not justified by this small development set.
    for iteration in range(3):
        changed=False
        for kind in FLAW_TYPES:
            candidates=[]
            for k in np.arange(1.5,3.5001,.25):
                trial=copy.deepcopy(settings);trial['k'][kind]=float(k)
                metrics,_=evaluate_settings(items,trial)
                candidates.append({'k':float(k),'f1':metrics[kind]['f1'],'false_alarms_per_minute':metrics['overall']['false_alarms_per_minute']})
            selected=choose_threshold(candidates)
            changed|=settings['k'][kind]!=selected['k'];settings['k'][kind]=selected['k']
            history.append({'iteration':iteration,'type':kind,'candidates':candidates,'selected':selected})
        if not changed:break
    metrics,evaluated=evaluate_settings(items,settings);z=[];target=[]
    for item in evaluated:
        for p,t in match_regions(item['predicted'],item['truth']):
            z.append(item['predicted'][p]['mean_abs_z']);target.append(item['truth'][t]['severity'])
    settings['severity_z_bins'],rho=fit_severity_bins(z,target,original['severity_z_bins'])
    metrics,evaluated=evaluate_settings(items,settings)
    inputs={}
    for item in items:
        rid=item['recording_id']
        for folder in ('words','windows'):
            artifact=root/'data/features'/folder/f'{rid}.parquet';inputs[str(artifact.relative_to(root))]=hashlib.sha256(artifact.read_bytes()).hexdigest()
        for relative in (f'data/alignment/{rid}.json',f'data/labels/{rid}.json'):
            artifact=root/relative
            if artifact.exists():inputs[relative]=hashlib.sha256(artifact.read_bytes()).hexdigest()
    result={'schema':'detector_calibration/v1','split':'dev','setting':'A-LOSO','files':len(items),'seed':20261001,
            'old_config':original,'selected_config':settings,'sweeps':history,'metrics':metrics,
            'confidence_intervals':bootstrap_detection(evaluated),'inputs':inputs,'severity_fit_spearman':rho,
            'clean_alarm_budget':.5,'clean_alarm_budget_met':metrics['overall']['false_alarms_per_minute']<=.5,
            'learned_detector':'omitted under PLAN cut line 2','human_validation':'PENDING',
            'freeze':calibration_identity(root)}
    # Preserve the initial values in the first audit rather than progressively
    # treating a previous calibrated result as uncalibrated ground truth.
    audit=root/'data/review/detector_calibration_initial.json'
    if not audit.exists():_write_json(audit,{'config':original})
    initial=json.loads(audit.read_text())['config']
    comments='# Original pre-calibration configuration: '+json.dumps(initial,sort_keys=True)+'\n'
    path.write_text(comments+yaml.safe_dump(settings,sort_keys=False))
    _write_json(root/'data/review/detector_calibration.json',result)
    write_calibration_report(root,result)
    LOGGER.info('Calibrated %d dev files: F1 %.3f, clean alarms %.3f/min, budget met=%s',len(items),metrics['overall']['f1'],metrics['overall']['false_alarms_per_minute'],result['clean_alarm_budget_met'])
    return result


def write_calibration_report(root: Path, result: dict) -> None:
    """Write development-only threshold evidence and measured sweep curves."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory=root/'reports/img';directory.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(2,4,figsize=(14,7))
    last={row['type']:row for row in result['sweeps']}
    for axis,kind in zip(axes.flat,FLAW_TYPES):
        row=last[kind];axis.plot([c['k'] for c in row['candidates']],[c['f1'] for c in row['candidates']],marker='o')
        axis.axvline(row['selected']['k'],color='red',linestyle='--');axis.set(title=kind,xlabel='k',ylabel='Dev F1',ylim=(0,1))
    axes.flat[-1].axis('off');fig.tight_layout();fig.savefig(directory/'dev_threshold_sweeps.png',dpi=130);plt.close(fig)
    lines=['# Phase 6 development calibration','',f"Files: {result['files']}; split: DEV only; setting: A-LOSO.",'',
           'Deterministic coordinate sweeps account for cross-type suppression. Each type is swept over 1.5–3.5 in increments of 0.25, up to three rounds. Ties prefer the conservative threshold. This is coordinate optimization, not exhaustive joint optimization.','',
           '| Type | Selected k | Dev F1 |','|---|---:|---:|']
    for kind in FLAW_TYPES:lines.append(f"| {kind} | {result['selected_config']['k'][kind]:.2f} | {result['metrics'][kind]['f1']} |")
    lines.extend(['',f"Combined clean-dev alarms/min: {result['metrics']['overall']['false_alarms_per_minute']:.3f}; ≤0.5 guard satisfied: {result['clean_alarm_budget_met']}.",
                  f"Severity cut points: {result['selected_config']['severity_z_bins']}; matched DEV Spearman: {result['severity_fit_spearman']}.",'',
                  '![Dev threshold sweeps](img/dev_threshold_sweeps.png)','',
                  'Synthetic labels describe controlled effects, not human perceptual judgments. Human recordings/labels are pending. No held-out test values selected these thresholds. Learned detector deferred under the plan cut line.',''])
    (root/'reports/phase06_calibration.md').write_text('\n'.join(lines),encoding='utf-8')


def evaluate_final(root: Path | None = None) -> dict:
    """Evaluate frozen committed rules; missing human labels are unavailable, never synthesized."""
    import subprocess
    from speecheval.verify import _write_json
    root=root or Path.cwd()
    dirty=subprocess.check_output(['git','status','--porcelain','--','src','configs'],cwd=root,text=True)
    if dirty.strip():raise ValueError('Commit/freeze implementation and detector configuration before held-out evaluation')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    settings=yaml.safe_load((root/'configs/detector.yaml').read_text())
    audit=json.loads((root/'data/review/detector_calibration.json').read_text())
    if settings!=audit['selected_config']:raise ValueError('Detector configuration differs from dev-calibration freeze')
    validate_calibration_freeze(root,audit)
    path=root/'data/review/final_evaluation.json'
    if path.exists():
        previous=json.loads(path.read_text())
        previous=reuse_final_result(previous,implementation_identity(root),evaluation_input_identity(root))
        write_results_report(root,previous)
        return previous
    result={'schema':'detection_final/v1','evaluated_commit':commit,'config':settings,'implementation':implementation_identity(root),
            'human_A':{'status':'PENDING recordings and actual labels'},'human_B':{'status':'PENDING recordings and actual labels'},
            'learned_detector':'not trained; PLAN cut line 2','settings':{}}
    onsets=[]
    for setting in ('A-LOSO','B-same-speaker'):
        items=comparison_items(root,'test',setting);metrics,evaluated=evaluate_settings(items,settings)
        result['settings'][setting]={'files':len(items),'metrics':metrics,'confidence_intervals':bootstrap_detection(evaluated),
                                    'excluded_uncertain_truth':sum(i['excluded_uncertain_truth'] for i in items)}
        for item in evaluated:
            for p,t in match_regions(item['predicted'],item['truth']):
                onsets.append(abs(item['predicted'][p]['start']-item['truth'][t]['start'])*1000)
        plot_metrics(root,setting,metrics)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axis=plt.subplots();axis.hist(onsets,bins=25);axis.set(xlabel='Matched onset absolute error (ms)',ylabel='Regions')
    fig.tight_layout();fig.savefig(root/'reports/img/onset_error_hist.png',dpi=130);plt.close(fig)
    result['inputs']=evaluation_input_identity(root)
    _write_json(root/'data/review'/f'final_evaluation_{commit[:12]}.json',result);_write_json(path,result)
    write_results_report(root,result)
    LOGGER.info('Held-out evaluation of %s completed; human settings are pending',commit)
    return result


def plot_metrics(root: Path,setting: str,metrics: dict) -> None:
    """Required severity recall and type confusion charts, without narrative phase reports."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory=root/'reports/img';directory.mkdir(parents=True,exist_ok=True)
    fig,axis=plt.subplots(figsize=(9,5))
    for kind in FLAW_TYPES:
        axis.plot(range(1,6),[metrics[kind]['recall_by_severity'][str(s)] if metrics[kind]['recall_by_severity'][str(s)] is not None else np.nan for s in range(1,6)],marker='o',label=kind)
    axis.set(xlabel='True injected severity',ylabel='Recall',ylim=(0,1),title=setting);axis.legend(fontsize=8);fig.tight_layout()
    fig.savefig(directory/f'recall_vs_severity_{setting}.png',dpi=130);plt.close(fig)
    confusion=np.asarray([[metrics['confusion'][t][p] for p in FLAW_TYPES] for t in FLAW_TYPES])
    fig,axis=plt.subplots(figsize=(9,7));image=axis.imshow(confusion,cmap='Blues');fig.colorbar(image,ax=axis)
    axis.set(xticks=range(7),yticks=range(7),xticklabels=FLAW_TYPES,yticklabels=FLAW_TYPES,xlabel='Predicted type',ylabel='True type',title=setting)
    plt.setp(axis.get_xticklabels(),rotation=45,ha='right');fig.tight_layout();fig.savefig(directory/f'confusion_{setting}.png',dpi=130);plt.close(fig)
