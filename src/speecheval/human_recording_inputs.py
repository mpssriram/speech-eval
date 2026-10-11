"""Recorder-authorised rule-built text; ASR is never independent ground truth."""
from __future__ import annotations
import difflib
import hashlib
import json
from pathlib import Path
import re

from speecheval.align.base import transcript_words
from speecheval.human_takes import expanded_transcript
from speecheval.verify import sentence_units, _write_json


def norm(word: str) -> str:
    """Case/punctuation-insensitive whole word, retaining contraction apostrophes."""
    return re.sub(r"[^a-z0-9']", '', word.lower().replace('’', "'")).strip("'")


def atoms(word: str) -> list[str]:
    """Lexical expansion only to match contraction forms; no acoustic inference."""
    value=norm(word)
    special={'cannot':['can','not'],"can't":['can','not'],"won't":['will','not'],
             "i'd":['i','had']}
    if value in special:return special[value]
    for suffix,tail in (("n't",'not'),("'ve",'have'),("'re",'are'),("'ll",'will'),("'m",'am'),("'d",'would')):
        if value.endswith(suffix):return [value[:-len(suffix)],tail]
    return [value]


def build_transcript(canonical: str, asr: str, protected_units: set[int] | None=None) -> dict:
    """Apply whole-word structural ASR edits, retain canonical substitutions/units."""
    protected_units=protected_units or set()
    canonical=expanded_transcript(canonical);asr=expanded_transcript(asr).replace('’',"'")
    units=sentence_units(canonical,False)
    cw=[];ca=[];co=[];cu=[]
    for unit in units:
        for word,_,_ in transcript_words(unit['text']):
            i=len(cw);cw.append(word);cu.append(unit['i']+1)
            for atom in atoms(word):ca.append(atom);co.append(i)
    aw=[w for w,_,_ in transcript_words(asr)];aa=[];ao=[]
    for i,word in enumerate(aw):
        for atom in atoms(word):aa.append(atom);ao.append(i)
    # Minimum word edit distance. On equal-cost paths, prefer a same-position
    # substitution over delete+insert so canonical substitutions stay canonical.
    cost=[list(range(len(aa)+1))]+[[i]+[0]*len(aa) for i in range(1,len(ca)+1)]
    for i in range(1,len(ca)+1):
        for j in range(1,len(aa)+1):
            cost[i][j]=min(cost[i-1][j-1]+(ca[i-1]!=aa[j-1]),cost[i-1][j]+1,cost[i][j-1]+1)
    chosen=[];i=len(ca);j=len(aa)
    while i or j:
        if i and j and cost[i][j]==cost[i-1][j-1]+(ca[i-1]!=aa[j-1]):
            chosen.append((ca[i-1],co[i-1],ao[j-1] if ca[i-1]==aa[j-1] else None,cu[co[i-1]]));i-=1;j-=1
        elif i and cost[i][j]==cost[i-1][j]+1:i-=1
        else:
            chosen.append((aa[j-1],None,ao[j-1],cu[co[max(0,i-1)]]));j-=1
    chosen.reverse()
    rendered=[];mapping=[];changes=[];word_index=0
    for unit in units:
        number=unit['i']+1;local=[x for x in chosen if x[3]==number];words=[];p=0
        if number in protected_units:
            text=unit['text']
        else:
            while p<len(local):
                _,ci,ai,_=local[p]
                # Complete ASR contractions can span multiple canonical words.
                if ai is not None and len(atoms(aw[ai]))>1:
                    size=len(atoms(aw[ai]));part=local[p:p+size]
                    if len(part)==size and [x[0] for x in part]==atoms(aw[ai]) and all(x[2]==ai for x in part):
                        words.append(aw[ai].strip('.,;:!?'));p+=size;continue
                # Expanded ASR form of a canonical contraction is also preserved.
                if ci is not None and len(atoms(cw[ci]))>1 and ai is not None:
                    size=len(atoms(cw[ci]));part=local[p:p+size]
                    if len(part)==size and all(x[1]==ci and x[2] is not None for x in part):
                        owners=list(dict.fromkeys(x[2] for x in part))
                        if len(owners)>1:
                            words.extend(aw[j].strip('.,;:!?') for j in owners);p+=size;continue
                if ci is not None:
                    words.append(re.sub(r"[.!?;:][\"']*$",'',cw[ci]))
                    p+=1
                    while p<len(local) and local[p][1]==ci:p+=1
                else:
                    words.append(aw[ai].strip('.,;:!?'));p+=1
                    while p<len(local) and local[p][1] is None and local[p][2]==ai:p+=1
            if not words:raise ValueError(f'Canonical unit {number} was entirely omitted; do not fabricate it')
            text=' '.join(words);text=text[0].upper()+text[1:]
            ending=re.search(r"([.!?;][\"']*|:)\s*$",unit['text'])
            text=text.rstrip('.!?;:')+(ending.group(1) if ending else '')
        before=[w for w,_,_ in transcript_words(unit['text'])]
        after=[w for w,_,_ in transcript_words(text)]
        for kind,a,b,c,d in difflib.SequenceMatcher(None,[norm(w) for w in before],[norm(w) for w in after],autojunk=False).get_opcodes():
            if kind in ('delete','replace'):
                changes.append({'unit':number,'operation':'omission','words':before[a:b]})
            if kind in ('insert','replace'):
                changes.append({'unit':number,'operation':'insertion','words':after[c:d]})
        mapping.append({'canonical_unit':number,'word_start':word_index,'word_end':word_index+len(after)-1,
                        'text':text,'protected_mumbling_unit':number in protected_units})
        word_index+=len(after);rendered.append(text)
    text=' '.join(rendered)+'\n'
    if len(sentence_units(text,False))!=len(units):raise ValueError('Canonical unit boundaries changed')
    return {'text':text,'units':mapping,'changes':changes}


