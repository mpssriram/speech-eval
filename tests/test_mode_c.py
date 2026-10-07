"""Known-answer good-speaker norms and number heuristics."""
import numpy as np
import pytest
from speecheval import mode_c as c


def test_norm_summary_has_hand_computed_robust_spread():
    result=c.norm_summary([1.,2.,3.,4.,5.])
    assert result['median']==3. and result['robust_sd']==pytest.approx(1.4826)
    assert result['n']==5 and result['percentiles']['50']==3.


@pytest.mark.parametrize('text,expected',[('We need 10,000 jobs.',True),('We need ten thousand jobs.',True),
    ('Growth is 45%.',True),('We raised ₹2 crore.',True),('It is one of the best.',False)])
def test_number_heuristic_ignores_indefinite_one(text,expected):
    assert bool(c.number_spans(text.split())) is expected


def test_rate_outlier_flags_exact_sentence_only():
    sentence={'i':0,'start':1.,'end':4.,'word_start':0,'word_end':3,'n_words':4,
              'articulation_rate_syl_s':float(np.exp(3.)), 'f0_st_range':1.,
              'final_int_drop_db':0.,'pause_after_s':np.nan,'invalid_evidence':False}
    norms={'features':{'rate':{'median':0.,'robust_sd':1.,'percentiles':{'25':-1.,'75':1.}}}}
    settings={'mode_c':{'k':{'rate':2.}},'severity_z_bins':[2.,2.75,3.5,4.5,6.]}
    result=c.sentence_regions([sentence],norms,settings)
    assert len(result)==1 and result[0]['type']=='rushing'
    assert (result[0]['start'],result[0]['end'])==(1.,4.)


def test_key_moments_are_guidelines_not_score_regions():
    words=[{'i':i,'text':w,'sentence':0,'start':i*.2,'end':i*.2+.1} for i,w in enumerate('We need ten thousand jobs.'.split())]
    alignment={'words':words,'sentences':[{'i':0,'word_start':0,'word_end':4,'start':0.,'end':.9}]}
    import pandas as pd
    word_table=pd.DataFrame([{'i':i,'start':w['start'],'end':w['end'],'dur_s':.1,'syllables':1,'pause_before_s':0.} for i,w in enumerate(words)])
    sentence={'i':0,'articulation_rate_syl_s':5.,'final_int_drop_db':-5.,'invalid_evidence':False}
    norms={'features':{'rate':{'median':float(np.log(5.)),'robust_sd':1.}}}
    result=c.key_checks(alignment,[sentence],word_table,norms,{})
    assert {item['kind'] for item in result}=={'number_rate','number_pause','strong_ending','first_sentence'}
    assert all('passed' in item and 'guideline' in item['message'] for item in result)


def test_sentence_metrics_do_not_double_count_duplicate_flags():
    item={'truth':{('rushing',0),('rushing',1)},'predicted':{('rushing',0),('rushing',2)},'clean':False,'duration_s':60.}
    result=c.sentence_metrics([item])
    assert result['rushing']['precision']==.5 and result['rushing']['recall']==.5
    assert result['rushing']['f1']==.5


def test_supported_false_type_is_not_hidden_by_truth_types():
    alignment={'words':[{'sentence':0} for _ in range(4)]}
    predictions=[{'type':'rushing','word_start':0},{'type':'dragging','word_start':1}]
    result=c.evaluation_pairs(alignment,predictions,{0})
    assert result=={('rushing',0),('dragging',0)}


def test_uncertain_sentence_mask_excludes_both_systems_evidence():
    alignment={'words':[{'sentence':0} for _ in range(5)],'uncertain_words':[4]}
    sentences=[{'i':0,'n_words':5,'invalid_evidence':True}]
    valid=c.evaluation_sentence_mask(alignment,sentences)
    assert valid==set()
    assert c.evaluation_pairs(alignment,[{'type':'rushing','word_start':0}],valid)==set()


def test_mode_c_gate_rejects_empty_phase7_artifacts(tmp_path):
    directory=tmp_path/'data/review';directory.mkdir(parents=True)
    for name in ('severity_validation','repro_validation'):(directory/f'{name}.json').write_text('{}')
    with pytest.raises(ValueError,match='Phase 7'):c.validate_phase7_evidence(tmp_path)


def test_key_evidence_changes_content_addressed_analysis_id():
    assert c.analysis_identity({'audio':'same'},[{'passed':True}])!=c.analysis_identity({'audio':'same'},[{'passed':False}])
