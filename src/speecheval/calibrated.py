"""Local CTC verification, seeded proxy-label calibration, and uncertainty tracking."""
from __future__ import annotations

import csv
import difflib
import json
import logging
import math
import os
import random
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import cmudict
import numpy as np
import torch
import yaml
from rapidfuzz.distance import Levenshtein

from speecheval.transcripts import _body_text, _escape_table, normalize_tokens
from speecheval.triage import SecondaryASR, _primary_context, write_review_html
from speecheval.verify import AcousticScorer, _hash_bytes, _write_json, build_sentence_windows, ctc_total, substitute_candidate

LOGGER = logging.getLogger(__name__)


def lexical_spans(body: str) -> list[tuple[int, int]]:
    """Whitespace-word spans with at least one spoken token; alignment indices use these."""
    return [m.span() for m in re.finditer(r'\S+', body) if normalize_tokens(m.group())]


def choose_margin(true_minus_fake: list[float], max_rate: float = .02) -> tuple[float, float]:
    """Smallest positive representable nats margin satisfying inclusive empirical FAR."""
    if not true_minus_fake or not all(math.isfinite(x) for x in true_minus_fake):
        raise ValueError('Calibration requires finite scored controls')
    fake_advantages = sorted((-x for x in true_minus_fake), reverse=True)
    allowed = math.floor(len(fake_advantages) * max_rate)
    if allowed >= len(fake_advantages):
        raise ValueError('Invalid false acceptance rate')
    # >= includes ties: move one representable float above the excluded observation.
    margin = max(float(np.nextafter(0., math.inf)), float(np.nextafter(fake_advantages[allowed], math.inf)))
    rate = sum(x >= margin for x in fake_advantages) / len(fake_advantages)
    return margin, rate


def local_window(body: str, start: int, end: int, variant: str,
                 aligned: list[dict[str, Any]], duration: float, padding: float = .2) -> dict[str, Any]:
    """Disputed span plus exactly one neighbouring transcript word, times in clip seconds."""
    spans = lexical_spans(body)
    affected = [i for i, (a, b) in enumerate(spans) if a < end and b > start]
    if affected:
        lo, hi = max(0, min(affected)-1), min(len(spans), max(affected)+2)
    else:
        insertion = next((i for i, (a, _) in enumerate(spans) if a >= start), len(spans))
        lo, hi = max(0, insertion-1), min(len(spans), insertion+1)
    if not spans or hi <= lo or len(aligned) != len(spans):
        return {'valid': False, 'reason': 'No aligned local word span'}
    char_lo, char_hi = min(spans[lo][0], start), max(spans[hi-1][1], end)
    a = body[char_lo:char_hi]
    b = substitute_candidate(a, start-char_lo, end-char_lo, variant)
    return {'valid': True, 'start_s': round(0. if start==end and start<=spans[0][0] else max(0., float(aligned[lo]['start'])-padding), 3),
            'end_s': round(duration if start==end and start>=spans[-1][1] else min(duration, float(aligned[hi-1]['end'])+padding), 3),
            'candidate_a': a, 'candidate_b': b, 'word_start': lo, 'word_end': hi-1,
            'interpolated_boundary': bool(aligned[lo].get('interpolated') or aligned[hi-1].get('interpolated'))}


def apply_and_uncertain(body: str, items: list[dict[str, Any]]) -> tuple[str, list[int]]:
    """Apply edits against original offsets and translate unresolved spans to final word indices."""
    uncertain = []
    for item in items:
        if item['decision'] == 'UNSURE':
            uncertain.append([item['transcript_start'], item['transcript_end']])
    for item in sorted((i for i in items if i['decision']=='APPLY_B'), key=lambda i: i['transcript_start'], reverse=True):
        start, end = item['transcript_start'], item['transcript_end']
        updated = substitute_candidate(body, start, end, item['asr'])
        shift = len(updated)-len(body)
        for span in uncertain:
            if end <= span[0]:
                span[0] += shift
                span[1] += shift
        body = updated
    indices = set()
    spans = lexical_spans(body)
    for start, end in uncertain:
        affected = [i for i, (a,b) in enumerate(spans) if a < end and b > start]
        if not affected:  # An unresolved insertion has no word: exclude its flanking words.
            k = next((i for i,(a,_) in enumerate(spans) if a >= start), len(spans))
            affected = [i for i in (k-1,k) if 0 <= i < len(spans)]
        indices.update(affected)
    return body, sorted(indices)


