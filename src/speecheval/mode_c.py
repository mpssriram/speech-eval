"""Train-only sentence norms; general delivery checks without same-text reference."""
from __future__ import annotations
import hashlib
import json
import logging
import re
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

LOGGER=logging.getLogger(__name__)
FEATURES={'rate':('articulation_rate_syl_s',0.,'syllables/s'),
          'pitchrange':('f0_st_range',.5,'semitones'),
          'final_drop':('final_int_drop_db',None,'dB'),
          'end_pause':('pause_after_s',.05,'s')}
NUMBER_WORDS=set('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion trillion crore lakh'.split())
SUPPORTED={'rushing','dragging','monotone','too_quiet','missing_pause'}
NON_NOUNS=set('of the a an is are was were be been being and or but to for in on at with from as than who which that this these those more less another other'.split())


def analysis_identity(identity: dict,key_moments: list[dict]) -> str:
    """Content address all scored and heuristic evidence, not only sentence summaries."""
    return hashlib.sha256(json.dumps({'inputs':identity,'key_moments':key_moments},sort_keys=True).encode()).hexdigest()[:12]


def evaluation_sentence_mask(alignment: dict,sentences: list[dict]) -> set[int]:
    """Shared eligibility for truth, both detectors and clean denominators."""
    unknown={alignment['words'][i]['sentence'] for i in alignment.get('uncertain_words',[])}
    return {int(s['i']) for s in sentences if s['n_words']>=4 and not s.get('invalid_evidence',False) and s['i'] not in unknown}


def evaluation_pairs(alignment: dict,regions: list[dict],eligible: set[int],ignored: set[tuple] | None = None) -> set[tuple]:
    """Preserve false-positive types; only exclude unsupported or ineligible evidence."""
    pairs={(r['type'],alignment['words'][r['word_start']]['sentence']) for r in regions if r['type'] in SUPPORTED}
    return {pair for pair in pairs if pair[1] in eligible and pair not in (ignored or set())}


def validate_phase7_evidence(root: Path) -> dict:
    """Require matching genuine score audits, not merely filenames."""
    from speecheval.validation import scoring_freeze
    audits=[]
    for name,schema in (('severity_validation','severity_validation/v1'),('repro_validation','repro_validation/v1')):
        path=root/'data/review'/f'{name}.json'
        if not path.exists():raise ValueError('Missing Phase 7 evidence')
        audit=json.loads(path.read_text())
        if audit.get('schema')!=schema or not audit.get('freeze'):raise ValueError('Malformed Phase 7 evidence')
        audits.append(audit)
    current=scoring_freeze(root)
    if any(audit['freeze']!=current for audit in audits):raise ValueError('Stale Phase 7 evidence')
    return current


def norm_summary(values: list[float]) -> dict:
    """Median, 1.4826 MAD, percentiles and finite sample size in transformed feature units."""
    x=np.asarray(values,dtype=float);x=x[np.isfinite(x)]
    if not len(x):raise ValueError('No valid norm evidence')
    median=float(np.median(x))
    return {'median':median,'robust_sd':float(1.4826*np.median(np.abs(x-median))),
            'percentiles':{str(p):float(np.percentile(x,p)) for p in (5,25,50,75,95)},'n':len(x)}


def transformed(key: str,value: float) -> float:
    """Natural-log rate/range/pause; identity final drop, invalid evidence stays NaN."""
    offset=FEATURES[key][1]
    if not np.isfinite(value):return np.nan
    if offset is None:return float(value)
    return float(np.log(value+offset)) if value>=0 and value+offset>0 else np.nan


def physical(key: str,value: float) -> float:
    """Invert a norm transform for readable measurements and typical ranges."""
    offset=FEATURES[key][1]
    return value if offset is None else float(np.exp(value)-offset)


def number_spans(words: list[str]) -> list[tuple[int,int]]:
    """Heuristic figures: digits, multiword numbers, or a number followed by a non-function token."""
    clean=[re.sub(r'[^a-z]','',word.lower()) for word in words];result=[];i=0
    while i<len(words):
        if re.search(r'\d',words[i]):result.append((i,i));i+=1;continue
        if clean[i] not in NUMBER_WORDS:i+=1;continue
        end=i
        while end+1<len(words) and clean[end+1] in NUMBER_WORDS:end+=1
        noun_follows=end+1<len(words) and clean[end+1] not in NON_NOUNS and bool(clean[end+1])
        if end>i or noun_follows:result.append((i,end))
        i=end+1
    return result


