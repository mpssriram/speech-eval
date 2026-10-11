"""One decision-bearing post-hoc v2 test evaluation; subsequent runs are frozen reproductions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import yaml

from speecheval.tune_v2 import promotion_allowed,select_best

DISCLAIMER='post-hoc v2; test split was seen with v1, so results are optimistic'
DEV_BASELINE_HASHES={
    'data/manifest/dataset_index.csv':'c58a569101af60a7fc87c29e8ebbaa8dc664074446bb343bce8b1d8720d764bb',
    'configs/detector.yaml':'f0759b1d459d2f1fd06452a1fa617e49444558f03c2ee8f8d1dfc05e1bc87e09',
}
CODE=('detector_v2.py','tune_v2.py','evaluate_v2.py','cli.py','pipeline.py','detect.py',
      'reference.py','explain.py','score.py','calibration.py','evaluate.py','reproduce.py')


def validate_gate(audit: dict) -> None:
    """Refuse test access unless bounded DEV results meet the predeclared guard/margin."""
    history=audit.get('history',[])
    if not 1<=len(history)<=30 or [v['id'] for v in history]!=list(range(1,len(history)+1)):
        raise ValueError('Invalid DEV configuration budget/history')
    if audit.get('split')!='dev' or audit.get('elapsed_seconds',14401)>14400:
        raise ValueError('Invalid DEV split/time budget')
    if audit.get('selected_id') not in [h['id'] for h in history]:raise ValueError('Missing selected DEV configuration')
    selected=next(h for h in history if h['id']==audit['selected_id'])
    if audit['selected_config']!=selected['config'] or audit['selected_metrics']!=selected['metrics']:
        raise ValueError('Selected DEV configuration/metrics differ from history')
    for entry in history:
        digest=hashlib.sha256(json.dumps(entry['config'],sort_keys=True).encode()).hexdigest()
        if 'config_sha256' in entry and entry['config_sha256']!=digest:
            raise ValueError('DEV configuration hash differs from history')
    if select_best(history)['id']!=selected['id']:
        raise ValueError('DEV selection violates the predeclared objective')
    old=audit['v1_metrics']['overall'];new=audit['selected_metrics']['overall']
    if not promotion_allowed(old['f1'],new['f1'],new['false_alarms_per_minute']):
        raise ValueError('DEV promotion gate failed; do not evaluate test')


def verify_hashes(root: Path,hashes: dict[str,str]) -> None:
    """Reject changed frozen inputs or code; no permissive substitution of measured files."""
    from speecheval.reproduce import file_sha
    for relative,expected in hashes.items():
        path=root/relative
        if not path.resolve().is_relative_to(root.resolve()) or not path.is_file() or file_sha(path)!=expected:
            raise ValueError(f'Frozen v2 input/code differs: {relative}')


def start_test_run(root: Path,commit: str) -> None:
    """Create an exclusive one-shot marker before opening held-out rows; interrupted runs fail closed."""
    path=root/'data/review/detector_v2_test_started.json';path.parent.mkdir(parents=True,exist_ok=True)
    try:
        with path.open('x') as stream:json.dump({'freeze_commit':commit,'disclaimer':DISCLAIMER},stream,sort_keys=True);stream.write('\n')
    except FileExistsError as exc:raise ValueError('V2 test evaluation already started; only explicit frozen reproduction is allowed') from exc


def severity_cohort(items: list[dict],severity: int) -> list[dict]:
    """Include shared clean controls plus recordings whose eligible truths all have this strength.

    Mixed-strength recordings and synthetic files with no eligible truth are not
    silently assigned a strength. Clean controls appear in every severity cohort.
    """
    return [item for item in items if item['clean'] or
            item['truth'] and {t['severity'] for t in item['truth']}=={severity}]


def compute_test(root: Path,settings: dict) -> dict:
    """Load each test setting once; apply v1/v2 on identical tables, masks and severity cohorts."""
    from speecheval.calibration import comparison_items,evaluate_settings
    from speecheval.detector_v2 import recording_contrast
    from speecheval.tune_v2 import v2_metrics
    from speecheval.evaluate import detection_metrics,bootstrap_detection
    output={}
    v1=yaml.safe_load((root/'configs/detector.yaml').read_text())
    for setting in ('A-LOSO','B-same-speaker'):
        items=comparison_items(root,'test',setting)
        for item in items:item['contrast']=recording_contrast(root,item['recording_id'],item['table'],settings)
        old,old_items=evaluate_settings(items,v1);new,new_items=v2_metrics(items,settings)
        entry={'files':len(items),'recording_ids':[v['recording_id'] for v in items],
               'excluded_uncertain_truth':sum(v['excluded_uncertain_truth'] for v in items),
               'v1':{'metrics':old,'confidence_intervals':bootstrap_detection(old_items)},
               'v2':{'metrics':new,'confidence_intervals':bootstrap_detection(new_items)},'severity_cohorts':{}}
        for severity in range(1,6):
            old_cohort=severity_cohort(old_items,severity);new_cohort=severity_cohort(new_items,severity)
            if [v['recording_id'] for v in old_cohort]!=[v['recording_id'] for v in new_cohort]:raise ValueError('Severity cohort differs between detectors')
            entry['severity_cohorts'][str(severity)]={'files':len(old_cohort),
                'v1':{'metrics':detection_metrics(old_cohort),'confidence_intervals':bootstrap_detection(old_cohort)},
                'v2':{'metrics':detection_metrics(new_cohort),'confidence_intervals':bootstrap_detection(new_cohort)}}
        entry['severity_cohort_note']='Shared clean controls repeated; only homogeneous eligible truth strengths; mixed strengths excluded. Full-set recall_by_severity includes every eligible truth region instead.'
        output[setting]=entry
    return output


def preflight(root: Path) -> tuple[dict,dict]:
    """Check only dev/configuration before the first held-out access."""
    from speecheval.reproduce import file_sha
    from speecheval.calibration import implementation_identity
    audit=json.loads((root/'data/review/detector_v2_dev.json').read_text());validate_gate(audit)
    cfg=root/'configs/detector_v2.yaml'
    if file_sha(cfg)!=audit['selected_yaml_sha256']:raise ValueError('V2 configuration differs from DEV selection')
    settings=yaml.safe_load(cfg.read_text())
    if settings!=audit['selected_config']:raise ValueError('V2 parsed configuration differs from DEV history')
    verify_hashes(root,DEV_BASELINE_HASHES)
    if file_sha(root/'src/speecheval/detector_v2.py')!=audit['implementation']['detector_v2.py']:
        raise ValueError('V2 detector changed after DEV search')
    if implementation_identity(root)!=audit['inputs']['implementation']:raise ValueError('Frozen v1 implementation changed')
    verify_hashes(root,audit['inputs']['inputs'])
    return audit,settings


def evaluate_once(root: Path) -> dict:
    """Require a clean committed freeze, then consume the sole test-evaluation permission."""
    from speecheval.reproduce import file_sha,verify_released_frozen_inputs
    from speecheval.validation import first_difference
    audit,settings=preflight(root)
    dirty=subprocess.check_output(['git','status','--porcelain','--','src','configs','tests'],cwd=root,text=True)
    if dirty.strip():raise ValueError('Commit/freeze v2 implementation, tests and configuration before test')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    started=root/'data/review/detector_v2_test_started.json'
    if started.exists():raise ValueError('V2 test evaluation already started')
    start_test_run(root,commit)
    frozen=json.loads((root/'data/review/final_evaluation.json').read_text())
    exclusions=verify_released_frozen_inputs(root,frozen)
    result=compute_test(root,settings)
    for setting,entry in result.items():
        expected=frozen['settings'][setting]
        check={'files':entry['files'],'metrics':entry['v1']['metrics'],
               'confidence_intervals':entry['v1']['confidence_intervals'],
               'excluded_uncertain_truth':entry['excluded_uncertain_truth']}
        diff=first_difference(expected,check)
        if diff:raise ValueError(f'Frozen v1 comparison changed: {diff}')
    hashes={f'src/speecheval/{name}':file_sha(root/'src/speecheval'/name) for name in CODE}
    hashes.update({name:file_sha(root/name) for name in ('configs/detector_v2.yaml','configs/detector.yaml',
                  'configs/rubric.yaml','data/review/detector_v2_dev.json','data/review/final_evaluation.json')})
    payload={'schema':'post-hoc-v2-test/v1','disclaimer':DISCLAIMER,'freeze_commit':commit,
             'dev_selected_id':audit['selected_id'],'test_evaluation_count':1,'code_and_config_hashes':hashes,
             'licence_exempt_unused_inputs':exclusions,'settings':result}
    destination=root/'data/review/detector_v2_test.json'
    destination.write_text(json.dumps(payload,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return payload


def reproduce(root: Path) -> dict:
    """Recompute frozen v2 outputs; never tune, select or create a second test-evaluation marker."""
    from speecheval.reproduce import verify_released_frozen_inputs,file_sha
    from speecheval.validation import first_difference
    expected_path=root/'data/review/detector_v2_test.json';expected=json.loads(expected_path.read_text())
    verify_hashes(root,expected['code_and_config_hashes'])
    audit,settings=preflight(root)
    verify_released_frozen_inputs(root,json.loads((root/'data/review/final_evaluation.json').read_text()))
    actual={**expected,'settings':compute_test(root,settings)}
    diff=first_difference(expected,actual)
    if diff:raise ValueError(f'Frozen v2 reproduction differs: {diff}')
    output=root/'data/review/v2_reproduction';output.mkdir(parents=True,exist_ok=True)
    target=output/'test.json';target.write_text(json.dumps(actual,sort_keys=True,indent=2,allow_nan=False)+'\n')
    if file_sha(target)!=file_sha(expected_path):raise ValueError('V2 reproduced JSON bytes differ')
    print(f"FROZEN V2 REPRODUCED OK: SHA256 {file_sha(target)}",flush=True)
    return actual


def write_results(root: Path,payload: dict) -> None:
    """Append measured tables only to the authorised Phase11 report."""
    from speecheval.evaluate import FLAW_TYPES
    path=root/'reports/phase11_v2.md';body=path.read_text().split('\n## One-shot post-hoc v2 test results')[0]
    lines=['','## One-shot post-hoc v2 test results','',f"**{DISCLAIMER}.**",'',
           f"Frozen commit before test: `{payload['freeze_commit']}`. One decision-bearing test run; any later numerical runs are requested frozen reproductions, not additional tuning/evaluation decisions.",'']
    def n(value,digits=3):return 'N/A' if value is None else f'{value:.{digits}f}'
    def ci(values):return 'N/A' if values is None else f'[{values[0]:.3f}, {values[1]:.3f}]'
    for setting,entry in payload['settings'].items():
        lines.extend([f'### {setting}', '',f"Files: {entry['files']}; excluded uncertain truth: {entry['excluded_uncertain_truth']}.",'',
                      '| Type | Version | Precision | Recall | F1 [95% CI] | Onset ms | Offset ms | Clean/min | Severity rho |',
                      '|---|---|---:|---:|---|---:|---:|---:|---:|'])
        for kind in (*FLAW_TYPES,'overall'):
            for version in ('v1','v2'):
                m=entry[version]['metrics'][kind];c=entry[version]['confidence_intervals'][kind]['f1_95ci']
                lines.append(f"| {kind} | {'frozen v1' if version=='v1' else 'post-hoc v2'} | {n(m['precision'])} | {n(m['recall'])} | {n(m['f1'])} {ci(c)} | {n(m['onset_median_ms'],1)} | {n(m['offset_median_ms'],1)} | {n(m['false_alarms_per_minute'])} | {n(m['severity_spearman'],2)} |")
        lines.extend(['','### Same-file severity cohorts','',entry['severity_cohort_note'],'',
                      '| Severity | Type | v1 P | v2 P | v1 R | v2 R | v1 F1 | v2 F1 |',
                      '|---:|---|---:|---:|---:|---:|---:|---:|'])
        for severity,cohort in entry['severity_cohorts'].items():
            for kind in (*FLAW_TYPES,'overall'):
                a=cohort['v1']['metrics'][kind];b=cohort['v2']['metrics'][kind]
                lines.append(f"| {severity} | {kind} | {n(a['precision'])} | {n(b['precision'])} | {n(a['recall'])} | {n(b['recall'])} | {n(a['f1'])} | {n(b['f1'])} |")
        lines.extend(['','Full-set severity recall (all eligible truth regions, including mixed files):','',
                      '| Type | Version | S1 | S2 | S3 | S4 | S5 |','|---|---|---:|---:|---:|---:|---:|'])
        for kind in (*FLAW_TYPES,'overall'):
            for version in ('v1','v2'):
                recalls=entry[version]['metrics'][kind]['recall_by_severity']
                lines.append(f"| {kind} | {version} | "+' | '.join(n(recalls[str(s)]) for s in range(1,6))+' |')
    path.write_text(body+'\n'.join(lines)+'\n')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reproduce',action='store_true');args=parser.parse_args()
    root=Path.cwd()
    if args.reproduce:reproduce(root)
    else:
        result=evaluate_once(root);write_results(root,result)
        print(json.dumps({'freeze_commit':result['freeze_commit'],'disclaimer':DISCLAIMER,
              'overall':{k:{v:e[v]['metrics']['overall'] for v in ('v1','v2')} for k,e in result['settings'].items()}},indent=2))


if __name__=='__main__':main()
