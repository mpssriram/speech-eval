"""Known signed shifts, paired samples, dictionary coverage and QA edge rules."""
import pytest
from speecheval import alignment_analysis as a


def test_signed_bias_is_removed_per_edge_not_from_absolute_errors():
    result=a.signed_summary([.010,.020,.030],[-.010,-.020,-.030])
    assert result['start']=={'mean_ms':20.,'median_ms':20.}
    assert result['end']=={'mean_ms':-20.,'median_ms':-20.}
    assert result['bias_corrected_pooled']['median_ms']==10.


def test_paired_bootstrap_keeps_start_end_pairs_and_sign():
    pairs=[{'recording_id':'a','mfa_start':.01,'mfa_end':.02,'whisperx_start':.03,'whisperx_end':.04}]*3
    result=a.paired_bootstrap(pairs,seed=7,resamples=10000)
    assert result['start']['mean_difference_ms']==pytest.approx(-20.)
    assert result['pooled']['mean_ci95_ms']==pytest.approx([-20.,-20.])
    assert result==a.paired_bootstrap(pairs,seed=7,resamples=10000)


def test_stop_initial_uses_phones_not_spelling_and_unknown_is_explicit():
    lexicon={'cat':[['K','AE1','T']],'chair':[['CH','EH1','R']],'the':[['DH','AH0']]}
    assert a.initial_class('Cat!',lexicon)=='stop'
    assert a.initial_class('chair',lexicon)=='other'
    assert a.initial_class('absent',lexicon)=='unknown'


def test_dictionary_canonicalization_preserves_variants_and_rejects_missing_words():
    from speecheval.align.mfa import canonical_dictionary
    assert canonical_dictionary('z\tZ\na  A\na\tA\nz\tS\n',{'a','z'})=='a\tA\nz\tS\nz\tZ\n'
    with pytest.raises(ValueError,match='missing'):
        canonical_dictionary('a A\n',{'a','z'})


def test_qa_excludes_sentence_final_long_word_and_counts_occurrences():
    from speecheval.alignment_qa import qa_row
    payload={'recording_id':'a','duration_s':4.,'uncertain_words':[],
             'words':[{'i':0,'start':0.,'end':.02,'norm':'x'},
                      {'i':1,'start':.02,'end':2.,'norm':'x'},
                      {'i':2,'start':2.,'end':4.,'norm':'y'}],
             'sentences':[{'word_end':2}], 'warnings':[{'type':'oov','text':'x'}]}
    row=qa_row(payload,'')
    assert row['short_words']==1 and row['long_words']==1
    assert row['oov']==2 and row['speech_rate_wps']==.75


def test_custom_dictionary_gate_rejects_worse_mean_even_with_equal_median():
    before={k:{'median_ms':20.,'mean_ms':30.} for k in ('start','end','overall')}
    after={k:dict(v) for k,v in before.items()};after['oov_words']=0
    assert a.custom_acceptable(before,after)
    after['start']['mean_ms']=31.
    assert not a.custom_acceptable(before,after)


def test_promotion_copies_only_recording_artifacts_not_source_provenance(tmp_path):
    from speecheval.align.pipeline import promote_outputs
    directory=tmp_path/'data/alignment/mfa';directory.mkdir(parents=True)
    directory.joinpath('a.json').write_text('recording')
    directory.joinpath('a.TextGrid').write_text('boundaries')
    directory.joinpath('provenance.json').write_text('not a recording')
    promote_outputs(tmp_path,'mfa',['a'])
    assert (tmp_path/'data/alignment/a.json').read_text()=='recording'
    assert not (tmp_path/'data/alignment/provenance.json').exists()


def test_dictionary_adoption_rejects_failed_or_changed_artifact_evidence():
    from speecheval.align.mfa import require_adoption
    binding={'dictionary':'sha1','mfa/gold.json':'sha2'}
    require_adoption(binding,{'accepted':True,'artifact_hashes':dict(binding)})
    with pytest.raises(ValueError,match='rejected'):
        require_adoption(binding,{'accepted':False,'artifact_hashes':dict(binding)})
    with pytest.raises(ValueError,match='stale'):
        require_adoption(dict(binding,dictionary='changed'),{'accepted':True,'artifact_hashes':dict(binding)})