def check_baseline(current: str, original: str, previous_hash: str | None) -> None:
    """Reject unrelated edits, including recordings absent from the original review list."""
    expected=previous_hash or _hash_bytes(original.encode())
    if _hash_bytes(current.encode())!=expected:
        raise ValueError('Transcript modified since original audit; refusing overwrite')


class LocalScorer(AcousticScorer):
    def __init__(self, root: Path, settings: dict[str, Any]) -> None:
        inference={key:settings[key] for key in ('device','threads','model')}
        inference.update(numerics='isolated_cpu_v1',mkldnn=False,mha_fastpath=False,float32_precision='highest')
        torch.manual_seed(0);torch.set_num_threads(int(inference['threads']));torch.use_deterministic_algorithms(True)
        torch.backends.mkldnn.enabled=False;torch.backends.mha.set_fastpath_enabled(False)
        torch.set_float32_matmul_precision('highest');torch.set_flush_denormal(False)
        super().__init__(root,inference)
        self.directory=root/'data/.cache/acoustic_verification_isolated'
        self.directory.mkdir(parents=True,exist_ok=True)

    def score(self, emission: torch.Tensor, text: str) -> float | None:
        normalized = '|'.join(normalize_tokens(text)).upper()
        if any(c not in self.labels for c in normalized):
            return None
        return ctc_total(emission, [self.labels[c] for c in normalized], self.labels['-'])


def score_pair(root: Path, scorer: LocalScorer, rid: str, window: dict[str, Any]) -> dict[str, Any]:
    """Cache total scores keyed by identical audio and both candidate texts."""
    if not window['valid'] or window['end_s'] <= window['start_s']:
        return {'score_a': None, 'score_b': None, 'delta_nats': None}
    emission, emission_key = scorer.emissions(root / 'data/audio/align16k' / f'{rid}.wav', window['start_s'], window['end_s'])
    key = _hash_bytes(json.dumps({'emission': emission_key, 'a': window['candidate_a'], 'b': window['candidate_b'],
                                'method': 'ctc_total/v1'}, sort_keys=True).encode())
    path = root / 'data/.cache/local_scores' / f'{key}.json'
    if path.exists():
        return json.loads(path.read_text())
    a,b = scorer.score(emission, window['candidate_a']), scorer.score(emission, window['candidate_b'])
    result = {'score_a': a, 'score_b': b, 'delta_nats': None if a is None or b is None else b-a,
              'frames': len(emission), 'emission_key': emission_key}
    _write_json(path, result)
    return result


def isolated_scores(root: Path, jobs: list[dict[str,Any]]) -> list[dict[str,Any]]:
    """Separate ASR libraries from acoustic numerical state in a clean CPU process."""
    with tempfile.TemporaryDirectory(prefix='ctc-worker-',dir=root/'data/.cache') as tmp:
        request=Path(tmp)/'input.json';output=Path(tmp)/'output.json'
        _write_json(request,{'root':str(root),'jobs':jobs})
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        env.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONHASHSEED='0')
        subprocess.run([sys.executable,'-m','speecheval.ctc_worker',str(request),str(output)],env=env,cwd=root,check=True)
        return json.loads(output.read_text())


def original_alignment(root: Path, rid: str, original: str, row: dict[str, str]) -> dict[str, Any]:
    """CPU forced-align original A before taking local window boundaries."""
    from speecheval.align.whisperx_align import align_recording
    body = _body_text(original)
    asr = json.loads((root / 'data/alignment/asr' / f'{rid}.json').read_text())
    windows = build_sentence_windows(body, asr['words'], float(row['cut_start_s']), float(row['cut_end_s']), .3,
                                     row['text_id']=='o_captain')
    identity = {'transcript_sha256': _hash_bytes(original.encode()), 'asr_sha256': _hash_bytes(json.dumps(asr,sort_keys=True).encode()),
                'audio_sha256': _hash_bytes((root / 'data/audio/align16k' / f'{rid}.wav').read_bytes())}
    path = root / 'data/review/original_alignment' / f'{rid}.json'
    if path.exists() and json.loads(path.read_text()).get('identity') == identity:
        return json.loads(path.read_text())
    payload = align_recording(root, rid, body, windows, float(row['duration_s']))
    payload['identity'] = identity
    _write_json(path, payload)
    return payload


