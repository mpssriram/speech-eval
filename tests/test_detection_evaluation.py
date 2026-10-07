"""Hand-derived temporal matching and file-level uncertainty estimates."""
import pytest
from speecheval import evaluate as e


def region(kind,a,b,severity=3):return {'type':kind,'start':a,'end':b,'severity':severity}


def test_pause_greedy_uses_iou_after_distance_eligibility():
    truth=[region('awkward_pause',0.,1.)]
    predictions=[region('awkward_pause',.4,.6),region('awkward_pause',0.,1.2)]
    assert e.match_regions(predictions,truth)==[(1,0)]


def test_type_confusion_counts_only_wrong_types():
    metrics=e.detection_metrics([{'predicted':[region('rushing',0,1)],
                                 'truth':[region('rushing',0,1)],'duration_s':2}])
    assert metrics['confusion']['rushing']['rushing']==0


def test_iou_and_one_to_one_matching_do_not_double_count():
    assert e.temporal_iou(region('rushing',0,2),region('rushing',1,3))==pytest.approx(1/3)
    predicted=[region('rushing',0,2),region('rushing',.1,1.9)]
    truth=[region('rushing',0,2)]
    assert e.match_regions(predicted,truth)==[(0,0)]
    result=e.detection_metrics([{'predicted':predicted,'truth':truth,'duration_s':10.}])
    assert result['overall']['precision']==.5 and result['overall']['recall']==1.
    assert result['overall']['f1']==pytest.approx(2/3)


def test_pause_distance_matches_even_without_overlap():
    predicted=[region('missing_pause',1.,1.03)]
    assert e.match_regions(predicted,[region('missing_pause',1.2,1.23)])==[(0,0)]
    assert e.match_regions(predicted,[region('missing_pause',1.3,1.33)])==[]
    assert e.match_regions(predicted,[region('awkward_pause',1.,1.03)])==[]


def test_clean_false_alarms_use_minutes_not_file_count():
    items=[{'predicted':[region('rushing',0,1)],'truth':[],'duration_s':30.,'clean':True},
           {'predicted':[region('rushing',0,1)],'truth':[region('rushing',0,1)],'duration_s':60.,'clean':False}]
    assert e.detection_metrics(items)['overall']['false_alarms_per_minute']==2.


def test_file_bootstrap_replays_and_absent_evidence_is_not_perfect():
    items=[{'predicted':[],'truth':[region('rushing',0,1)],'duration_s':10.},
           {'predicted':[region('rushing',0,1)],'truth':[region('rushing',0,1)],'duration_s':10.}]
    a=e.bootstrap_detection(items,resamples=100,seed=4)
    assert a==e.bootstrap_detection(items,resamples=100,seed=4)
    assert a['overall']['recall_95ci']==[0.,1.]
    assert a['monotone']['recall_95ci'] is None