def sentence_regions(sentences: list[dict], norms: dict, settings: dict) -> list[dict]:
    """Flag valid sentences against train-only norms; times in participant seconds."""
    regions=[]
    for number,sentence in enumerate(sentences):
        if sentence.get('invalid_evidence',False) or sentence['n_words']<4:continue
        for key,summary in norms['features'].items():
            if key=='end_pause' and number==len(sentences)-1:continue
            value=transformed(key,sentence[FEATURES[key][0]])
            if not np.isfinite(value) or summary['robust_sd']<=0:continue
            z=(value-summary['median'])/summary['robust_sd'];k=settings.get('mode_c',{}).get('k',{}).get(key,2.)
            kind=None
            if key=='rate' and abs(z)>=k:kind='rushing' if z>0 else 'dragging'
            elif key=='pitchrange' and z<=-k:kind='monotone'
            elif key=='final_drop' and z<=-k:kind='too_quiet'
            elif key=='end_pause' and z<=-k:kind='missing_pause'
            if kind is None:continue
            start,end=sentence['start'],sentence['end'];first,last=sentence['word_start'],sentence['word_end']
            if key=='final_drop':first=max(first,last-1)
            if key=='end_pause':start=max(0.,end-.015);end+=.015
            severity=int(np.clip(np.searchsorted(settings['severity_z_bins'],abs(z),side='right'),1,5))
            p25=physical(key,summary['percentiles']['25']);p75=physical(key,summary['percentiles']['75']);participant=physical(key,value)
            regions.append({'type':kind,'start':round(float(start),3),'end':round(float(end),3),
                            'word_start':int(first),'word_end':int(last),'severity':severity,'mean_abs_z':float(f'{abs(z):.4g}'),
                            'sentence':int(sentence['i']),'evidence':{'feature':key,'participant':float(f'{participant:.4g}'),
                            'reference':float(f"{physical(key,summary['median']):.4g}"),'unit':FEATURES[key][2],'z':float(f'{z:.4g}')},
                            'tags':[],'explanation':f'{start:.1f}–{end:.1f} s: {kind.replace("_"," ")}; {key} {participant:.2g} {FEATURES[key][2]} versus good speakers in our dataset (typical range {p25:.2g}–{p75:.2g}); z={z:.2g}.'})
    return sorted(regions,key=lambda r:(r['start'],r['type']))


