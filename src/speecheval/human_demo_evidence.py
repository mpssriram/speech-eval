"""Read-only diagnostics over frozen genuine results; never rerun or tune detectors."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
from speecheval.evaluate import match_regions
from speecheval.human_takes import digest

TYPES = ('rushing', 'dragging', 'monotone', 'too_quiet', 'mumbling',
         'awkward_pause', 'missing_pause')


def row_breakdown(row: dict) -> dict:
    """Count unmatched predictions under the already-published strict IoU rule."""
    flags = Counter(r['type'] for r in row['regions'])
    result = {'flags_by_type': {k: flags[k] for k in TYPES},
              'false_alarms_by_type': None, 'matched_pairs': [],
              'false_positive_indices': None, 'missing_pause_share': None,
              'rushing_share': None}
    if row['excluded_from_scoring']:
        return result
    intervals = lambda rows: [{**r, 'type': 'interval:' + r['type']} for r in rows]
    pairs = match_regions(intervals(row['regions']), intervals(row['intended_regions']), .3, .25)
    used = {p for p, _ in pairs}
    indices = [i for i in range(len(row['regions'])) if i not in used]
    counts = Counter(row['regions'][i]['type'] for i in indices)
    assert len(pairs) == row['comparison']['primary']['hits']
    assert len(indices) == row['comparison']['primary']['false_positives']
    result.update(false_alarms_by_type={k: counts[k] for k in TYPES},
                  matched_pairs=pairs, false_positive_indices=indices,
                  missing_pause_share=counts['missing_pause']/len(indices) if indices else None,
                  rushing_share=counts['rushing']/len(indices) if indices else None)
    return result


def pause_summary(alignment: dict, first: int, last: int) -> dict:
    """Seconds of positive inter-word MFA gaps in the selected same-text span."""
    words = alignment['words'][first:last+1]
    span = words[-1]['end'] - words[0]['start']
    pauses = sum(max(0., b['start']-a['end']) for a, b in zip(words, words[1:]))
    return {'aligned_span_s': span, 'interword_pause_s': pauses,
            'pause_fraction': pauses/span, 'word_count': len(words)}


def collect_evidence(root: Path) -> dict:
    """Read actual promoted reference readers and genuine jobs; preserve input bytes."""
    path = root/'data/human/evaluation.json'
    payload = json.loads(path.read_text())
    rows = [{k: r[k] for k in ('take_id','detector','mode','duration_s','excluded_from_scoring','job_id')}
            | row_breakdown(r) for r in payload['results'] if r['mode'] in ('A','B')]
    pools = []
    for detector in ('v1','v2'):
        for mode in ('A','B'):
            counts = Counter()
            for r in rows:
                if r['detector']==detector and r['mode']==mode and not r['excluded_from_scoring']:
                    counts.update(r['false_alarms_by_type'])
            total = sum(counts.values())
            pools.append({'detector':detector,'mode':mode,'false_positives':total,
                          'by_type':dict(counts), 'missing_pause_share':counts['missing_pause']/total,
                          'rushing_share':counts['rushing']/total,
                          'combined_share':(counts['missing_pause']+counts['rushing'])/total})
    references = {}; takes = []
    for text in ('gettysburg','reagan_challenger'):
        suffix = 'none' if text=='gettysburg' else 'reagan_challenger__reagan__orig'
        reference = json.loads((root/f'data/reference/{text}__excl-{suffix}.json').read_text())
        records = []
        for rid in reference['readers']:
            alignment = json.loads((root/f'data/alignment/{rid}.json').read_text())
            last = alignment['sentences'][16]['word_end'] if text=='reagan_challenger' else len(alignment['words'])-1
            if text=='reagan_challenger':
                assert alignment['words'][last]['norm']=='truths', 'Reference excerpt stop differs'
            records.append({'recording_id':rid,'prepared_duration_s':alignment['duration_s'],
                            'word_start':0,'word_end':last, **pause_summary(alignment,0,last)})
        references[text] = records
    for row in payload['results']:
        if row['detector']!='v1' or row['mode']!='A':
            continue
        alignment = json.loads((root/f'data/alignment/{row["recording_id"]}.json').read_text())
        takes.append({'take_id':row['take_id'],'duration_s':row['duration_s'],
                      **pause_summary(alignment,0,len(alignment['words'])-1)})
    return {'schema':'human-demo-evidence/v1','evaluation_sha256':digest(path),
            'matching':'same type, one-to-one strict IoU >=0.3; published pairs unchanged',
            'rows':rows,'pooled_false_alarms':pools,'reference_readers':references,
            'take_timings':takes,'detector_changes':False}


def breakdown_markdown(evidence: dict) -> str:
    """Render all seven supported types and explicit excluded-take flag counts."""
    lines = ['## False-alarm breakdown (primary IoU >=0.3)', '',
        'Counts below are unmatched predictions, not independently verified delivery errors. No unlabelled difference is reclassified as a hit. Unknown take04s show flags only, with no false-alarm claim.', '',
        '| Detector | Take | Mode | Rushing | Dragging | Monotone | Too quiet | Mumbling | Awkward pause | Missing pause | FP | Missing-pause share | Rushing share |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in evidence['rows']:
        counts = row['false_alarms_by_type'] if not row['excluded_from_scoring'] else row['flags_by_type']
        cells = ' | '.join(str(counts[k]) for k in TYPES)
        fp = str(sum(counts.values())) if not row['excluded_from_scoring'] else 'excluded; flags only'
        shares = ' | '.join('excluded' if row['excluded_from_scoring'] else
            ('n/a' if row[k] is None else f'{100*row[k]:.1f}%') for k in ('missing_pause_share','rushing_share'))
        lines.append(f'| {row["detector"]} | {row["take_id"]} | {row["mode"]} | {cells} | {fp} | {shares} |')
    lines += ['', 'Take01 rows give flags by type explicitly: all are unmatched because no delivery flaws were declared. Slips are not delivery labels.', '',
        '| Detector / mode | FP | Missing pause | Rushing | Combined share |', '|---|---:|---:|---:|---:|']
    for p in evidence['pooled_false_alarms']:
        lines.append(f'| {p["detector"]} / {p["mode"]} | {p["false_positives"]} | {p["by_type"]["missing_pause"]} ({100*p["missing_pause_share"]:.1f}%) | {p["by_type"]["rushing"]} ({100*p["rushing_share"]:.1f}%) | {100*p["combined_share"]:.1f}% |')
    lines += ['', '## Same-text reference duration and pause context', '',
        'Timing uses retained real MFA, not listening. Inter-word pause is the sum of positive gaps between consecutive aligned words; it is not a new detector feature. Compare the same excerpt, not the full 249.13 s Reagan speech.', '',
        '| Text | Reference readers | Prepared audio range (s) | Same-text aligned span range (s) | Inter-word pause range (s) |', '|---|---:|---:|---:|---:|']
    for text, records in evidence['reference_readers'].items():
        ranges = [f'{min(r[k] for r in records):.2f}-{max(r[k] for r in records):.2f}' for k in ('prepared_duration_s','aligned_span_s','interword_pause_s')]
        lines.append(f'| {text} | {len(records)} | '+ ' | '.join(ranges)+' |')
    lines += ['', '| Take | Prepared duration (s) | Same-text aligned span (s) | Inter-word pause (s) |', '|---|---:|---:|---:|']
    for r in evidence['take_timings']:
        lines.append(f'| {r["take_id"]} | {r["duration_s"]:.2f} | {r["aligned_span_s"]:.2f} | {r["interword_pause_s"]:.2f} |')
    lines += ['', 'Gettysburg reference readers are the ten actual Mode-A train readers, not all fifteen available readers. Reagan has one reference: its first 17 canonical units, ending “discover its truths.”, are compared with the recordings. Duration alone does not establish faster delivery in every sentence, and fewer total gap seconds does not mean every individual pause is shorter.', '',
        'Machine-readable full precision and reference IDs: `data/human/demo_evidence.json`. Frozen genuine evaluation JSON is unchanged.', '']
    return '\n'.join(lines)
