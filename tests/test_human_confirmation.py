"""Rule-authorised inputs and grounding; all audio here is synthetic test data."""
import json
import numpy as np
import pytest
import soundfile as sf


def test_rule_transcript_keeps_substitutions_but_applies_structural_edits():
    from speecheval.human_recording_inputs import build_transcript
    result = build_transcript("We see the blue sky. They have won.",
                              "We see red sky. They have have won.")
    assert result['text'] == "We see blue sky. They have have won.\n"
    assert result['units'][0]['word_end'] == 3
    assert result['units'][1]['word_start'] == 4
    assert [c['operation'] for c in result['changes']] == ['omission', 'insertion']


def test_mumbling_unit_is_canonical_and_asr_punctuation_does_not_renumber():
    from speecheval.human_recording_inputs import build_transcript
    result = build_transcript("In a larger sense, we cannot go. They speak clearly.",
                              "In a larger... sense we cannot go they don't speak.", {2})
    assert result['text'] == "In a larger sense, we cannot go. They speak clearly.\n"
    assert len(result['units']) == 2


def test_asr_contractions_follow_asr_without_changing_canonical_units():
    from speecheval.human_recording_inputs import build_transcript
    result = build_transcript("We've never lost. We are ready.", "We have never lost we’re ready")
    assert result['text'] == "We have never lost. We're ready.\n"
    assert len(result['units']) == 2


def test_equal_length_substitution_block_keeps_canonical_words():
    from speecheval.human_recording_inputs import build_transcript
    result=build_transcript('To dedicate a portion.', 'To a dedicated portion.')
    assert result['text']=='To dedicate a portion.\n'
    assert result['changes']==[]


def test_explicit_exclusion_is_not_clean_truth(tmp_path):
    from speecheval.human_takes import validate_human_inputs
    raw=tmp_path/'data/human/raw';raw.mkdir(parents=True)
    rid='gettysburg__user__take04'
    sf.write(raw/f'{rid}.wav', np.ones(1600)*.1, 16000)
    (raw.parent/'CONSENT.md').write_text('Synthetic fixture consent.')
    transcripts=raw.parent/'transcripts';transcripts.mkdir()
    (transcripts/f'{rid}.txt').write_text('We read.')
    detail={'flaws':None,'slips':'unknown','excluded_from_scoring':True,
            'exclusion_reason':'spontaneous mixed reading, flaws unknown'}
    (raw/'notes.md').write_text('```json\n'+json.dumps({'takes':{rid:detail}})+'\n```')
    cases, notes=validate_human_inputs(tmp_path)
    assert notes['takes'][rid]['flaws'] is None
    assert len(cases)==1
    detail['excluded_from_scoring']=False
    (raw/'notes.md').write_text('```json\n'+json.dumps({'takes':{rid:detail}})+'\n```')
    with pytest.raises(ValueError,match='flaws'): validate_human_inputs(tmp_path)


def test_canonical_closing_quotes_do_not_duplicate_sentence_endings():
    from speecheval.human_recording_inputs import build_transcript
    result=build_transcript("He said ``Meet it with joy.'' They spoke.",
                            'He said meet it with joy they spoke')
    assert result['text']=="He said ``Meet it with joy.'' They spoke.\n"
    assert len(result['units'])==2


def test_localized_labels_use_fixed_word_anchors_not_whole_sentence():
    from speecheval.human_grounding import grounded_regions
    words=[{'i':i,'text':w,'norm':w,'start':s,'end':e,'sentence':5}
           for i,(w,s,e) in enumerate([('in',1,1.1),('a',1.1,1.2),('larger',1.2,1.6),('sense',2.6,3)])]
    alignment={'duration_s':4,'words':words}
    units=[{'canonical_unit':6,'word_start':0,'word_end':3}]
    primary,secondary,basis=grounded_regions('gettysburg__user__take02',
        {'flaws':[{'type':'awkward_pause','sentence':6}]},alignment,units)
    assert primary[0]['start']==1.6 and primary[0]['end']==2.6
    assert secondary[0]['start']==1 and secondary[0]['end']==3
    assert 'larger|sense' in basis[0]
    words[3]['norm']='other'
    with pytest.raises(ValueError,match='anchor'):grounded_regions('gettysburg__user__take02',
        {'flaws':[{'type':'awkward_pause','sentence':6}]},alignment,units)


def test_missing_pause_zero_gap_has_boundary_event_and_secondary_is_one_to_one():
    from speecheval.human_grounding import grounded_regions, compare_grounded
    words=[{'i':0,'text':'here.','norm':'here','start':1,'end':2,'sentence':7},
           {'i':1,'text':'It','norm':'it','start':2,'end':3,'sentence':8}]
    units=[{'canonical_unit':8,'word_start':0,'word_end':0},
           {'canonical_unit':9,'word_start':1,'word_end':1}]
    truth,unit_truth,_=grounded_regions('gettysburg__user__take03',
        {'flaws':[{'type':'missing_pause','sentence':8}]},{'words':words,'duration_s':4},units)
    assert truth[0]['start']==1.985 and truth[0]['end']==2.015
    predicted=[{'type':'missing_pause','start':1.98,'end':2.02}]*2
    scores=compare_grounded(predicted,truth,unit_truth)
    assert scores['primary']=={'hits':1,'misses':0,'false_positives':1}
    assert scores['secondary']=={'hits':1,'misses':0,'false_positives':1}
    predicted=[{'type':'missing_pause','start':1.1,'end':1.2}]
    scores=compare_grounded(predicted,truth,unit_truth)
    assert scores['primary']['hits']==0 and scores['secondary']['hits']==1


def test_trailing_four_words_and_dragging_phrase_are_localized():
    from speecheval.human_grounding import grounded_regions
    words=[{'i':i,'text':w,'norm':w,'start':i,'end':i+.5,'sentence':7 if i<6 else 8}
           for i,w in enumerate(['we','remember','what','they','did','here','have','thus','far'])]
    units=[{'canonical_unit':8,'word_start':0,'word_end':5},
           {'canonical_unit':9,'word_start':6,'word_end':8}]
    a,_,_=grounded_regions('gettysburg__user__take02',{'flaws':[{'type':'too_quiet','sentence':8}]},
                          {'words':words,'duration_s':10},units)
    assert (a[0]['start'],a[0]['end'])==(2,5.5)
    b,_,_=grounded_regions('gettysburg__user__take03',{'flaws':[{'type':'dragging','sentence':9}]},
                          {'words':words,'duration_s':10},units)
    assert (b[0]['start'],b[0]['end'])==(6,8.5)