def build_norms(root: Path | None = None) -> dict:
    """Build four sentence norms from clean TRAIN sources only, masking uncertain aggregates."""
    from speecheval.reference import validate_measurement_provenance
    from speecheval.verify import _write_json
    root=root or Path.cwd();splits=yaml.safe_load((root/'configs/splits.yaml').read_text());values={key:[] for key in FEATURES};speakers={};inputs={}
    for rid in sorted(splits['train']):
        validate_measurement_provenance(root,rid)
        path=root/'data/features/sentences'/f'{rid}.parquet';inputs[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
        table=pd.read_parquet(path);speaker=rid.split('__')[1];rates=[]
        for number,sentence in enumerate(table.to_dict('records')):
            if sentence.get('invalid_evidence',False) or sentence['n_words']<4:continue
            for key,(column,_,_) in FEATURES.items():
                if key=='end_pause' and number==len(table)-1:continue
                value=transformed(key,sentence[column])
                if np.isfinite(value):values[key].append(value)
                if key=='rate' and np.isfinite(value):rates.append(value)
        if rates:speakers[speaker]=float(np.median(rates))
    inputs['configs/splits.yaml']=hashlib.sha256((root/'configs/splits.yaml').read_bytes()).hexdigest()
    identity={'inputs':inputs,'code':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result={'schema':'norms/v1','source':'clean train sentences >=4 words','readers':sorted(splits['train']),
            'features':{key:norm_summary(v) for key,v in values.items() if v},'speaker_rate_medians_log':speakers,
            'inputs':identity,'reference_version':hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest(),
            'limitations':['Sentence-level, weaker than same-text comparison. Zero-spread features are not scored.']}
    _write_json(root/'data/reference/norms_v1.json',result);return result


def key_checks(alignment: dict,sentences: list[dict],word_table: pd.DataFrame,norms: dict,settings: dict) -> list[dict]:
    """Delivery guidelines for numbers/opening/ending; never statistical flaws or score penalties."""
    from speecheval.features import window_rate
    words=alignment['words'];unknown=set(alignment.get('uncertain_words',[]));config=settings.get('key_moments',{})
    valid=[s['articulation_rate_syl_s'] for s in sentences if not s.get('invalid_evidence',False) and np.isfinite(s['articulation_rate_syl_s'])]
    own_median=float(np.median(valid)) if valid else np.nan;items=[]
    for first,last in number_spans([w['text'] for w in words]):
        a=max(0,first-1);b=min(len(words)-1,last+1)
        if any(i in unknown for i in range(a,b+1)):continue
        quote=' '.join(w['text'] for w in words[first:last+1]);local=word_table[(word_table.i>=a)&(word_table.i<=b)]
        rate=window_rate(local,.25);pause=float(word_table.iloc[first]['pause_before_s'])
        if np.isfinite(rate) and np.isfinite(own_median):items.append({'kind':'number_rate','start':words[first]['start'],'end':words[last]['end'],'words':quote,
            'passed':bool(rate<=own_median*config.get('number_rate_multiplier',1.)),
            'message':f'guideline: key figure "{quote}" at {rate:.2g} vs own median {own_median:.2g} syllables/s.'})
        if first>0 and first-1 in unknown:continue
        if np.isfinite(pause):items.append({'kind':'number_pause','start':words[first]['start'],'end':words[last]['end'],'words':quote,
            'passed':bool(pause>=config.get('number_pause_min_s',.15)),
            'message':f'guideline: pause before "{quote}" is {pause:.2g} s (target ≥{config.get("number_pause_min_s",.15):.2g} s).'})
    if sentences:
        final=sentences[-1];span=alignment['sentences'][-1]
        if not final.get('invalid_evidence',False):
            rate=transformed('rate',final['articulation_rate_syl_s']);summary=norms['features'].get('rate')
            z=(rate-summary['median'])/summary['robust_sd'] if summary and summary['robust_sd']>0 else np.nan
            drop=final['final_int_drop_db']
            if np.isfinite(z) and np.isfinite(drop):items.append({'kind':'strong_ending','start':span['start'],'end':span['end'],
                'words':' '.join(w['text'] for w in words[span['word_start']:span['word_end']+1]),
                'passed':bool(drop>=config.get('final_drop_min_db',-3.) and z<=config.get('final_rate_max_z',1.)),
                'message':f'guideline: final sentence drop {drop:.2g} dB and rate z={z:.2g}; targets ≥−3 dB and z≤1.'})
        first=alignment['sentences'][0]
        items.append({'kind':'first_sentence','start':first['start'],'end':first['end'],
                      'words':' '.join(w['text'] for w in words[first['word_start']:first['word_end']+1]),
                      'passed':None,'message':'guideline: opening sentence identified; no additional numerical rule or penalty.'})
    return items


def analyze_mode_c(audio: Path,text_id: str,transcript: Path | None = None,root: Path | None = None,norms: dict | None = None) -> dict:
    """General transcript/audio delivery evaluation; no same-text reference is consumed."""
    from decimal import Decimal
    from speecheval.pipeline import prepare_participant,rounded
    from speecheval.reference import recording_values
    from speecheval.score import rubric_scores
    from speecheval.verify import _write_json
    root=root or Path.cwd();rid,source=prepare_participant(audio.resolve(),text_id,root,transcript)
    alignment,_=recording_values(root,rid);norms=norms or build_norms(root)
    path=root/'configs/detector.yaml';settings=yaml.safe_load(path.read_text());rubric_path=root/'configs/rubric.yaml'
    table=pd.read_parquet(root/'data/features/sentences'/f'{rid}.parquet');sentences=table.to_dict('records')
    for sentence,span in zip(sentences,alignment['sentences']):sentence.update(word_start=span['word_start'],word_end=span['word_end'])
    regions=sentence_regions(sentences,norms,settings);words=alignment['words']
    for region in regions:
        if region['type']=='too_quiet':region['start']=words[region['word_start']]['start']
        if region['type']=='missing_pause':
            sentence=next(s for s in alignment['sentences'] if s['i']==region['sentence'])
            boundary=sentence['end'];region.update(start=max(0.,round(boundary-.015,3)),end=min(alignment['duration_s'],round(boundary+.015,3)),
                word_start=sentence['word_end'],word_end=min(len(words)-1,sentence['word_end']+1))
        region['tags']=['sentence_final'] if region['type'] in ('too_quiet','missing_pause') else []
        quote=' '.join(w['text'] for w in words[region['word_start']:region['word_end']+1])
        region['explanation']=f'{region["start"]:.1f}–{region["end"]:.1f} s, "{quote}": '+region['explanation'].split(' s: ',1)[-1]
    key_moments=key_checks(alignment,sentences,pd.read_parquet(root/'data/features/words'/f'{rid}.parquet'),norms,settings)
    config_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    identity={'audio':hashlib.sha256(audio.read_bytes()).hexdigest(),'alignment':alignment,'sentence_features':rounded(sentences),
              'norms':norms['reference_version'],'config':config_hash,'rubric':hashlib.sha256(rubric_path.read_bytes()).hexdigest(),
              'mode_c_code':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'score_code':hashlib.sha256(Path(__file__).with_name('score.py').read_bytes()).hexdigest()}
    analysis_id=analysis_identity(identity,key_moments)
    duration=Decimal(str(words[-1]['end']))-Decimal(str(words[0]['start']))
    result={'schema':'analysis/v1','analysis_id':analysis_id,'recording_id':rid,'text_id':text_id,'mode':'C',
            'reference':{'kind':'norms','reference_version':norms['reference_version'],'n_readers':len(norms['readers']),'baseline_recording_id':None},
            'transcript_source':'asr' if source=='automatic_as_read' else source,
            'detector':{'engine':'rules','config_hash':config_hash},'duration_s':alignment['duration_s'],
            'regions':regions,'key_moments':key_moments,'scores':rubric_scores(regions,duration,yaml.safe_load(rubric_path.read_text())),
            'progress':None,'warnings':alignment['warnings']+[{'type':'limited_sentence_norms_mode'}]}
    _write_json(root/'data/analyses'/f'{analysis_id}.json',result);return result


def sentence_metrics(items: list[dict]) -> dict:
    """One-to-one type/sentence set matching; duplicate flags cannot inflate recall."""
    result={}
    for kind in ('rushing','dragging','monotone','too_quiet','missing_pause','overall'):
        truth=predicted=matched=clean_predictions=0;clean_minutes=0.
        for item in items:
            t={pair for pair in item['truth'] if kind=='overall' or pair[0]==kind}
            p={pair for pair in item['predicted'] if kind=='overall' or pair[0]==kind}
            truth+=len(t);predicted+=len(p);matched+=len(t&p)
            if item['clean']:clean_predictions+=len(p);clean_minutes+=item['duration_s']/60
        result[kind]={'truth':truth,'predicted':predicted,'matched':matched,
                      'precision':matched/predicted if predicted else (0. if truth else None),
                      'recall':matched/truth if truth else None,'f1':2*matched/(truth+predicted) if truth+predicted else None,
                      'clean_alarms_per_minute':clean_predictions/clean_minutes if clean_minutes else None}
    return result


def evaluate_mode_c(root: Path | None = None) -> dict:
    """Cost of no same-text reference on the identical eligible test files/types; no threshold tuning."""
    import csv
    from speecheval.validation import test_analysis
    from speecheval.reference import recording_values
    from speecheval.verify import _write_json
    root=root or Path.cwd()
    freeze=validate_phase7_evidence(root)
    norms=build_norms(root);eligible=SUPPORTED
    mode_c_items=[];reference_items=[]
    rows=[r for r in csv.DictReader((root/'data/manifest/dataset_index.csv').open()) if r['split']=='test']
    for row in rows:
        alignment,_=recording_values(root,row['recording_id']);unknown=set(alignment.get('uncertain_words',[]))
        sentence_rows=pd.read_parquet(root/'data/features/sentences'/f"{row['recording_id']}.parquet").to_dict('records')
        valid_sentences=evaluation_sentence_mask(alignment,sentence_rows)
        all_labels=json.loads((root/row['label_path']).read_text())['flaws'] if row['label_path'] else []
        ignored={(f['type'],alignment['words'][f['word_start']]['sentence']) for f in all_labels
                 if f['type']=='too_quiet' and f.get('parameters',{}).get('shape')!='trail'}
        labels=all_labels
        labels=[f for f in labels if f['type'] in eligible and
                (f['type']!='too_quiet' or f.get('parameters',{}).get('shape')=='trail') and
                not any(i in unknown for i in range(f['word_start'],f['word_end']+1))]
        # Include clean sources; omit single flaws Mode C does not support.
        if row['kind']=='synthetic' and not labels:continue
        def pairs(regions):
            return evaluation_pairs(alignment,regions,valid_sentences,ignored)
        truth=pairs(labels)
        general=analyze_mode_c(root/row['audio_path'],row['text_id'],root=root,norms=norms)
        reference=test_analysis(root,row)
        evaluated_duration=sum(s['end']-s['start'] for s in sentence_rows if s['i'] in valid_sentences)
        shared={'recording_id':row['recording_id'],'truth':truth,'clean':row['kind']=='source','duration_s':evaluated_duration}
        mode_c_items.append({**shared,'predicted':pairs(general['regions'])})
        reference_items.append({**shared,'predicted':pairs(reference['regions'])})
        LOGGER.info('Mode C comparison %d/%d: %s',len(mode_c_items),len(rows),row['recording_id'])
    result={'schema':'mode_c_evaluation/v1','files':len(mode_c_items),'granularity':'type/sentence; at most one per type per sentence',
            'mode_C':sentence_metrics(mode_c_items),'reference_informed':sentence_metrics(reference_items),
            'reference_setting':'A-LOSO Gettysburg/O Captain; B-same-speaker JFK/Reagan',
            'norms_version':norms['reference_version'],'freeze':freeze,'human_takes':'PENDING actual recordings',
            'between_speaker_rate_syl_s':{speaker:float(np.exp(value)) for speaker,value in norms['speaker_rate_medians_log'].items()}}
    _write_json(root/'data/review/mode_c_evaluation.json',result);write_mode_c_report(root,result,norms)
    return result


def write_mode_c_report(root: Path,result: dict,norms: dict) -> None:
    """Write measured reference-vs-norm costs without claiming missing human/pitch evidence."""
    def n(value):return 'N/A' if value is None else f'{value:.3f}'
    lines=['# Phase 8 Mode C-lite results','',
           f"Files: {result['files']}; norms version `{result['norms_version']}`; built from clean TRAIN sources only.",'',
           'Mode C is weaker and more general than same-text comparison. Four sentence features are checked: rate, pitch range, sentence-final loudness drop, and non-final sentence-end pause. No mumbling or awkward-pause detector is offered in Mode C. Zero-spread norm features are not scored.','',
           f"Comparison setting: {result['reference_setting']}. Matching uses the same type/sentence granularity for both systems, not Phase 6 word-level boundaries. Too-quiet truth is trail-only; unsupported single-effect files are omitted. In mixed files only supported types are scored.",'',
           '| Type | C precision | C recall | Reference precision | Reference recall | C clean alarms/min | Reference clean alarms/min |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for kind,m in result['mode_C'].items():
        ref=result['reference_informed'][kind]
        lines.append(f"| {kind} | {n(m['precision'])} | {n(m['recall'])} | {n(ref['precision'])} | {n(ref['recall'])} | {n(m['clean_alarms_per_minute'])} | {n(ref['clean_alarms_per_minute'])} |")
    lines.extend(['',f"Measured aggregate recall: reference {n(result['reference_informed']['overall']['recall'])}, Mode C {n(result['mode_C']['overall']['recall'])}. This comparison describes controlled synthetic changes, not human performance.",'',
                  '## Between-speaker spread','', '| Train speaker | Median sentence rate (syllables/s) |','|---|---:|'])
    for speaker,value in sorted(result['between_speaker_rate_syl_s'].items()):lines.append(f'| {speaker} | {value:.3f} |')
    lines.extend(['','## Guidelines and limitations','',
                  'Number checks use a lexical heuristic: digits always count; number words count when multiword or followed by a non-function token (a noun/unit proxy, not a POS model). “one of the” is excluded. Number-rate ≤ own median, preceding pause ≥0.15 s, ending drop ≥−3 dB and ending rate z≤1 are configurable guidelines only and never alter scores. Opening sentences are identified without a separate penalty.',
                  'Actual user takes, independent listening labels, and pitch-rehearsal progress are PENDING. ASR-only inputs use configured fixed-beam CUDA ASR where available under the user’s GPU preference, with deterministic CPU MFA and feature extraction. Automatic transcripts are explicitly unreviewed.',''])
    (root/'reports/phase08_mode_c.md').write_text('\n'.join(lines),encoding='utf-8')
