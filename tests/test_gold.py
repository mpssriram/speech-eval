"""Gold templates must remain deterministic, unbiased and explicitly unreviewed."""
import json
import pytest
from speecheval import gold


def test_selects_highest_lufs_clean_gettysburg_with_stable_tie():
    rows=[{'recording_id':'bad','text_id':'gettysburg','qa_flags':'clipping','integrated_lufs':'-10'},
          {'recording_id':'b','text_id':'gettysburg','qa_flags':'','integrated_lufs':'-20'},
          {'recording_id':'a','text_id':'gettysburg','qa_flags':'','integrated_lufs':'-20'},
          {'recording_id':'quiet','text_id':'gettysburg','qa_flags':'','integrated_lufs':'-30'}]
    assert gold.choose_recordings(rows)==['a','jfk_rice__jfk__orig','reagan_challenger__reagan__orig']


def fixture_alignment(rid='sample', name='mfa'):
    return {'schema':'alignment/v1','recording_id':rid,'aligner':{'name':name},
            'audio':f'data/audio/hq/{rid}.wav','transcript':f'data/transcripts/as_spoken/{rid}.txt',
            'sentences':[], 'duration_s':45.,'uncertain_words':[0],'warnings':[{'type':'interpolated','word':1}],
            'words':[{'i':i,'text':f'w{i}','norm':f'w{i}','sentence':0,'start':float(i),'end':i+.3} for i in range(42)]}


def test_word_selection_excludes_uncertain_and_uses_both_duration_thresholds():
    a=fixture_alignment();b=fixture_alignment()
    b['words'][2]['end']=2.1
    candidates=gold.candidate_boundaries(a,b)
    assert len(candidates)==20
    assert candidates[0]['word_index']==3
    assert candidates[-1]['word_index']==41
    assert all(x['word_index'] not in (0,1,2) for x in candidates)


def test_average_boundaries_padded_and_clipped_without_bias():
    a=fixture_alignment();b=fixture_alignment()
    a['uncertain_words']=b['uncertain_words']=[];a['warnings']=b['warnings']=[]
    b['words'][0]['start']=.1;b['words'][0]['end']=.5
    intervals=gold.candidate_boundaries(a,b)
    assert intervals[0]['start']==0.
    assert intervals[0]['end']==.55
    assert intervals[1]['word_index']==2


def test_rejects_insufficient_eligible_words():
    a=fixture_alignment();a['words']=a['words'][:19]
    with pytest.raises(ValueError,match='20'):
        gold.candidate_boundaries(a,a)


def test_prepare_writes_only_todo_and_reuses_templates(tmp_path):
    from praatio import textgrid
    (tmp_path/'configs').mkdir();(tmp_path/'configs/default.yaml').write_text('paths:\n  gold: data/gold/alignment\n  alignment: data/alignment\n')
    manifest=tmp_path/'data/manifest';manifest.mkdir(parents=True)
    manifest.joinpath('recordings.csv').write_text('recording_id,text_id,qa_flags,integrated_lufs\ngettysburg__test__orig,gettysburg,,-20\njfk_rice__jfk__orig,jfk_rice,,-20\nreagan_challenger__reagan__orig,reagan_challenger,,-20\n')
    for name in ('mfa','whisperx'):
        path=tmp_path/'data/alignment'/name;path.mkdir(parents=True)
        for rid in ('gettysburg__test__orig','jfk_rice__jfk__orig','reagan_challenger__reagan__orig'):
            path.joinpath(rid+'.json').write_text(json.dumps(fixture_alignment(rid,name)))
    gold.prepare_gold(tmp_path)
    todo=tmp_path/'data/gold/alignment/todo'
    assert len(list(todo.glob('*.TextGrid')))==3
    tg=textgrid.openTextgrid(str(todo/'gettysburg__test__orig.TextGrid'),includeEmptyIntervals=False)
    assert tg.tierNames==('gold',) and len(tg.getTier('gold').entries)==20
    assert not list(todo.parent.glob('*.TextGrid'))
    before={p.name:p.read_bytes() for p in todo.iterdir()}
    gold.prepare_gold(tmp_path)
    assert before=={p.name:p.read_bytes() for p in todo.iterdir()}
    # Existing human edits, even in todo, must never be silently overwritten.
    edited=todo/'gettysburg__test__orig.TextGrid';edited.write_text('manual edits')
    with pytest.raises(ValueError,match='changed'):
        gold.prepare_gold(tmp_path)
    assert edited.read_text()=='manual edits'


@pytest.mark.parametrize('field,value',[('recording_id','wrong_recording'),('aligner',{'name':'mfa'})])
def test_rejects_misfiled_alignment_before_writing_templates(tmp_path,field,value):
    (tmp_path/'configs').mkdir();(tmp_path/'configs/default.yaml').write_text('paths:\n  gold: data/gold/alignment\n  alignment: data/alignment\n')
    manifest=tmp_path/'data/manifest';manifest.mkdir(parents=True)
    manifest.joinpath('recordings.csv').write_text('recording_id,text_id,qa_flags,integrated_lufs\ngettysburg__test__orig,gettysburg,,-20\njfk_rice__jfk__orig,jfk_rice,,-20\nreagan_challenger__reagan__orig,reagan_challenger,,-20\n')
    for name in ('mfa','whisperx'):
        path=tmp_path/'data/alignment'/name;path.mkdir(parents=True)
        for rid in ('gettysburg__test__orig','jfk_rice__jfk__orig','reagan_challenger__reagan__orig'):
            payload=fixture_alignment(rid,name)
            if name=='whisperx' and rid=='gettysburg__test__orig':payload[field]=value
            path.joinpath(rid+'.json').write_text(json.dumps(payload))
    with pytest.raises(ValueError,match='identity'):
        gold.prepare_gold(tmp_path)
    assert not (tmp_path/'data/gold/alignment/todo').exists()