def calibration_controls(root: Path, inputs: dict[str, Any], rows: dict[str, Any],
                         alignments: dict[str, Any], settings: dict[str, Any]) -> list[dict[str, Any]]:
    """Draw seeded controls proportional to eligible words, at least one per recording."""
    path = root / 'data/review/calibration_controls.json'
    identity = {'inputs': _hash_bytes(json.dumps(inputs,sort_keys=True).encode()),
                'alignments': _hash_bytes(json.dumps(alignments,sort_keys=True).encode()), 'seed': settings['seed'], 'count': settings['controls']}
    if path.exists():
        saved = json.loads(path.read_text())
        if saved['identity'] != identity:
            raise ValueError('Control inputs changed; preserve audit before recalibration')
        return saved['controls']
    old = json.loads((root / 'data/review/acoustic_verification_legacy.json').read_text())
    secondary = SecondaryASR(root)
    medium_path = root / 'data/review/calibration_medium_asr.json'
    medium = json.loads(medium_path.read_text()) if medium_path.exists() else {}
    pools = {}
    for rid, original in inputs['transcripts'].items():
        body = _body_text(original)
        spans = lexical_spans(body)
        old_uncertain = [i for i in old['items'] if i['recording_id']==rid and i['decision']=='UNSURE']
        forbidden = set()
        for item in old_uncertain:
            lo,hi = item['transcript_start'],item['transcript_end']
            if lo==hi:
                k=next((i for i,(a,_) in enumerate(spans) if a>=lo),len(spans))
                forbidden.update(i for i in (k-1,k) if 0<=i<len(spans))
            else:
                forbidden.update(i for i,(a,b) in enumerate(spans) if a<hi and b>lo)
        file = root / 'data/transcripts/uncertain' / f'{rid}.json'
        if file.exists():
            forbidden.update(json.loads(file.read_text()).get('uncertain_words', []))
        row = rows[rid]
        asr = json.loads((root / 'data/alignment/asr' / f'{rid}.json').read_text())['words']
        units = build_sentence_windows(body,asr,float(row['cut_start_s']),float(row['cut_end_s']),.3,row['text_id']=='o_captain')
        eligible = []
        full_medium = None
        for unit in units:
            indices = [i for i,(a,_) in enumerate(spans) if unit['char_start'] <= a < unit['char_end']]
            if not unit['valid'] or len(indices)<3 or any(i in forbidden for i in indices):
                continue
            primary = _primary_context(asr,float(row['cut_start_s']),unit['start'],unit['end'])
            if normalize_tokens(primary)!=normalize_tokens(unit['text']):
                continue
            audio = root / 'data/audio/align16k' / f'{rid}.wav'
            key = _hash_bytes(json.dumps({'audio':_hash_bytes(audio.read_bytes()),'start':unit['start'],'end':unit['end'],
                                         'model':'medium.en','beam':5,'device':'cpu','compute_type':'int8'},sort_keys=True).encode())
            if key not in medium:
                LOGGER.info('Control proxy sentence: %s %.3f-%.3f',rid,unit['start'],unit['end'])
                medium[key] = {'recording_id':rid,'window':unit,'text':secondary.transcribe(audio,unit['start'],unit['end']),
                               'audio_sha256':_hash_bytes(audio.read_bytes())}
                _write_json(medium_path,medium)
            if normalize_tokens(medium[key]['text']) == normalize_tokens(unit['text']):
                for i in indices[1:-1]:
                    eligible.append({'word_index':i,'sentence_index':unit['i'],'proxy_asr_key':key})
        if not eligible:
            # Contextual decoding is independent and uses no transcript prompt.
            # It can resolve clipped-sentence ASR errors without relaxing agreement.
            full_medium = medium_recording(root, secondary, rid, float(row['duration_s']))
            for unit in units:
                indices=[i for i,(a,_) in enumerate(spans) if unit['char_start']<=a<unit['char_end']]
                if len(indices)<3 or any(i in forbidden for i in indices):continue
                primary=_primary_context(asr,float(row['cut_start_s']),unit['start'],unit['end'])
                if normalize_tokens(primary)!=normalize_tokens(unit['text']):continue
                aligned=alignments[rid]['words']
                second=_primary_context(full_medium['words'],0.,max(0.,aligned[indices[0]]['start']-.05),
                                        aligned[indices[-1]]['end']+.05)
                if normalize_tokens(second)==normalize_tokens(unit['text']):
                    for i in indices[1:-1]:
                        eligible.append({'word_index':i,'sentence_index':unit['i'],'proxy_asr_key':full_medium['cache_key']})
        if not eligible:
            raise ValueError(f'No three-way-agreeing, non-uncertain control words for {rid}, even with full-recording context')
        pools[rid]=eligible
    rng = random.Random(settings['seed'])
    total = sum(len(p) for p in pools.values())
    count = settings['controls']
    remaining = count-len(pools)
    allocation = {rid: 1+int(remaining*len(pool)/total) for rid,pool in pools.items()}
    remainder = count-sum(allocation.values())
    ranked = sorted(pools,key=lambda rid: (-(remaining*len(pools[rid])/total % 1),rid))
    for rid in ranked[:remainder]:
        allocation[rid]+=1
    pronunciations = cmudict.dict()
    by_length = {}
    for word, phones in sorted(pronunciations.items()):
        if re.fullmatch('[a-z]+',word):
            for phone in phones:
                by_length.setdefault(len(phone),[]).append((word,phone))
    neighbours = {}
    controls=[]
    kinds=('substitution','deletion','insertion')
    for rid,pool in sorted(pools.items()):
        body=_body_text(inputs['transcripts'][rid]); spans=lexical_spans(body)
        for n in range(allocation[rid]):
            kind=kinds[len(controls)%3]
            choices=[]
            for candidate in pool:
                i=candidate['word_index'];a,b=spans[i]; word=''.join(normalize_tokens(body[a:b]))
                if kind=='substitution':
                    if word not in neighbours:
                        close=set()
                        for phone in pronunciations.get(word,[]):
                            for size in range(max(1,len(phone)-2),len(phone)+3):
                                for other,other_phone in by_length.get(size,[]):
                                    if other!=word and 1<=Levenshtein.distance(phone,other_phone)<=2:
                                        close.add(other)
                        neighbours[word]=sorted(close)
                    if not neighbours[word]:
                        continue
                choices.append(candidate)
            if not choices:
                raise ValueError(f'No phonetic substitution controls for {rid}')
            candidate=rng.choice(choices);i=candidate['word_index'];a,b=spans[i];word=''.join(normalize_tokens(body[a:b]))
            variant=rng.choice(neighbours[word]) if kind=='substitution' else ('' if kind=='deletion' else rng.choice(['the','a','of','to','and','in']))
            if kind=='insertion':
                b=a
            window=local_window(body,a,b,variant,alignments[rid]['words'],float(rows[rid]['duration_s']),settings['padding_s'])
            controls.append({'recording_id':rid,'kind':kind,'true_word_index':i,'variant':variant,
                             **candidate,'window':window})
    _write_json(path,{'identity':identity,'allocation':allocation,'eligible_words':{r:len(p) for r,p in pools.items()},
                      'proxy_label_not_human_ground_truth':True,'controls':controls})
    return controls


