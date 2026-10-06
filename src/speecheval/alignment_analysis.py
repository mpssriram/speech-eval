"""Paired diagnostic statistics for a small, visually annotated reference."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import cmudict
import numpy as np
from speecheval.transcripts import normalize_tokens
from speecheval.evaluate import error_metrics


def custom_acceptable(before: dict, after: dict) -> bool:
    """Adopt only with zero OOV and non-worse mean/median error for all edge groups."""
    return after['oov_words']==0 and all(after[e][k]<=before[e][k]+1e-8
        for e in ('start','end','overall') for k in ('median_ms','mean_ms'))


def signed_summary(starts: list[float], ends: list[float]) -> dict:
    """Signed aligner-minus-gold biases and absolute residuals in milliseconds."""
    s,t=np.asarray(starts),np.asarray(ends)
    if not len(s) or len(s)!=len(t):raise ValueError('Missing paired edges')
    result={edge:{'mean_ms':round(float(v.mean()*1000),3),
                  'median_ms':round(float(np.median(v)*1000),3)} for edge,v in [('start',s),('end',t)]}
    result['bias_corrected_pooled']=error_metrics(np.concatenate([s-np.median(s),t-np.median(t)]).tolist())
    return result


def paired_bootstrap(pairs: list[dict], seed: int, resamples: int) -> dict:
    """Stratified paired-word percentile CIs, milliseconds; keep both edges together."""
    if not pairs or resamples<1:raise ValueError('Missing bootstrap data')
    rng=np.random.default_rng(seed)
    groups={rid:[i for i,p in enumerate(pairs) if p['recording_id']==rid] for rid in sorted({p['recording_id'] for p in pairs})}
    indices=np.concatenate([rng.choice(g,(resamples,len(g)),replace=True) for g in groups.values()],axis=1)
    result={}
    for edge in ('start','end','pooled'):
        edges=('start','end') if edge=='pooled' else (edge,)
        m=np.array([[abs(p['mfa_'+e])*1000 for e in edges] for p in pairs])
        w=np.array([[abs(p['whisperx_'+e])*1000 for e in edges] for p in pairs])
        bm=m[indices].reshape(resamples,-1);bw=w[indices].reshape(resamples,-1)
        mean_ci=np.percentile(bm.mean(axis=1)-bw.mean(axis=1),[2.5,97.5])
        med_ci=np.percentile(np.median(bm,axis=1)-np.median(bw,axis=1),[2.5,97.5])
        result[edge]={'mean_difference_ms':round(float(m.mean()-w.mean()),3),
                      'mean_ci95_ms':np.round(mean_ci,3).tolist(),
                      'median_difference_ms':round(float(np.median(m)-np.median(w)),3),
                      'median_ci95_ms':np.round(med_ci,3).tolist()}
    return result


def initial_class(word: str, lexicon: dict) -> str:
    """Classify /p b t d k g/ lexical word onsets, not orthographic initials."""
    tokens=normalize_tokens(word)
    pronunciations=lexicon.get(tokens[0],[]) if tokens else []
    if not pronunciations:return 'unknown'
    classes={'stop' if p[0].rstrip('012') in {'P','B','T','D','K','G'} else 'other' for p in pronunciations if p}
    return classes.pop() if len(classes)==1 else 'unknown'


def annotate_audit(root: Path, audit: dict, seed: int = 20261007, resamples: int = 10000) -> None:
    """Add signed, paired, recording/onset and explicit coverage evidence to an audit."""
    lexicon=cmudict.dict();lookup={};stats={};onsets={};recording_stats={}
    for d in audit['details']:
        key=(d['recording_id'],d['original_word_index'])
        if (d['aligner'],key) in lookup:raise ValueError('Duplicate scored word')
        lookup[d['aligner'],key]=d
        d['initial_class']=initial_class(d['word'],lexicon)
    mkeys={k for name,k in lookup if name=='mfa'};wkeys={k for name,k in lookup if name=='whisperx'}
    if mkeys!=wkeys:raise ValueError('Aligners must score identical paired words')
    pairs=[]
    for key in sorted(mkeys):
        p={'recording_id':key[0]}
        for name in ('mfa','whisperx'):
            d=lookup[name,key]
            for edge in ('start','end'):p[name+'_'+edge]=d['predicted_'+edge]-d['gold_'+edge]
        pairs.append(p)
    for name in ('mfa','whisperx'):
        rows=[d for d in audit['details'] if d['aligner']==name]
        signed={edge:[d['predicted_'+edge]-d['gold_'+edge] for d in rows] for edge in ('start','end')}
        stats[name]=signed_summary(signed['start'],signed['end'])
        recording_stats[name]={}
        for rid in sorted({d['recording_id'] for d in rows}):
            subset=[d for d in rows if d['recording_id']==rid]
            recording_stats[name][rid]={'words':len(subset),**{e:error_metrics([d['predicted_'+e]-d['gold_'+e] for d in subset]) for e in ('start','end')}}
        onsets[name]={c:{'words':len(subset),'start':error_metrics([d['predicted_start']-d['gold_start'] for d in subset]) if subset else None}
                      for c in ('stop','other','unknown') for subset in [[d for d in rows if d['initial_class']==c]]}
        corpus_words=gold_oov=gold_interpolated=0;unique=set()
        for row in csv.DictReader((root/'data/manifest/recordings.csv').open()):
            payload=json.loads((root/'data/alignment'/name/f"{row['recording_id']}.json").read_text())
            oovs={w['text'] for w in payload['warnings'] if w['type']=='oov'};unique.update(oovs)
            interpolated={w['word'] for w in payload['warnings'] if w['type']=='interpolated'}
            corpus_words+=len(payload['words'])
            for d in [d for d in rows if d['recording_id']==row['recording_id']]:
                gold_oov+=any(set(payload['words'][i]['norm'].split()) & oovs for i in d['current_indices'])
                gold_interpolated+=bool(set(d['current_indices']) & interpolated)
        audit['evidence'][name].update(corpus_words=corpus_words,gold_oov_words=gold_oov,gold_interpolated_words=gold_interpolated,unique_oov=sorted(unique))
    baseline=root/'data/review/before_custom_dictionary/alignment_bakeoff.json'
    original=json.loads(baseline.read_text()) if baseline.exists() else audit
    gold_tokens={t for d in original['details'] if d['aligner']=='mfa' for t in normalize_tokens(d['word'])}
    oov_list=original.get('evidence',{}).get('mfa',{}).get('unique_oov',[])
    audit['analysis']={'seed':seed,'resamples':resamples,'signed':stats,'bootstrap':paired_bootstrap(pairs,seed,resamples),
                       'per_recording':recording_stats,'onsets':onsets,
                       'baseline_oov':[{'word':w,'in_scored_words':w in gold_tokens} for w in oov_list]}
    if baseline.exists():
        audit['analysis']['before_custom']={name:original['evidence'][name] for name in ('mfa','whisperx')}


def report_lines(audit: dict) -> list[str]:
    """Markdown diagnostics in ms; bias removal is not a timing correction."""
    a=audit['analysis'];lines=['','## Signed errors and in-sample bias diagnostic','',
        'Positive means the aligner boundary is later than gold. Subtract the median signed START bias from starts and END bias from ends, then pool absolute residuals. This is an in-sample descriptive diagnostic, not validated calibration; stored boundaries are NOT shifted.',
        '', '| Aligner | Start signed mean / median ms | End signed mean / median ms | Bias-corrected pooled median / mean ms |', '|---|---:|---:|---:|']
    for name,s in a['signed'].items():
        lines.append(f"| {name} | {s['start']['mean_ms']} / {s['start']['median_ms']} | {s['end']['mean_ms']} / {s['end']['median_ms']} | {s['bias_corrected_pooled']['median_ms']} / {s['bias_corrected_pooled']['mean_ms']} |")
    lines.extend(['','## Paired bootstrap MFA minus WhisperX','',
        f"{a['resamples']:,} resamples; NumPy PCG64 seed {a['seed']}. Resample paired WORDS within each recording, maintaining 15/15/7 words and both edges together. Percentile 95% CIs use raw absolute error; negative favors MFA. Both mean (MAE) and median differences are shown. These conditional CIs do not account for annotation error or generalize over independent readers (only three selected recordings).",'',
        '| Edge | MAE difference ms | 95% CI ms | Median difference ms | 95% CI ms |','|---|---:|---|---:|---|'])
    for edge,s in a['bootstrap'].items():lines.append(f"| {edge} | {s['mean_difference_ms']} | {s['mean_ci95_ms']} | {s['median_difference_ms']} | {s['median_ci95_ms']} |")
    lines.extend(['','## Per-recording gold errors','', '| Aligner | Recording | Words | Start median / mean ms | End median / mean ms |','|---|---|---:|---:|---:|'])
    for name,recordings in a['per_recording'].items():
        for rid,s in recordings.items():lines.append(f"| {name} | {rid} | {s['words']} | {s['start']['median_ms']} / {s['start']['mean_ms']} | {s['end']['median_ms']} / {s['end']['mean_ms']} |")
    lines.extend(['','## Stop-initial versus other starts','',
        'Lexical first phoneme from CMUdict: stops = P/B/T/D/K/G; affricates CH/JH are other. Normalize numbers and use the first word of expansions. Missing or mixed-onset pronunciations are unknown, never silently assigned. This is lexical grouping, not an acoustic onset classification.', '',
        '| Aligner | Initial class | Words | Start median / mean ms |','|---|---|---:|---:|'])
    for name,classes in a['onsets'].items():
        for c,s in classes.items():lines.append(f"| {name} | {c} | {s['words']} | {str(s['start']['median_ms'])+' / '+str(s['start']['mean_ms']) if s['start'] else 'N/A'} |")
    lines.extend(['','## Corpus coverage (not gold denominators)','',
        '| Aligner | Corpus recordings | Transcript words | Interpolated word occurrences | OOV word occurrences | Unique OOV forms |','|---|---:|---:|---:|---:|---:|'])
    for name,e in audit['evidence'].items():lines.append(f"| {name} | 30 | {e['corpus_words']} | {e['interpolated_words']} | {e['oov_words']} | {len(e['unique_oov'])} |")
    lines.extend(['', 'Baseline MFA OOV=84 counts transcript-word occurrences across all 30 recordings containing at least one normalized token absent from the BASE dictionary, counted once per whitespace word. It is not 84 gold words, edges, unique forms or failed alignments. The prior pipeline already used temporary G2P pronunciations. WhisperX is character-based and emits no lexical OOV warnings; zero is not equivalent lexical coverage.', '',
        '| Baseline unique OOV | In 37 scored words? |','|---|---|'])
    for row in a['baseline_oov']:lines.append(f"| {row['word']} | {'yes' if row['in_scored_words'] else 'no'} |")
    if 'before_custom' in a:
        lines.extend(['','## MFA committed dictionary before/after','', '| Version | Start median / mean ms | End median / mean ms | Pooled median ms | Corpus OOV occurrences |','|---|---:|---:|---:|---:|'])
        for label,e in [('Before',a['before_custom']['mfa']),('After',audit['evidence']['mfa'])]:lines.append(f"| {label} | {e['start']['median_ms']} / {e['start']['mean_ms']} | {e['end']['median_ms']} / {e['end']['mean_ms']} | {e['overall']['median_ms']} | {e['oov_words']} |")
    return lines
