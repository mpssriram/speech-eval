"""Render completed Phase 13 evidence only; never run a detector or change primary outputs."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path


def main() -> None:
    root=Path(__file__).resolve().parents[1];reports=root/'reports'
    runs={stage:json.loads((reports/f'phase13_{stage}.json').read_text()) for stage in ('dev','test','human')}
    protocol=(reports/'phase13_pause_floor.md').read_text().split('\n## Results')[0]
    lines=['## Results — post-hoc sensitivity check; test split previously seen with v1','',
        'Completed one DEV run (152 files), one TEST run (190 A-LOSO + 76 B-same-speaker files), and one genuine run (six distinct scored takes: six A comparisons and four B current-take comparisons). No floor search, threshold tuning, realignment or feature extraction. The same retained measurements/reference centres and localized labels were used. v1 stays primary; these comparisons do not replace any published v1 number.','',
        'Synthetic matching is exactly the frozen v1 evaluator: same type, greedy one-to-one IoU >=0.3 for non-pauses; for pause types, the existing centre-distance <=0.25 s eligibility rule is retained. Genuine matching is its original primary rule: same-type greedy one-to-one **strict IoU >=0.3 for every type**. Neither cohort’s policy was changed to imitate the other. Uncertain truth/prediction exclusions and clean-control/current-duration denominators are retained.','',
        'The synthetic v1 metrics and 95% recall/F1 intervals reproduced the stored Phase 6 JSON exactly. CIs for v1+floor use the same file-level bootstrap: 1,000 resamples, NumPy default_rng seed 20261001, percentile 2.5/97.5. This treats files as sampling units, as v1 did; edited files from the same speaker are correlated, so it is not a speaker-level generalization interval. Precision has no published v1 CI. Genuine v1 has no published CIs, so none are invented here.','',
        'Flags-by-type cells use the fixed order **R / D / Mo / Q / Mu / AP / MP** = rushing / dragging / monotone / too_quiet / mumbling / awkward_pause / missing_pause. Hit/miss/FP counts use the corresponding frozen matcher, not a new human judgement.','',
        '| Cohort | Version | Files / labels | Precision | Recall (95% CI where available) | F1 (95% CI where available) | Clean alarms/min | Hits / misses / FP | Flags by type: R/D/Mo/Q/Mu/AP/MP |',
        '|---|---|---:|---:|---|---|---:|---|---|']
    cohorts=[('TEST A-LOSO',runs['test']['settings']['A-LOSO']),
             ('TEST B-same-speaker',runs['test']['settings']['B-same-speaker']),
             ('Genuine A',runs['human']['settings']['A']),('Genuine B',runs['human']['settings']['B'])]
    fmt=lambda v:'N/A' if v is None else f'{v:.4f}'
    for title,entry in cohorts:
        for version in ('v1','v1+floor'):
            e=entry[version];m=e['metrics']['overall'];ci=e.get('confidence_intervals',{}).get('overall',{})
            ci_text=lambda key:'' if not ci.get(key) else f' [{ci[key][0]:.4f}, {ci[key][1]:.4f}]'
            lines.append(f'| {title} | {version} | {e["files"]} / {m["truth"]} | {fmt(m["precision"])} | {fmt(m["recall"])}{ci_text("recall_95ci")} | {fmt(m["f1"])}{ci_text("f1_95ci")} | {fmt(m["false_alarms_per_minute"])} | {m["hits"]} / {m["misses"]} / {m["false_positives"]} | '+ '/'.join(str(e['flags_by_type'][k]) for k in ('rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause'))+' |')
    a=runs['human']['settings']['A'];b=runs['human']['settings']['B']
    lines+=['',
        f'Genuine A clean alarms/min uses only the two declared natural take01 controls ({a["v1"]["clean_minutes"]:.6f} minutes). They are recorder-declared clean, not independently validated. Its all-six-take FP/min changes from {a["v1"]["false_positives_per_current_minute"]:.6f} to {a["v1+floor"]["false_positives_per_current_minute"]:.6f}, using {a["v1"]["current_minutes"]:.6f} current-take minutes. Genuine B has no clean current-take controls; clean alarms/min is N/A. Its FP/current-minute changes from {b["v1"]["false_positives_per_current_minute"]:.6f} to {b["v1+floor"]["false_positives_per_current_minute"]:.6f}, using {b["v1"]["current_minutes"]:.6f} minutes. Own take01 is used as B’s reference and its duration is not added. Take04s remain excluded.','',
        '### What changed','']
    changed_summary={}
    for title,entry in cohorts:
        removed=Counter();added=Counter();same_spans_evidence_changed=Counter()
        signature=lambda p:(p['type'],p['start'],p['end'],p['word_start'],p['word_end'])
        for item in entry['files']:
            old={signature(p):p for p in item['v1_regions']};new={signature(p):p for p in item['floor_regions']}
            removed.update(k[0] for k in old.keys()-new.keys());added.update(k[0] for k in new.keys()-old.keys())
            same_spans_evidence_changed.update(k[0] for k in old.keys()&new.keys() if old[k]!=new[k])
        new_hits=Counter(h['type'] for h in entry['new_hits']);lost=Counter(h['type'] for h in entry['lost_hits'])
        text=lambda counts:', '.join(f'{k}={v}' for k,v in sorted(counts.items())) or 'none'
        lines.append(f'- **{title}:** removed flags {text(removed)}; added flags {text(added)}. Retained spans with changed pause z/severity: {text(same_spans_evidence_changed)}. Newly matched labels: {text(new_hits)}; lost matched labels: {text(lost)}.')
        changed_summary[title]={'removed_flags':dict(removed),'added_flags':dict(added),
           'retained_spans_evidence_changed':dict(same_spans_evidence_changed),'newly_matched_types':dict(new_hits),'lost_matched_types':dict(lost)}
    lines+=['',
        '**No non-pause flaw becomes a hit.** Rushing, dragging, monotone, too_quiet and mumbling retain identical detected regions, evidence, severities and per-type matched labels in every file. Only awkward_pause and missing_pause evidence can change. In these completed runs, all removed detections are awkward_pause; missing_pause intervals/counts are unchanged, although their z/severity can decrease. The pause floor does not solve the genuine non-pause misses. It reduces some false alarms but sacrifices synthetic pause recall; it does not establish improved perceptual validity or justify replacing v1.','',
        '### DEV result and provenance','']
    dev=runs['dev']['settings']['A-LOSO']
    old=dev['v1']['metrics']['overall'];new=dev['v1+floor']['metrics']['overall']
    lines+=[f'DEV A-LOSO (the original calibration cohort): v1 P/R/F1 = {old["precision"]:.6f}/{old["recall"]:.6f}/{old["f1"]:.6f}, H/M/FP = {old["hits"]}/{old["misses"]}/{old["false_positives"]}; floor P/R/F1 = {new["precision"]:.6f}/{new["recall"]:.6f}/{new["f1"]:.6f}, H/M/FP = {new["hits"]}/{new["misses"]}/{new["false_positives"]}. Both have clean alarms/min {old["false_alarms_per_minute"]:.6f}. The unchanged floor was not selected or adjusted in response to DEV. Institutional JFK/Reagan B benchmark sources are TEST-only, so no invented DEV B benchmark is included.','',
        'Protocol was committed before implementation/results: `17a15e4`. Implementation and tests were committed before one-shot runs: `ae38269`. Eight new floor tests passed; the worktree suite passed **344 tests with 1 existing dataset-dependent skip**. Every eligible file also passes OFF table-byte identity and exact non-pause region identity. The primary code/config/reference/stored-analysis/report hash snapshot is verified before and after each run. Source feature provenance is checked; retained genuine producer artifacts are verified against their existing hashes without regenerating them in another runtime.','',
        'Machine-readable metrics, per-type results, all per-file predictions/matches, newly/lost matched labels and input hashes: `phase13_dev.json`, `phase13_test.json`, `phase13_human.json`. Exclusive `phase13_*_started.json` markers prevent a second run; no overwrite/retry flag is provided. Bootstrap resampling is performed on the single retained prediction sets, not repeated detector runs.','',
        'The flag belongs to the separate `speecheval.pause_floor` experimental path and `configs/pause_floor_sensitivity.yaml`. Missing/null/zero disables it. The primary `pipeline.py`, `detect.py`, `reference.py`, detector/rubric YAML and normal CLI are unchanged, so their default outputs and analysis identities remain byte-identical. No dashboard, Space, `web/`, `deploy/` or primary published v1 result is changed by this branch.','',
        'Commands used once from the experimental worktree (with the existing installed v1 environment/data):','',
        '```sh',
        'PYTHONPATH=$PWD/src /home/sriram/speech-eval/.venv/bin/python scripts/run_pause_floor_sensitivity.py dev --data-root /home/sriram/speech-eval',
        'PYTHONPATH=$PWD/src /home/sriram/speech-eval/.venv/bin/python scripts/run_pause_floor_sensitivity.py test --data-root /home/sriram/speech-eval',
        'PYTHONPATH=$PWD/src /home/sriram/speech-eval/.venv/bin/python scripts/run_pause_floor_sensitivity.py human --data-root /home/sriram/speech-eval',
        'python scripts/report_pause_floor_sensitivity.py',
        '```','',
        'These evaluation commands are recorded for provenance; existing one-shot markers intentionally reject reruns. The report renderer reads completed results only and can be rerun without evaluation. All work completed within the two-hour timebox.','']
    assert not any(h['type'] not in ('awkward_pause','missing_pause') for _,entry in cohorts for h in entry['new_hits'])
    assert all(c.get('missing_pause',0)==0 for d in changed_summary.values() for c in (d['removed_flags'],d['added_flags']))
    (reports/'phase13_pause_floor.md').write_text(protocol+'\n\n'+'\n'.join(lines))
    (reports/'phase13_changes.json').write_text(json.dumps(changed_summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps(changed_summary,indent=2))


if __name__=='__main__':main()
