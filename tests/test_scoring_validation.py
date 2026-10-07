"""Known-answer ordinal score behavior and reproducibility diagnostics."""
from speecheval import validation as v
import pytest


def test_monotonic_summary_does_not_treat_constant_scores_as_correlation():
    result=v.monotonic_summary([[10.,9.,8.,7.,6.],[10.,10.,10.,10.,10.]])
    assert result['median_spearman']==pytest.approx(-1.)
    assert result['non_increasing_percent']==100.
    assert result['constant_series']==1 and result['series']==2


def test_monotonic_summary_reports_increasing_score_failure():
    result=v.monotonic_summary([[6.,7.,8.,9.,10.]])
    assert result['median_spearman']==pytest.approx(1.) and result['non_increasing_percent']==0.


def test_repro_diff_identifies_first_actual_field():
    assert v.first_difference({'scores':{'pace':7.}},{'scores':{'pace':6.}})=='$.scores.pace'
    assert v.first_difference({'scores':{'pace':7.}},{'scores':{'pace':7.}}) is None


def test_repro_uses_second_analysis_output_when_id_changes(tmp_path):
    import json
    directory=tmp_path/'data/analyses';directory.mkdir(parents=True)
    a={'analysis_id':'first','scores':{'pace':7.}};b={'analysis_id':'second','scores':{'pace':6.}}
    (directory/'first.json').write_text(json.dumps(a));(directory/'second.json').write_text(json.dumps(b))
    result=v.compare_analysis_outputs(tmp_path,a,b,(directory/'first.json').read_bytes())
    assert not result['identical'] and result['first_sha256']!=result['second_sha256']


def test_scoring_freeze_rejects_empty_phase6_artifact(tmp_path):
    directory=tmp_path/'data/review';directory.mkdir(parents=True)
    (directory/'final_evaluation.json').write_text('{}')
    with pytest.raises(ValueError,match='frozen'):v.scoring_freeze(tmp_path)


def test_coverage_includes_completely_absent_series():
    complete,missing=v.coverage_series([('source','rushing')],{})
    assert complete=={} and missing==[{'source':'source','type':'rushing','missing_severities':[1,2,3,4,5]}]
