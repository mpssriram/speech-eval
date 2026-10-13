"""Explain retained genuine v1 evidence; no inference, scoring or threshold selection."""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from speecheval.detect import TYPES, z_table
from speecheval.reference import FEATURES, inverse, map_words, transform
from speecheval.human_demo_evidence import row_breakdown

ORDER=tuple(TYPES)+('awkward_pause','missing_pause')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stored_values(root: Path,rid: str,provenance: dict) -> tuple[dict,list[dict]]:
    """Read hash-verified retained artifacts without rerunning a producer in another runtime."""
    relative=f'data/alignment/{rid}.json'; alignment=json.loads((root/relative).read_text())
    required=[relative,alignment['audio']]+[f'data/features/{folder}/{rid}.parquet' for folder in ('words','windows')]
    states=[]
    for p in (root/'data/.cache/participants').glob('*/state.json'):
        saved=json.loads(p.read_text())
        if relative in saved.get('artifacts',{}):states.append((p,saved))
    if not states:raise ValueError(f'Missing retained hash provenance: {rid}')
    state,saved=next((p,s) for p,s in states if all(s['artifacts'].get(k)==digest(root/k) for k in required))
    provenance[str(state.relative_to(root))]=digest(state)
    provenance.update({k:digest(root/k) for k in required})
    tables={folder:pd.read_parquet(root/f'data/features/{folder}/{rid}.parquet').set_index('i') for folder in ('words','windows')}
    values=[{key:transform(key,float(tables[folder].loc[w['i'],column])) if w['i'] not in alignment.get('uncertain_words',[]) else np.nan
             for key,(folder,column) in FEATURES.items()} for w in alignment['words']]
    return alignment,values


def distribution(values: list[float]) -> dict:
    x=np.asarray(values,dtype=float);x=x[np.isfinite(x)]
    edges=[0.,1.,2.,3.5,10.,100.,1000.,10000.,float('inf')]
    counts=np.histogram(x,bins=edges)[0]
    return {'n':len(x),'min':float(np.min(x)),'p25':float(np.quantile(x,.25)),
            'median':float(np.median(x)),'p75':float(np.quantile(x,.75)),
            'p95':float(np.quantile(x,.95)),'max':float(np.max(x)),
            'histogram':{f'[{a:g}, {b:g})':int(c) for a,b,c in zip(edges,edges[1:],counts)}}


