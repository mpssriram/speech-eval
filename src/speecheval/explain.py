"""Number-backed flaw explanations; deterministic templates, not generated prose."""


def explanation(region: dict, words: list[str], mode: str = 'A') -> str:
    """Quote participant words and format measured evidence to two significant figures."""
    def n(value):return f'{value:.2g}'
    kind=region['type'];e=region['evidence'];p=e['participant'];r=e['reference'];z=abs(e['z'])
    reference='your previous take' if mode=='B' else 'good readers'
    a,b=region['word_start'],region['word_end'];quote=' '.join(words[a:b+1])
    prefix=f"{region['start']:.1f}–{region['end']:.1f} s, \"{quote}\": "
    if kind=='rushing':
        text=f'you spoke at {n(p)} syllables/s; {reference} average {n(r)} ({n(p/r)}× faster, {n(z)} SD above). Rushing this phrase reduces its weight.'
    elif kind=='dragging':
        text=f'you spoke at {n(p)} vs {n(r)} syllables/s for {reference} ({n(r/p)}× slower, {n(z)} SD below). The phrase loses momentum.'
    elif kind=='monotone':
        pct=100*(1-p/r) if r else 0.
        text=f'your pitch varied by {n(p)} semitones; {reference} vary by {n(r)} ({n(pct)}% less variation, {n(z)} SD below). The phrase sounds flat.'
    elif kind=='too_quiet':
        text=f'{n(r-p)} dB quieter than {reference} relative to your own average level ({n(z)} SD below).'
        if 'sentence_final' in region['tags']:text+=' Your voice trails off at the end of the sentence.'
    elif kind=='mumbling':text=f'high-frequency energy (consonant clarity) is {n(r-p)} dB lower than {reference} ({n(z)} SD below). Words may sound muffled.'
    elif kind=='awkward_pause':
        text=f'a {n(p)} s pause between "{words[a]}" and "{words[b]}" where {reference} pause {n(r)} s ({n(p-r)} s longer, {n(z)} SD above). It breaks the sentence.'
    elif kind=='missing_pause':
        text=f'you paused {n(p)} s after "{words[a]}" where {reference} pause {n(r)} s ({n(r-p)} s shorter, {n(z)} SD below). The listener gets no breathing space.'
    else:raise ValueError('Unknown delivery flaw')
    suffix={'final_sentence':" This is the speech's final sentence.",'first_sentence':' This is the opening sentence.',
            'contains_number':' This phrase contains a number.','sentence_final':' This region reaches a sentence ending.'}
    return prefix+text+''.join(suffix[t] for t in region['tags'] if t in suffix)
