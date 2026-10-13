"""Readable templates over frozen JSON evidence; never mutate detection or scoring."""
from __future__ import annotations
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP, localcontext
import yaml

def _fixed(value: float, digits: int = 2) -> str:
    """Match the browser's fixed-point rounding over the same JSON number."""
    number = Decimal(str(value))
    with localcontext() as context:
        context.prec = max(28, number.adjusted() + digits + 2)
        return format(number.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP), 'f')


def explanation(region: dict, words: list[str], mode: str = 'A', threshold: float | None = None) -> str:
    """Format seconds to two decimals and features/SD to one; cap only displayed SD."""
    kind=region['type'];e=region['evidence'];p=e['participant'];r=e['reference'];z=abs(e['z'])
    if threshold is None:
        config=yaml.safe_load((Path(__file__).resolve().parents[2]/'configs/detector.yaml').read_text())
        features={'rushing':'rate','dragging':'rate','monotone':'pitchrange','too_quiet':'final_drop','missing_pause':'end_pause'}
        threshold=config['mode_c']['k'][features[kind]] if mode=='C' and kind in features else config['k'][kind]
    def n(v: float) -> str:
        text=_fixed(v, 1)
        return ('0.0' if text=='-0.0' else text).replace('-','−')
    def pause(v: float) -> str:
        return 'none' if v<.02 else f'{_fixed(v)} s'
    ref='your earlier take' if mode=='B' else ('typical speakers' if mode=='C' else 'good readers')
    average="your earlier take's average" if mode=='B' else ref+"' average"
    a,b=region['word_start'],region['word_end'];quote=' '.join(words[a:b+1])
    header=f'{kind.replace("_"," ").capitalize()} · {_fixed(region["start"])}–{_fixed(region["end"])} s · "{quote}"'
    if kind=='rushing':
        what='You spoke much faster here.';measured=f'{n(p)} syllables per second (you) vs {n(r)} syllables per second ({ref})';off=f'{n(p/r)} times faster';why='Listeners may miss words.'
    elif kind=='dragging':
        what='You spoke much more slowly here.';measured=f'{n(p)} syllables per second (you) vs {n(r)} syllables per second ({ref})';off=f'{n(r/p)} times slower';why='The phrase loses momentum.'
    elif kind=='monotone':
        what='Your pitch stayed flat here.';measured=f'{n(p)} semitones (you) vs {n(r)} semitones ({ref})';off=f'{n(100*p/r if r else 0)}% of the reference range';why='Flat pitch hides which words matter.'
    elif kind=='too_quiet':
        what='You were much quieter here.';measured=f'{n(p)} dB (you) vs {n(r)} dB ({ref}), relative to your own average';off=f'{n(r-p)} dB quieter';why='Listeners may lose these words.'
    elif kind=='mumbling':
        what='Your words were less crisp here.';measured=f'clarity measure (high-frequency energy): {n(p)} dB (you) vs {n(r)} dB ({ref})';off=f'{n(r-p)} dB lower';why='Consonants are harder to hear.'
    elif kind in ('awkward_pause','missing_pause'):
        expected='no pause' if r<.02 else pause(r)
        measured=f"pause after '{words[a]}': {pause(p)} (you) vs {expected} ({ref})"
        if kind=='awkward_pause':
            what='You paused in the middle of a phrase.';off=f'{_fixed(p-r)} s longer';why='It breaks the sentence.'
        else:
            what=('You did not pause where ' if p<.02 else 'Your pause was too short where ')+ref+(' pauses.' if mode=='B' else ' pause.');off=f'{_fixed(r-p)} s shorter';why='Listeners get no breathing space.'
    else:raise ValueError('Unknown delivery flaw')
    sd='more than 10 SD' if z>10 else f'{n(z)} SD'
    direction='below' if e['z']<0 else 'above'
    article = '' if mode == 'B' else 'the '
    lines=[header,'What happened: '+what,'Measured: '+measured,f'How far off: {off}, which is {sd} {direction} {article}{average}. Flags start at {_fixed(threshold, 1)} SD.','Why it matters: '+why]
    tags=region.get('tags',[]);where=[]
    if 'first_sentence' in tags:where.append('opening sentence')
    if 'final_sentence' in tags:where.append('final sentence')
    if where:lines.append('Where: '+' / '.join(where))
    return '\n'.join(lines)
