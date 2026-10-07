"""Private human recording preparation and actual, never inferred, flaw annotations."""
import re
from speecheval.inject import Label


def annotation_labels(alignment: dict, intervals: list) -> dict:
    """Convert only actual flaw-tier intervals to labels/v1; seconds and inclusive word indices."""
    flaws=[];words=alignment['words']
    for start,end,label in intervals:
        if not label.strip():continue
        match=re.fullmatch('(rushing|dragging|monotone|too_quiet|mumbling|awkward_pause|missing_pause):([1-5])',label.strip())
        if not match or not 0<=start<end<=alignment['duration_s']:raise ValueError('Invalid human flaw annotation')
        kind,severity=match.groups()
        selected=[w for w in words if w['start']<end and w['end']>start]
        if kind in ('awkward_pause','missing_pause'):
            centre=(start+end)/2
            after=next((w['i'] for w in words if w['start']>=centre),len(words)-1)
            first,last=max(0,after-1),after
        elif selected:first,last=selected[0]['i'],selected[-1]['i']
        else:raise ValueError('Region annotation has no word evidence')
        flaws.append({'type':kind,'start':round(start,3),'end':round(end,3),'severity':int(severity),
                      'word_start':first,'word_end':last,'parameters':{}})
    rid=alignment['recording_id']
    result={'schema':'labels/v1','recording_id':rid,'reference_id':None,'text_id':rid.split('__')[0],'source':'human',
            'flaws':sorted(flaws,key=lambda x:(x['start'],x['end'],x['type']))}
    Label.model_validate(result);return result