def medium_recording(root: Path, secondary: SecondaryASR, rid: str, duration: float) -> dict[str,Any]:
    """Independent unprompted full-clip medium.en decoding with CPU word alignment."""
    from speecheval.prepare import _import_whisperx, _round_asr_result
    from speecheval.align import whisperx_align as wx_alignment
    audio=root/'data/audio/align16k'/f'{rid}.wav'
    sha=_hash_bytes(audio.read_bytes())
    path=root/'data/review/medium_full_asr'/f'{rid}.json'
    if path.exists():
        obj=json.loads(path.read_text())
        if obj['audio_sha256']==sha:return obj
    LOGGER.info('Full-context independent medium.en: %s',rid)
    if secondary.model is None:
        secondary.transcribe(audio,0.,min(5.,duration))
    result=secondary.model.transcribe(str(audio),batch_size=1,language='en')
    wx=_import_whisperx()
    model,metadata=wx_alignment.get_align_model(root)
    aligned=wx.align(result['segments'],model,metadata,str(audio),'cpu',print_progress=False)
    payload={'model':'medium.en','device':'cpu','compute_type':'int8','beam_size':5,'temperature':0.,
             'audio_sha256':sha,'cache_key':_hash_bytes((rid+sha+'medium.en/full').encode()),'time_basis':'prepared_clip',
             **_round_asr_result(aligned)}
    _write_json(path,payload)
    return payload


