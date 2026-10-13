"""Human-readable presentation of frozen evidence; no detection or scoring changes."""
from __future__ import annotations


def explanation(region: dict, words: list[str], mode: str = 'A') -> str:
    """Format times in seconds, rates to one decimal, and cap only displayed SD."""
    def n(value: float) -> str:
        return f'{value:.2f}'

    kind = region['type']
    evidence = region['evidence']
    p, r, z = evidence['participant'], evidence['reference'], abs(evidence['z'])
    sd = 'more than 10 SD' if z > 10 else f'{n(z)} SD'
    reference = 'your previous take' if mode == 'B' else ('speaker norms' if mode == 'C' else 'good readers')
    averaged = 'averaged' if mode == 'B' else 'average'
    varied = 'varied' if mode == 'B' else 'vary'
    paused = 'paused' if mode == 'B' else 'pause'
    a, b = region['word_start'], region['word_end']
    quote = ' '.join(words[a:b + 1])
    prefix = f'{region["start"]:.2f}–{region["end"]:.2f} s, "{quote}": '
    tags = region.get('tags', [])
    if kind == 'rushing':
        text = f'you spoke at {p:.1f} syllables/s; {reference} {averaged} {r:.1f} ({n(p/r)}× faster, {sd} above). Rushing this phrase reduces its weight.'
    elif kind == 'dragging':
        text = f'you spoke at {p:.1f} vs {r:.1f} syllables/s for {reference} ({n(r/p)}× slower, {sd} below). The phrase loses momentum.'
    elif kind == 'monotone':
        pct = 100 * (1 - p/r) if r else 0.
        text = f'your pitch varied by {n(p)} semitones; {reference} {varied} by {n(r)} ({n(pct)}% less variation, {sd} below). The phrase sounds flat.'
    elif kind == 'too_quiet':
        text = f'{n(r-p)} dB quieter than {reference} relative to your own average level ({sd} below).'
        if 'sentence_final' in tags:
            text += ' Your voice trails off at the end of the sentence.'
    elif kind == 'mumbling':
        text = f'high-frequency energy (consonant clarity) is {n(r-p)} dB lower than {reference} ({sd} below). Words may sound muffled.'
    elif kind == 'awkward_pause':
        participant = 'you left no pause' if p < .02 else f'you paused {n(p)} s'
        expected = f'{reference} do not pause' if r < .02 and mode != 'B' else (
            'your previous take had no pause' if r < .02 else f'{reference} {paused} {n(r)} s')
        text = f'{participant} between "{words[a]}" and "{words[b]}", where {expected} ({n(p-r)} s longer, {sd} above). It breaks the sentence.'
    elif kind == 'missing_pause':
        participant = 'you left no pause' if p < .02 else f'you paused {n(p)} s'
        expected = f'{reference} do not pause' if r < .02 and mode != 'B' else (
            'your previous take had no pause' if r < .02 else f'{reference} {paused} {n(r)} s')
        text = f'{participant} after "{words[a]}" where {expected} ({n(r-p)} s shorter, {sd} below). The listener gets no breathing space.'
    else:
        raise ValueError('Unknown delivery flaw')
    suffix = {'final_sentence': " This is the speech's final sentence.",
              'first_sentence': ' This is the opening sentence.',
              'contains_number': ' This phrase contains a number.',
              'sentence_final': ' This region reaches a sentence ending.'}
    return prefix + text + ''.join(suffix[t] for t in tags if t in suffix)