def main() -> None:
    root=Path.cwd();human=root/'data/human/evaluation.json'; original=digest(human)
    settings=yaml.safe_load((root/'configs/detector.yaml').read_text())
    assert all(settings['k'][k]==3.5 for k in ORDER)
    refs={json.loads(p.read_text()).get('reference_version'):p for p in (root/'data/reference').glob('*.json')}
    near=[];flags=[];samples=defaultdict(list);spreads=defaultdict(list);provenance={}
    for row in json.loads(human.read_text())['results']:
        if row['detector']!='v1' or row['mode'] not in ('A','B'):continue
        jobpath=root/f"data/app/jobs/{row['job_id']}.json";job=json.loads(jobpath.read_text());a=job['analysis']
        assert a['regions']==row['regions']
        assert a['detector']['config_hash']==digest(root/'configs/detector.yaml')
        refpath=refs[a['reference']['reference_version']];reference=json.loads(refpath.read_text())
        assert reference['reference_version']==a['reference']['reference_version']
        # These are actual input hashes of the retained reference, including prior take features.
        for rel,sha in reference['inputs']['inputs'].items():assert digest(root/rel)==sha,rel
        alignment,values=stored_values(root,row['recording_id'],provenance)
        table=z_table(alignment,values,reference,map_words([w['norm'] for w in alignment['words']],reference['words']))
        provenance[str(refpath.relative_to(root))]=digest(refpath)
        provenance[str(jobpath.relative_to(root))]=digest(jobpath)
        counts=Counter(p['type'] for p in a['regions'])
        flags.append({'take':row['take_id'],'mode':row['mode'],'excluded':row['excluded_from_scoring'],
                      'counts':{k:counts[k] for k in ORDER}})
        if row['excluded_from_scoring']:continue
        mode=row['mode']
        for p in a['regions']:
            group='pause flags' if p['type'] in ('awkward_pause','missing_pause') else 'non-pause flags'
            samples[(mode,group)].append(abs(p['evidence']['z']))
        for t in table:
            for feature,z in t['z'].items():
                group='pause feature (all words)' if feature=='pause' else 'non-pause features (all words)'
                samples[(mode,group)].append(abs(z))
                summary=reference['features'][str(t['ref_i'])][feature]
                spreads[(mode,feature)].append(summary['sigma'])
        matched={target:prediction for prediction,target in row_breakdown(row)['matched_pairs']}
        for index,label in enumerate(row['intended_regions']):
            kind=label['type'];feature,direction=TYPES.get(kind,('pause',1 if kind=='awkward_pause' else -1))
            candidates=[t for t in table if label['word_start']<=t['i']<=label['word_end'] and feature in t['z']]
            if feature=='pause':candidates=[t for t in candidates if t['i']==label['word_end']]
            evidence=[]
            for t in candidates:
                summary=reference['features'][str(t['ref_i'])][feature]
                evidence.append({'word_i':t['i'],'word':t['text'],'reference_i':t['ref_i'],
                    'participant':inverse(feature,t['values'][feature]),'reference':inverse(feature,t['reference'][feature]),
                    'participant_transformed':t['values'][feature],'reference_transformed':t['reference'][feature],
                    'sigma_transformed':summary['sigma'],'z':t['z'][feature],
                    'passes_signed_threshold':direction*t['z'][feature]>=3.5})
            peak=max(evidence,key=lambda e:direction*e['z']) if evidence else None
            near.append({'take':row['take_id'],'mode':mode,'type':kind,'canonical_unit':label['canonical_unit'],
                'label_interval_s':[label['start'],label['end']],'feature':feature,'threshold':3.5,'direction':direction,
                'representative':'strongest z in flaw direction within label; pause uses right-hand boundary word',
                'peak':peak,'finite_words':len(evidence),'threshold_words':sum(e['passes_signed_threshold'] for e in evidence),
                'z_median':float(np.median([e['z'] for e in evidence])) if evidence else None,
                'primary_hit':index in matched,'prediction_index':matched.get(index),'per_word_evidence':evidence})
    out={'schema':'human-near-miss-diagnosis/v1','human_evaluation_sha256':original,'inference_runs':0,
         'benchmark_test_evaluations':0,'threshold':3.5,'near_misses':near,'flags':flags,
         'distributions':[{'mode':m,'group':g,**distribution(v)} for (m,g),v in samples.items() if v],
         'reference_sigma':[{'mode':m,'feature':f,**distribution(v)} for (m,f),v in spreads.items()],
         'retained_provenance_sha256':provenance}
    assert digest(human)==original
    (root/'reports/phase10_human_near_misses.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    units={'rate':'syllables/s (log transformed)','pitchvar':'semitones (log +0.5)',
           'loud':'dB relative to speaker median','clarity':'high-band ratio dB','pause':'seconds (log +0.05)'}
    lines=['## Why mostly pause flags','',
        'Read-only diagnosis of frozen v1 genuine takes. No detector, threshold, score or feature changes; no new human inference or synthetic test benchmark evaluation. All recorder-confirmed declared flaws are listed below (26 A/B comparisons of 13 labels). Monotone and mumbling were declared in take03, not take02. G = Gettysburg, R = Reagan Challenger. Take04 has unknown labels and contributes only to the flags table, not the distributions or hit counts.','',
        '**Feature evidence and near misses.** A/B use ±3.5 SD. Rate is the 3-word-window syllable rate (one neighbour on either side, restricted to the sentence), pitchvar is window pitch standard deviation, loud is window mean intensity relative to the speaker median, and clarity is window mean high-band energy ratio. Mumbling evaluates clarity alone. Pause is the gap before the boundary word. z = (transformed measured value − reference centre) / shrunk reference sigma. Measured and reference values below are in physical units; z is calculated after the stated transform, rounded to the detector’s four significant digits. Each row shows the strongest z **in the flaw direction** within the exact declared span, plus median z and threshold-crossing word count. It does not represent a unit-averaged detector or imply a hit. Full per-word values and reference sigma are in `phase10_human_near_misses.json`.','',
        'Non-pause rules require at least 3 flagged words in a sentence with at most 1 intervening word; unmatched/invalid evidence breaks a run. Pause flags additionally require gap ≥0.45 s (awkward), or reference gap ≥0.3 s and participant gap ≤40% of reference (missing). Ordered containment suppression still applies. A hit below means the original frozen same-type, one-to-one strict IoU ≥0.3 pair; a flag elsewhere is not a labelled hit.','',
        '| Take | Mode | Unit / flaw | Feature (physical units) | Measured | Reference | z (strongest signed) | Median z | Threshold | Words crossing / finite | Primary hit |',
        '|---|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    short=lambda take:('G ' if take.startswith('gettysburg') else 'R ')+take.split('__')[-1]
    for n in near:
        p=n['peak'];fmt=lambda v:f'{v:.6g}' if v is not None else 'absent'
        lines.append(f'| {short(n["take"])} | {n["mode"]} | {n["canonical_unit"]} / {n["type"]} | {n["feature"]} ({units[n["feature"]]}) | {fmt(p["participant"] if p else None)} | {fmt(p["reference"] if p else None)} | {fmt(p["z"] if p else None)} | {fmt(n["z_median"])} | 3.5 | {n["threshold_words"]}/{n["finite_words"]} | {"yes" if n["primary_hit"] else "no"} |')
    lines+=['','**All stored flags by type per take.** Includes matched and unmatched flags; zeros are explicit.','',
        '| Take | Mode | Rushing | Dragging | Monotone | Too quiet | Mumbling | Awkward pause | Missing pause | Total |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for f in flags:
        lines.append(f'| {short(f["take"])}'+(' (unknown labels)' if f['excluded'] else '')+f' | {f["mode"]} | '+' | '.join(str(f['counts'][k]) for k in ORDER)+f' | {sum(f["counts"].values())} |')
    lines+=['','**Distribution of |z| on the scored takes.** A: six takes01–03. B: four current takes02–03 versus own take01. Pause flags use each retained region’s evidence z. Non-pause feature samples use every finite word × feature in rate/pitchvar/loud/clarity, including subthreshold values. These populations have different sampling units; repeated overlapping windows are correlated. All pause-feature and non-pause-flag distributions are also shown to make the distinction explicit.','',
        '| Mode | Population | n | Minimum | p25 | Median | p75 | p95 | Maximum |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for d in out['distributions']:
        lines.append(f'| {d["mode"]} | {d["group"]} | {d["n"]} | '+' | '.join(f'{d[k]:.5g}' for k in ('min','p25','median','p75','p95','max'))+' |')
    lines+=['','| Mode / population | Absolute z <1 | 1–<2 | 2–<3.5 | 3.5–<10 | 10–<100 | 100–<1000 | 1000–<10000 | ≥10000 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for d in out['distributions']:
        if d['group'] in ('pause flags','non-pause features (all words)'):
            lines.append(f'| {d["mode"]} / {d["group"]} | '+' | '.join(str(v) for v in d['histogram'].values())+' |')
    lines+=['','**Why pauses dominate.** The pooled training pause spread is near zero because most aligned word boundaries have no gap; its median robust spread is zero before the numerical safeguard. There is no substantive pause sigma floor in v1: `reference.py` has a generic numerical `SCALE_FLOOR = .001` in transformed units, but no pause-specific timing/noise floor. The pooled pause sigma is .001; shrinking toward it can make the per-boundary sigma even smaller. This is not literally a zero denominator. Tiny timing changes at low-spread boundaries can therefore produce very large z, while real monotone/mumbling/rate/volume edits may remain within their broader reference distributions or fail the region/localization gates. Some Mode-A boundaries have substantial reader spread, so not every pause has tiny sigma. The comparison is especially sensitive in B (one previous take) and Reagan A (one expert reader). No fix in v1.','',
        '| Mode | Reference feature sigma (transformed units; word-weighted) | n | Minimum | Median | p95 | Maximum |',
        '|---|---|---:|---:|---:|---:|---:|']
    for d in out['reference_sigma']:
        lines.append(f'| {d["mode"]} | {d["feature"]} | {d["n"]} | '+' | '.join(f'{d[k]:.6g}' for k in ('min','median','p95','max'))+' |')
    pause_examples=sorted([p for row in json.loads(human.read_text())['results'] if row['detector']=='v1' and row['mode'] in ('A','B') and not row['excluded_from_scoring']
        for p in row['regions'] if p['type']=='awkward_pause'],key=lambda p:abs(p['evidence']['participant']-p['evidence']['reference']))[:3]
    lines+=['','Smallest stored awkward-pause differences (still subject to the ≥0.45 s gate): '+
        '; '.join(f'{p["evidence"]["participant"]:.4g} s versus {p["evidence"]["reference"]:.4g} s, Δ={p["evidence"]["participant"]-p["evidence"]["reference"]:.4g} s, z={p["evidence"]["z"]:.5g}' for p in pause_examples)+'.','',
        'Reproduce this read-only analysis: `env -u PYTHONPATH .venv/bin/python scripts/diagnose_human_near_misses.py`. Stored artifact hashes are checked against the retained producer state; runtime/model-path identity is not re-executed or rewritten. Genuine evaluation bytes and primary pairs remain unchanged.','']
    coverage=json.loads((root/'reports/phase10_rule_coverage.json').read_text())
    lines+=['### DEV rule activation audit','',
        'No detector activation bug found; no post-hoc detector bug fix and **zero benchmark test reruns**. All seven A/B rules and all five supported C-lite rules fire in isolated feature probes using the unchanged configuration. The probes are fabricated feature evidence, separate from the real DEV audio runs below. A non-hit on one selected audio file does not mean the rule is disabled. C-lite intentionally does not implement mumbling or awkward_pause; its too_quiet rule measures final intensity drop, not general quietness. C retains its frozen feature threshold **2.0**, not A/B’s 3.5.','',
        'One preselected single-flaw synthetic DEV file per type was run once in each mode (7 files, 21 mode runs), using retained real alignment/features. A uses the train-reader distribution excluding the source speaker; B uses that DEV speaker’s original recording; C uses the retained train-only sentence norms. Selection was based on stored DEV examples and strongest injection severity (severity 4 trail shape for quietness, since C supports sentence-final drop); it is a diagnostic sample, not a new performance estimate. No new feature extraction or benchmark test evaluation.','',
        '| Injected flaw / recording | Severity | Mode | Target type supported | All fired types (counts) | Target type fires anywhere | Same-type IoU ≥0.3 hit |',
        '|---|---:|---|---|---|---|---|']
    for c in coverage['results']:
        fired=', '.join(f'{k} ({v})' for k,v in c['flags_by_type'].items()) or 'none'
        lines.append(f'| {c["recording_id"]} | {c["severity"]} | {c["mode"]} | {"yes" if c["supported"] else "unsupported"} | {fired} | {"yes" if c["target_type_fired"] else "no"} | {"yes" if c["strict_interval_hit_indices"] else "no"} |')
    lines+=['','Every A/B path calls the same `detect()` function. Its non-pause loop evaluates rate (positive rushing, negative dragging), pitchvar (negative monotone), loud (negative too_quiet), and clarity (negative mumbling); its boundary loop evaluates both pause types. C’s `sentence_regions()` evaluates rate both directions, pitchrange, final_drop and end_pause. The probes confirm all branches produce regions. DEV audio misses reflect measured evidence, threshold/region gates and word-versus-sentence aggregation, not disabled code. Full flags, references, activation probes and frozen hashes: `phase10_rule_coverage.json`. Reproduce DEV only: `env -u PYTHONPATH .venv/bin/python scripts/diagnose_rule_coverage.py`.','']
    report=root/'reports/phase10_human_takes.md';base=report.read_text().split('\n## Why mostly pause flags')[0]
    report.write_text(base.rstrip()+'\n\n'+'\n'.join(lines))
    print(json.dumps({'near_miss_rows':len(near),'flag_rows':len(flags),'distributions':out['distributions']},indent=2))


if __name__=='__main__':main()