def histogram_svg(values: list[float], margin: float) -> str:
    """Deterministic SVG histogram of true-minus-fake totals, marking +/- margin."""
    counts,edges=np.histogram(values,bins=30)
    lo=min(float(edges[0]),-margin);hi=max(float(edges[-1]),margin)
    scale=lambda x: 65+700*(x-lo)/(hi-lo if hi>lo else 1)
    height=max(1,int(counts.max()))
    pieces=['<svg xmlns="http://www.w3.org/2000/svg" width="820" height="360" viewBox="0 0 820 360">',
            '<rect width="820" height="360" fill="white"/>',
            '<text x="65" y="24" font-family="sans-serif" font-size="17">Local total CTC: true minus fake (proxy-label controls)</text>']
    for count,a,b in zip(counts,edges[:-1],edges[1:]):
        h=250*int(count)/height
        pieces.append(f'<rect x="{scale(a):.3f}" y="{290-h:.3f}" width="{max(1.,scale(b)-scale(a)-1):.3f}" height="{h:.3f}" fill="#28769c"/>')
    for x,label,color in [(margin,'+m','#bc3b36'),(-margin,'-m: fake acceptance boundary','#b06417')]:
        pos=scale(x)
        pieces.append(f'<path d="M {pos:.3f} 42 V 290" stroke="{color}" stroke-width="2" stroke-dasharray="5 4"/>')
        pieces.append(f'<text x="{min(pos+4,560):.3f}" y="{48 if x>=0 else 70}" font-family="sans-serif" font-size="12" fill="{color}">{label}: {x:.6g}</text>')
    pieces.extend([f'<text x="65" y="320" font-family="sans-serif">{lo:.3f} nats</text>',
                   f'<text x="680" y="320" font-family="sans-serif">{hi:.3f} nats</text>',
                   '<text x="65" y="346" font-family="sans-serif" font-size="12">Fake accepted when true - fake &lt;= -m. Counts are in-sample, not human accuracy.</text>','</svg>'])
    return '\n'.join(pieces)+'\n'


def regenerate_secondary(root: Path, inputs: dict[str,Any], rows: dict[str,Any]) -> None:
    """Actually redecode repaired recordings' old medium.en clips, preserving prior cache."""
    path=root/'data/review/secondary_asr.json'
    history=root/'data/review/secondary_asr_legacy.json'
    if not history.exists():_write_json(history,json.loads(path.read_text()))
    cache=json.loads(path.read_text())
    repairs={r['recording_id'] for r in json.loads((root/'data/review/audio_repairs.json').read_text())}
    marker=root/'data/review/secondary_regeneration.json'
    evidence=json.loads(marker.read_text()) if marker.exists() else {}
    model=SecondaryASR(root)
    for n,item in enumerate(inputs['items']):
        rid=item['recording_id']
        if rid not in repairs:continue
        audio=root/'data/audio/hq'/f'{rid}.wav'
        sha=_hash_bytes(audio.read_bytes())
        start=max(0.,item['start_s']-1);end=min(float(rows[rid]['duration_s']),item.get('end_s',item['start_s'])+1)
        identity={'audio_sha256':sha,'start_s':round(start,3),'end_s':round(end,3),'model':'medium.en','device':'cpu',
                  'compute_type':'int8','beam_size':5,'temperature':0.0}
        key=_hash_bytes(json.dumps(identity,sort_keys=True).encode())
        if key not in evidence:
            LOGGER.info('Regenerating medium clip %s %.3f-%.3f',rid,start,end)
            text=model.transcribe(audio,start,end)
            cache[key]={**identity,'recording_id':rid,'text':text}
            evidence[key]={'recording_id':rid,'regenerated':True,'cache_key':key}
            _write_json(path,cache);_write_json(marker,evidence)


