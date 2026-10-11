"""Read-only DEV B investigation; no test rows, threshold selection, or corpus writes."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import numpy as np
import soundfile as sf
import yaml
from speecheval.reference import canonical_words, recording_values, map_words, mask_pause_evidence, summarize, FEATURES
from speecheval.detect import z_table, detect
from speecheval.calibration import exclude_uncertain_predictions
from speecheval.evaluate import match_regions, detection_metrics
from speecheval.inject import map_time

root = Path.cwd()
rows = [r for r in csv.DictReader((root/'data/manifest/dataset_index.csv').open()) if r['split']=='dev']
splits = yaml.safe_load((root/'configs/splits.yaml').read_text())
settings = yaml.safe_load((root/'configs/detector.yaml').read_text())
pool = json.loads((root/'data/reference/pooled_sigma.json').read_text())['sigma']
refs = {}
items = []
counts = Counter()
distances = defaultdict(list)
timing = defaultdict(list)
oracle_errors = []
oracle_large_errors = []
audio_checks = []
duplicates = 0
z_abs = defaultdict(list)
pause_diffs = []
fp_by_edit = Counter()
fp_on_unchanged_audio = Counter()
FP_rows = []

for r in rows:
    rid = r['recording_id']
    source_id = rid.rsplit('__',1)[0]+'__orig'
    assert source_id in splits['dev'] and source_id not in splits['test']
    if source_id not in refs:
        source, values = recording_values(root, source_id)
        words = canonical_words(root, r['text_id'])
        mapping = map_words([w['norm'] for w in source['words']], words)
        values = mask_pause_evidence(values, mapping)
        collected = {i:{f:[] for f in FEATURES} for i in range(len(words))}
        for j,i in enumerate(mapping):
            if i is not None:
                for f in FEATURES: collected[i][f].append(values[j][f])
        ref = {'words': words, 'features': {str(i):{f:summarize(v,pool[f]) for f,v in row.items()} for i,row in collected.items()}}
        refs[source_id] = (ref,source)
    ref, source = refs[source_id]
    alignment, values = recording_values(root,rid)
    table = z_table(alignment,values,ref,map_words([w['norm'] for w in alignment['words']],ref['words']))
    truth = json.loads((root/r['label_path']).read_text())['flaws'] if r['label_path'] else []
    uncertain = set(alignment.get('uncertain_words',[]))
    excluded = [f for f in truth if any(i in uncertain for i in range(f['word_start'],f['word_end']+1))]
    eligible = [f for f in truth if f not in excluded]
    pred = exclude_uncertain_predictions(detect(table,alignment['duration_s'],settings),excluded)
    pairs = match_regions(pred,eligible)
    matched = {p for p,t in pairs}
    items.append({'recording_id':rid,'truth':eligible,'predicted':pred,'duration_s':alignment['duration_s'],'clean':r['kind']=='source'})
    signatures = [(p['type'],p['start'],p['end'],p['word_start'],p['word_end']) for p in pred]
    duplicates += len(signatures)-len(set(signatures))
    for j,p in enumerate(pred):
        if j in matched: continue
        a,b = p['start'],p['end']
        if not truth: position,distance = 'clean',0.
        else:
            target = min(truth,key=lambda t:max(t['start']-b,a-t['end'],0.))
            if target['start']<=a and b<=target['end']: position,distance='inside',0.
            elif a<=target['end'] and b>=target['start']: position,distance='overlap',0.
            elif b<target['start']: position,distance='before',target['start']-b
            else: position,distance='after',a-target['end']
        counts[p['type'],position]+=1
        fp_by_edit[rid.rsplit('__',1)[-1].split('_s')[0],p['type']]+=1
        global_gain = truth[0]['parameters'].get('peak_normalised_db',0.) if truth else 0.
        if position in ('before','after') and global_gain==0:
            fp_on_unchanged_audio[p['type']]+=1
        distances[p['type'],position].append(distance)
        z_abs[p['type']].append(abs(p['evidence']['z']))
        if p['type'] in ('awkward_pause','missing_pause'):
            pause_diffs.append(abs(p['evidence']['participant']-p['evidence']['reference']))
        FP_rows.append((rid,p['type'],a,b,position,distance))
    if not truth: continue
    time_map = json.loads((root/'data/flawed/timemaps'/f'{rid}.json').read_text())['breakpoints']
    oracle = json.loads((root/'data/alignment/oracle'/f'{rid}.json').read_text())
    assert len(oracle['words'])==len(source['words'])==len(alignment['words'])
    for o,s in zip(oracle['words'],source['words']):
        errors = [abs(o['start']-map_time(s['start'],time_map)),abs(o['end']-map_time(s['end'],time_map,side='left'))]
        oracle_errors.extend(errors)
        if max(errors)>.01:
            oracle_large_errors.append({'id':rid,'word':s['i'],'source':[s['start'],s['end']],'oracle':[o['start'],o['end']], 'errors':errors,'map':time_map})
    for w,s in zip(alignment['words'],source['words']):
        expected = map_time(s['start'],time_map)
        if s['start']>time_map[-2][0]+.1:
            timing['after_edit_mapped'].append(abs(w['start']-expected))
            timing['after_edit_unmapped'].append(abs(w['start']-s['start']))
    dry,sr = sf.read(root/source['audio'],dtype='float64')
    wet,wet_sr = sf.read(root/alignment['audio'],dtype='float64')
    assert sr==wet_sr==44100
    prefix = max(0,int((time_map[1][0]-.1)*sr))
    suffix = max(0,min(len(dry),int((len(dry)/sr-time_map[-2][0]-.1)*sr)))
    # Mixed labels repeat the total global attenuation on EVERY flaw. Do not sum
    # that repeated recording-wide value (which would falsely triple the gain).
    gains = [t['parameters'].get('peak_normalised_db',0.) for t in truth]
    assert len(set(gains))==1
    adjustment = gains[0]
    gain=10**(adjustment/20)
    errors=[]
    if prefix: errors.append(float(np.max(abs(wet[:prefix]-dry[:prefix]*gain))))
    if suffix: errors.append(float(np.max(abs(wet[-suffix:]-dry[-suffix:]*gain))))
    audio_checks.append({'id':rid,'gain_db':adjustment,'outside_max_pcm_lsb':max(errors,default=0.)*32768,'map_duration_error_s':abs(time_map[-1][1]-len(wet)/sr)})

def quantiles(v):
    return dict(zip(('median','p95','max'),[float(x) for x in np.quantile(v,[.5,.95,1])])) if v else None

output={'split':'DEV only','setting':'B on the four DEV Gettysburg/O Captain speakers, each edited file versus its own original; NOT the published JFK/Reagan test cohort',
        'files':len(items),'metrics':{k:v for k,v in detection_metrics(items).items() if k!='confusion'},
        'false_positives':[{'type':k[0],'position':k[1],'count':n,'distance_s':quantiles(distances[k])} for k,n in sorted(counts.items())],
        'fp_abs_z':{k:quantiles(v) for k,v in sorted(z_abs.items())},'fp_pause_difference_s':quantiles(pause_diffs),
        'fp_by_injected_variant': [{'variant':key[0],'predicted_type':key[1],'count':n} for key,n in sorted(fp_by_edit.items())],
        'fp_before_after_zero_global_gain':dict(fp_on_unchanged_audio),
        'word_start_errors_s':{k:quantiles(v) for k,v in timing.items()},'oracle_mapped_edge_errors_s':quantiles(oracle_errors),
        'oracle_large_errors':oracle_large_errors,
        'exact_duplicate_predictions':duplicates,'gain_adjusted_files':sum(c['gain_db']!=0 for c in audio_checks),
        'outside_audio_error_pcm_lsb':quantiles([v['outside_max_pcm_lsb'] for v in audio_checks]),
        'outside_audio_more_than_2_lsb':[c for c in audio_checks if c['outside_max_pcm_lsb']>2],
        'map_duration_error_s':quantiles([v['map_duration_error_s'] for v in audio_checks]),
        'per_fp_rows_sha256':hashlib.sha256(json.dumps(FP_rows,sort_keys=True).encode()).hexdigest()}
print(json.dumps(output,indent=2))
if '--rows' in __import__('sys').argv:
    print('recording_id,type,start_s,end_s,position,distance_s')
    for row in FP_rows:
        print(','.join(str(v) for v in row))
