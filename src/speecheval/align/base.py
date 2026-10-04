"""Validated alignment contracts, transcript word mapping and TextGrid export."""
from __future__ import annotations
import difflib
import re
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, model_validator
from praatio import textgrid
from speecheval.transcripts import normalize_tokens


class Word(BaseModel):
    i: int
    text: str
    norm: str
    start: float
    end: float
    sentence: int


class Sentence(BaseModel):
    i: int
    start: float
    end: float
    word_start: int
    word_end: int


class Alignment(BaseModel):
    schema_id: str = Field(alias='schema')
    recording_id: str
    audio: str
    duration_s: float
    transcript: str
    aligner: dict[str, Any]
    words: list[Word]
    sentences: list[Sentence]
    warnings: list[dict[str, Any]]
    uncertain_words: list[int] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_times(self) -> 'Alignment':
        if self.schema_id!='alignment/v1':
            raise ValueError('Unexpected alignment schema')
        for i, word in enumerate(self.words):
            if word.i!=i or not 0<=word.start<=word.end<=self.duration_s:
                raise ValueError('Invalid word indices/times')
            if i and self.words[i-1].end>word.start:
                raise ValueError('Overlapping word times')
        if any(i<0 or i>=len(self.words) for i in self.uncertain_words):
            raise ValueError('Uncertain index outside transcript')
        return self


def transcript_words(body: str) -> list[tuple[str,int,int]]:
    """Return whitespace words and character offsets, excluding punctuation-only tokens."""
    return [(m.group(),m.start(),m.end()) for m in re.finditer(r'\S+',body) if normalize_tokens(m.group())]


def map_words(body: str, output: list[dict[str, Any]], duration: float) -> tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    """Map split/merged aligned tokens to every original transcript word; seconds."""
    originals=transcript_words(body)
    target=[]; owners=[]
    for i,(text,_,_) in enumerate(originals):
        tokens=normalize_tokens(text);target.extend(tokens);owners.extend([i]*len(tokens))
    observed=[]; sources=[]
    # Allow aligners to split compound words while mapping to the unsplit original.
    for i,word in enumerate(output):
        tokens=normalize_tokens(str(word.get('word',word.get('text',''))))
        observed.extend(tokens);sources.extend([i]*len(tokens))
    mappings={i:[] for i in range(len(originals))}
    for kind,a,b,c,d in difflib.SequenceMatcher(None,target,observed,autojunk=False).get_opcodes():
        if kind=='equal':
            for ti,oi in zip(range(a,b),range(c,d)):
                mappings[owners[ti]].append(output[sources[oi]])
        elif kind=='replace':
            # Recover compounds whose aligner segmented letters differently, not real substitutions.
            if ''.join(target[a:b])==''.join(observed[c:d]):
                for owner in set(owners[a:b]):
                    mappings[owner].extend(output[sources[oi]] for oi in range(c,d))
    words=[];warnings=[]
    for i,(text,_,_) in enumerate(originals):
        found=[w for w in mappings[i] if 'start' in w and 'end' in w]
        words.append({'i':i,'text':text,'norm':' '.join(normalize_tokens(text)),
                      'start':min(float(w['start']) for w in found) if found else None,
                      'end':max(float(w['end']) for w in found) if found else None,'sentence':0})
    cursor=0
    while cursor<len(words):
        if words[cursor]['start'] is not None:
            cursor+=1;continue
        stop=cursor
        while stop<len(words) and words[stop]['start'] is None:
            stop+=1
        left=words[cursor-1]['end'] if cursor else 0.
        right=words[stop]['start'] if stop<len(words) else duration
        width=max(0.,right-left)/(stop-cursor)
        for i in range(cursor,stop):
            words[i].update(start=left+(i-cursor)*width,end=left+(i-cursor+1)*width,interpolated=True)
            warnings.append({'type':'interpolated','word':i})
        cursor=stop
    for word in words:
        word['start']=max(0.,min(duration,word['start']));word['end']=max(word['start'],min(duration,word['end']))
    for previous,current in zip(words,words[1:]):
        if previous['end']>current['start']:
            midpoint=max(previous['start'],(previous['end']+current['start'])/2)
            previous['end']=midpoint;current['start']=midpoint
            current['end']=max(current['end'],midpoint)
    for word in words:
        word['start']=round(word['start'],3);word['end']=round(word['end'],3)
    return words,warnings


def make_alignment(rid: str, body: str, windows: list[dict[str,Any]], output: list[dict[str,Any]],
                   duration: float, name: str, uncertain: list[int] | None = None, extra_warnings: list | None = None) -> dict[str,Any]:
    """Produce the shared validated alignment/v1 contract."""
    words,warnings=map_words(body,output,duration)
    spans=transcript_words(body);sentences=[]
    for unit in windows:
        included=[i for i,(_,a,_) in enumerate(spans) if unit['char_start']<=a<unit['char_end']]
        if not included:continue
        for i in included:words[i]['sentence']=unit['i']
        sentences.append({'i':unit['i'],'start':words[included[0]]['start'],'end':words[included[-1]]['end'],
                          'word_start':included[0],'word_end':included[-1]})
    payload={'schema':'alignment/v1','recording_id':rid,'audio':f'data/audio/hq/{rid}.wav',
             'duration_s':duration,'transcript':f'data/transcripts/as_spoken/{rid}.txt',
             'aligner':{'name':name,'device':'cpu','version':'3.4.2' if name=='mfa' else '3.7.2'},
             'words':words,'sentences':sentences,'warnings':warnings+(extra_warnings or []),'uncertain_words':uncertain or []}
    return Alignment.model_validate(payload).model_dump(by_alias=True)


def write_textgrid(path: Path, payload: dict[str,Any]) -> None:
    """Export valid nonzero word/sentence intervals in seconds."""
    tg=textgrid.Textgrid()
    duration=payload['duration_s']
    for name,entries in [('words',payload['words']),('sentences',payload['sentences'])]:
        intervals=[]
        for entry in entries:
            if entry['end']<=entry['start']:continue
            label=entry['text'] if name=='words' else ' '.join(w['text'] for w in payload['words'][entry['word_start']:entry['word_end']+1])
            intervals.append((entry['start'],entry['end'],label))
        tg.addTier(textgrid.IntervalTier(name,intervals,0,duration))
    path.parent.mkdir(parents=True,exist_ok=True)
    tg.save(str(path),format='long_textgrid',includeBlankSpaces=True)