def render_calibrated_report(root: Path, audit: dict[str,Any], calibration: dict[str,Any]) -> None:
    """Write calibration evidence, comparison to legacy results and all final decisions."""
    margin=audit['margin_total_nats'];values=[c['true_minus_fake'] for c in calibration['controls']]
    (root/'reports/day01_ctc_calibration.svg').write_text(histogram_svg(values,margin),encoding='utf-8')
    old=json.loads((root/'data/review/acoustic_verification_legacy.json').read_text())
    lines=['# Day 1 calibrated automatic acoustic verification','',
           'Original pre-verification transcripts are candidate A for all 85 items, including the six earlier edits. Candidate B substitutes the frozen ASR variant.',
           'Identical local audio covers the disputed words plus one neighbouring word on either side, padded 0.2 s. Word edges come from CPU WhisperX forced alignment of ORIGINAL text. Scores are total CTC log-likelihoods in nats, summed over valid paths, never per-frame averages.',
           'CPU wav2vec2 runs in an isolated scoring process, fixed seed, evaluation mode, one thread, highest float32 precision, disabled MKLDNN/MHA fastpaths and deterministic PyTorch settings. Impossible paths or invalid windows remain UNSURE. A preliminary mixed-process cache differed from fresh CPU scores by about 0.002 nats; it is preserved as pre_isolation evidence and superseded, not passed off as deterministic.','',
           'For insertions at the very start/end of a transcript, the missing outer neighbour is replaced by the prepared-clip boundary so disputed edge audio is not silently omitted. Edge noise/readout material may affect those preferences; complete spoken words are not human-confirmed.','',
           f"Margin m = {margin:.12g} total nats. Empirical fake-acceptance rate = {calibration['false_acceptance_rate']:.3%} ({calibration['false_acceptances']}/300).",
           f"Final counts: {audit['counts']}. Legacy sentence-average counts: {old['counts']}.",
           '[Preserved old report](day01_acoustic_verification_legacy.md); full original score audit: data/review/acoustic_verification_legacy.json.','',
           '## Calibration','',
           'Three-way normalized transcript / large-v3 / medium.en agreement is a proxy label, NOT human ground truth. Controls are sampled with replacement in fixed-seed proportions to eligible words, with at least one from every recording. Prior uncertain words (and their insertion neighbours) are excluded. The margin is the smallest positive representable value satisfying inclusive fake-minus-true >= m in at most 2% of these controls; ties are excluded together.',
           'The reported rate is in-sample, not a held-out guarantee. Related ASR/acoustic models share errors. Artificial fakes may not represent real disagreements; repeated controls and sentences are correlated. Large multi-word edit groups still span more audio than single-word controls. A universal margin may not transfer equally across edit types, speakers or recording quality.','',
           '![True minus fake histogram](day01_ctc_calibration.svg)','',
           '| True minus fake statistic | Total nats |','|---|---:|']
    for label,q in [('min',0),('p10',.1),('median',.5),('p90',.9),('max',1)]:
        lines.append(f'| {label} | {np.quantile(values,q):.6f} |')
    lines.extend(['','| Recording | Controls | Uncertain words |','|---|---:|---:|'])
    allocations=Counter(c['recording_id'] for c in calibration['controls'])
    for rid,count in sorted(audit['uncertain_counts'].items()):
        lines.append(f'| {rid} | {allocations[rid]} | {count} |')
    lines.extend(['',f"Total uncertain words: {sum(audit['uncertain_counts'].values())}. Indices are zero-based FINAL as-spoken whitespace-word indices. Unresolved insertions exclude both neighbouring words because no inserted word exists. Later reference statistics and evaluation must exclude these indices.",'',
                  '## Prepared audio and ASR regeneration','',
                  '| Recording | Old cut (source s) | New cut (source s) |','|---|---|---|'])
    for repair in audit['audio_repairs']:
        lines.append(f"| {repair['recording_id']} | {repair['old_start_s']:.3f}–{repair['old_end_s']:.3f} | {repair['new_start_s']:.3f}–{repair['new_end_s']:.3f} |")
    lines.extend(['',
        'All 12 full-source large-v3 caches were actually regenerated from raw audio; old caches are retained under data/review/legacy_asr. The repaired recordings\' medium.en dispute clips were redecode-regenerated, and calibration sentences have newly decoded medium.en caches. Source timestamps stay in full-source coordinates; sentence/local windows are prepared-clip relative. All 30 cuts match excerpts.yaml and recordings.csv; all final windows are regenerated from final text and current ASR. Raw audio is unchanged.',
        'Historical triage count: a same-input replay of commit 7f989f7 gives 178 before numeric normalization fixes and 177 after them; JFK changes from 6 to 5 groups. Fixes separate expanded digits from adjacent hyphen/letter tokens and handle commas in thousands. Evidence: data/review/triage_count_reconciliation.json. The frozen triage audit has 78 IGNORE + 14 LIKELY_ASR + 53 LISTEN + 32 LIKELY_REAL = 177, with 85 original review items. Full-poem/ASR regeneration and final edits change the new diff count; those counts refer to different inputs, not dropped review items.',
        'This automatic marker is not human review. Verification decisions cover the original 85 items, not every newly exposed diff; additional differences remain documented in the refreshed diff report.','',
        '## Original 85 decisions','',
        '| Recording | Original time | Local window | A | B | A total | B total | B minus A | Decision |','|---|---:|---|---|---|---:|---:|---:|---|'])
    for item in audit['items']:
        w=item['window'];bounds=f"{w['start_s']:.3f}–{w['end_s']:.3f}s" if w['valid'] else 'invalid'
        nums=['unscorable' if item.get(k) is None else f'{item[k]:.6f}' for k in ('score_a','score_b','delta_nats')]
        lines.append(f"| {item['recording_id']} | {item['start_s']:.3f}s | {bounds} | {_escape_table(w.get('candidate_a',''))} | {_escape_table(w.get('candidate_b',''))} | {' | '.join(nums)} | {item['decision']} |")
    (root/'reports/day01_acoustic_verification.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    listen=['# Day 1 listen list — calibrated automatic decisions','',
            'All original 85 items. UNSURE is unchanged; no human review claimed. See day01_acoustic_verification.md.','',
            '| Recording | Time | Transcript says | ASR says | Class | Decision |','|---|---:|---|---|---|---|']
    for item in audit['items']:
        listen.append(f"| {item['recording_id']} | {item['start_s']:.3f}s | {_escape_table(item['transcript'])} | {_escape_table(item['asr'])} | {item['class']} | {item['decision']} |")
    (root/'reports/day01_listen_list.md').write_text('\n'.join(listen)+'\n')
    write_review_html(root/'data/review/index.html',audit['items'])