def prepare_confirmed_transcripts(root: Path) -> dict:
    """Write only authorised human input artifacts from existing ASR/canonical files."""
    saved=root/'data/human/review/transcript_units.json'
    prior=json.loads(saved.read_text())['takes'] if saved.exists() else {}
    records={};lines=['# Applied transcript insertions/omissions','',
        'Recorder-authorised canonical + ASR structural-edit rule, 2026-10-12.',
        'ASR punctuation/substitutions are not ground truth. Contraction form changes are structural edits too.',
        'Canonical mumbling units remain unchanged. No listening or independent verbatim review is claimed.','']
    for text_id in ('gettysburg','reagan_challenger'):
        source=root/'data/transcripts/canonical'/f'{text_id}.txt'
        canonical=expanded_transcript(source.read_text())
        if text_id=='reagan_challenger':canonical=' '.join(u['text'] for u in sentence_units(canonical,False)[:17])
        for n in range(1,5):
            rid=f'{text_id}__user__take{n:02d}';draft=root/'data/human/asr_drafts'/f'{rid}.txt'
            protected={7 if text_id=='gettysburg' else 9} if n==3 else set()
            result=build_transcript(canonical,draft.read_text(),protected)
            target=root/'data/human/transcripts'/f'{rid}.txt';target.parent.mkdir(parents=True,exist_ok=True)
            contents='# source: recorder-authorised canonical/ASR rule, 2026-10-12\n# reviewed: rule-authorised, not independently verbatim-verified\n'+result['text']
            if target.exists() and target.read_text()!=contents:
                if hashlib.sha256(target.read_bytes()).hexdigest()!=prior.get(rid,{}).get('transcript_sha256'):
                    raise ValueError(f'Existing transcript differs from generated provenance: {target}; preserve recorder edits')
            target.write_text(contents)
            result['canonical_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
            result['asr_sha256']=hashlib.sha256(draft.read_bytes()).hexdigest()
            result['transcript_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
            records[rid]=result;lines.extend(['## '+rid,''])
            lines.extend(f'- Unit {c["unit"]}, {c["operation"]}: '+ ' '.join(c['words']) for c in result['changes'])
            if not result['changes']:lines.append('No applied insertions/omissions.')
            lines.append('')
    folder=root/'data/human/review';folder.mkdir(parents=True,exist_ok=True)
    _write_json(folder/'transcript_units.json',{'schema':'human-canonical-units/v1','takes':records})
    (folder/'TRANSCRIPT_DIFFS.md').write_text('\n'.join(lines))
    return records
