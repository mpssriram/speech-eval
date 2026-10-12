"""Report diagnostics must preserve frozen matching and excluded unknown labels."""
import pytest
from speecheval.human_demo_evidence import row_breakdown, pause_summary, hit_rows


def test_breakdown_uses_matched_prediction_indices_and_same_type():
    row = {'excluded_from_scoring': False, 'regions': [
        {'type': 'rushing', 'start': 0., 'end': 2.},
        {'type': 'missing_pause', 'start': 5., 'end': 5.03},
        {'type': 'awkward_pause', 'start': 8., 'end': 9.},
        {'type': 'rushing', 'start': 12., 'end': 13.}],
        'intended_regions': [{'type': 'rushing', 'start': 0., 'end': 3.}],
        'comparison': {'primary': {'hits': 1, 'misses': 0, 'false_positives': 3}}}
    result = row_breakdown(row)
    assert result['matched_pairs'] == [(0, 0)]
    assert result['false_positive_indices'] == [1, 2, 3]
    assert result['false_alarms_by_type']['rushing'] == 1
    assert result['false_alarms_by_type']['missing_pause'] == 1
    assert result['missing_pause_share'] == pytest.approx(1 / 3)
    assert result['rushing_share'] == pytest.approx(1 / 3)


def test_unknown_take_flags_are_not_false_alarms():
    result = row_breakdown({'excluded_from_scoring': True,
        'regions': [{'type': 'rushing', 'start': 1., 'end': 2.}],
        'intended_regions': None, 'comparison': None})
    assert result['false_alarms_by_type'] is None
    assert result['flags_by_type']['rushing'] == 1


def test_pause_summary_uses_selected_excerpt_not_full_recording():
    alignment = {'duration_s': 100., 'words': [
        {'start': 1., 'end': 2.}, {'start': 2.5, 'end': 3.},
        {'start': 3., 'end': 4.}, {'start': 80., 'end': 90.}]}
    result = pause_summary(alignment, 0, 2)
    assert result == {'aligned_span_s': 3., 'interword_pause_s': .5,
                      'pause_fraction': 1 / 6, 'word_count': 3}


def test_hit_rows_quote_dashboard_explanation_not_raw_scientific_text():
    row = {'take_id':'example','detector':'v1','mode':'B','job_id':'job',
        'dashboard_url':'http://localhost/results/job','excluded_from_scoring':False,
        'regions':[{'type':'awkward_pause','start':1.,'end':2.,'explanation':'raw 6e-18'}],
        'intended_regions':[{'type':'awkward_pause','start':1.1,'end':2.1}],
        'comparison':{'primary':{'hits':1,'misses':0,'false_positives':0}}}
    shown = [{'type':'awkward_pause','start':1.,'end':2.,'explanation':'raw 6e-18',
              'display_explanation':'where your previous take does not pause'}]
    hits = hit_rows(row, shown)
    assert len(hits) == 1
    assert hits[0]['explanation'] == 'where your previous take does not pause'
    assert hits[0]['detected_interval_s'] == [1.,2.]
    assert hits[0]['label_interval_s'] == [1.1,2.1]
    with pytest.raises(ValueError,match='Dashboard intervals differ'):
        hit_rows(row, [{**shown[0],'end':3.}])