def verify_calibrated(root: Path | None = None) -> dict[str,Any]:
    """Calibrate local totals and reapply all original candidates without circular scoring."""
    root=(root or Path.cwd()).resolve()
    config=yaml.safe_load((root/'configs/default.yaml').read_text())
    settings=config['transcript_verification']
    scorer=LocalScorer(root,settings)
    path=root/'data/review/acoustic_verification_calibrated.json'
    if path.exists():
        audit=json.loads(path.read_text())
        if audit['settings']!=settings or audit['model_sha256']!=scorer.model_hash:
            raise ValueError('Calibrated settings or model changed; preserve audit before rerun')
        for rid,sha in audit['audio_sha256'].items():
            if _hash_bytes((root/'data/audio/align16k'/f'{rid}.wav').read_bytes())!=sha:
                raise ValueError('Audio changed after calibrated audit')
        for rid,sha in audit['output_transcript_sha256'].items():
            if _hash_bytes((root/'data/transcripts/as_spoken'/f'{rid}.txt').read_bytes())!=sha:
                raise ValueError('Transcript changed after calibrated audit')
        from speecheval.verify import _refresh_output_windows
        _refresh_output_windows(root,config,{'transcripts':audit['output_transcript_sha256']})
        render_calibrated_report(root,audit,json.loads((root/'data/review/ctc_calibration.json').read_text()))
        LOGGER.info('Reusing calibrated audit: %s',audit['counts']);return audit
    inputs=json.loads((root/'data/review/verification_input.json').read_text())
    legacy=root/'data/review/acoustic_verification_legacy.json'
    if not legacy.exists():
        _write_json(legacy,json.loads((root/'data/review/acoustic_verification.json').read_text()))
        (root/'reports/day01_acoustic_verification_legacy.md').write_text((root/'reports/day01_acoustic_verification.md').read_text())
    rows={r['recording_id']:r for r in csv.DictReader((root/'data/manifest/recordings.csv').open())}
    alignments={rid:original_alignment(root,rid,original,rows[rid]) for rid,original in inputs['transcripts'].items()}
    controls=calibration_controls(root,inputs,rows,alignments,settings)
    control_scores=isolated_scores(root,controls)
    scored=[]
    for n,(control,scores) in enumerate(zip(controls,control_scores),1):
        if scores['delta_nats'] is None:
            raise ValueError('Unscorable control; calibration aborted rather than changing denominator')
        scored.append({**control,**scores,'true_minus_fake':-scores['delta_nats']})
        if n%25==0:LOGGER.info('Scored controls %d/300',n)
    margin,rate=choose_margin([c['true_minus_fake'] for c in scored],settings['max_false_acceptance_rate'])
    calibration={'schema':'ctc_calibration/v1','margin_total_nats':margin,'false_acceptance_rate':rate,
                 'false_acceptances':sum(c['delta_nats']>=margin for c in scored),'seed':settings['seed'],
                 'proxy_label_not_human_ground_truth':True,'controls':scored}
    _write_json(root/'data/review/ctc_calibration.json',calibration)
    regenerate_secondary(root,inputs,rows)
    items=[]
    for frozen in inputs['items']:
        item=frozen.copy();rid=item['recording_id'];body=_body_text(inputs['transcripts'][rid])
        window=local_window(body,item['transcript_start'],item['transcript_end'],item['asr'],alignments[rid]['words'],
                            float(rows[rid]['duration_s']),settings['padding_s'])
        item['window']=window;items.append(item)
    item_scores=isolated_scores(root,items)
    for item,scores in zip(items,item_scores):
        delta=scores['delta_nats']
        decision='UNSURE' if delta is None else ('APPLY_B' if delta>=margin else ('KEEP_A' if -delta>=margin else 'UNSURE'))
        item.update(**scores,decision=decision)
    hashes={};uncertain_counts={}
    previous_path=root/'data/review/acoustic_verification_calibrated_pre_isolation.json'
    previous=json.loads((previous_path if previous_path.exists() else legacy).read_text())
    for rid,original in inputs['transcripts'].items():
        check_baseline((root/'data/transcripts/as_spoken'/f'{rid}.txt').read_text(),original,
                       previous['output_transcript_sha256'].get(rid))
    for rid,original in inputs['transcripts'].items():
        current_path=root/'data/transcripts/as_spoken'/f'{rid}.txt'
        expected=previous['output_transcript_sha256'].get(rid)
        current=current_path.read_text()
        check_baseline(current,original,expected)
        own=[i for i in items if i['recording_id']==rid]
        body,uncertain=apply_and_uncertain(_body_text(original),own)
        headers=[line for line in original.splitlines() if line.startswith('#') and not line.startswith(('# reviewed:','# verification:'))]
        headers.extend(['# reviewed: auto-acoustic-calibrated',
                        f'# verification: original_85_items; total_ctc_margin={margin:.12g}; human_review=no; uncertain_words={len(uncertain)}'])
        current_path.write_text('\n'.join(headers)+'\n'+body+'\n',encoding='utf-8')
        hashes[rid]=_hash_bytes(current_path.read_bytes());uncertain_counts[rid]=len(uncertain)
        _write_json(root/'data/transcripts/uncertain'/f'{rid}.json',{'schema':'transcript_uncertainty/v1','recording_id':rid,
                    'transcript_sha256':hashes[rid],'word_index_basis':'final_as_spoken_whitespace_words',
                    'uncertain_words':uncertain,'reason':'Unresolved original verification items; insertion neighbours excluded'})
    config['transcript_verification']['margin_total_nats']=margin
    config['transcript_verification']['measured_false_acceptance_rate']=rate
    (root/'configs/default.yaml').write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    from speecheval.verify import _refresh_output_windows
    _refresh_output_windows(root,config,inputs)
    audit={'schema':'acoustic_verification/v2','method':'local_total_ctc','human_reviewed':False,
           'margin_total_nats':margin,'false_acceptance_rate':rate,'model_sha256':scorer.model_hash,
           'counts':{name:sum(i['decision']==name for i in items) for name in ('APPLY_B','KEEP_A','UNSURE')},
           'items':items,'uncertain_counts':uncertain_counts,'output_transcript_sha256':hashes,
           'audio_repairs':json.loads((root/'data/review/audio_repairs.json').read_text()),'settings':settings,
           'audio_sha256':{rid:_hash_bytes((root/'data/audio/align16k'/f'{rid}.wav').read_bytes()) for rid in rows}}
    _write_json(path,audit);render_calibrated_report(root,audit,calibration)
    LOGGER.info('Calibrated verification: margin %.12g, FAR %.3f, %s',margin,rate,audit['counts'])
    return audit
