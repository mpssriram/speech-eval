"""Dev-only threshold constraints and increasing ordinal severity cut points."""
import numpy as np
import pytest
from speecheval import calibration as c


def test_uncertain_truth_excludes_predicted_fragments_not_other_errors():
    excluded={'type':'rushing','start':1.,'end':4.,'word_start':2,'word_end':5}
    predictions=[{'type':'rushing','start':1.,'end':2.,'word_start':2,'word_end':3},
                 {'type':'monotone','start':6.,'end':7.,'word_start':7,'word_end':8}]
    assert c.exclude_uncertain_predictions(predictions,[excluded])==[predictions[1]]


def test_evaluation_input_identity_changes_with_data_not_only_commit(tmp_path):
    path=tmp_path/'data/labels';path.mkdir(parents=True)
    (path/'one.json').write_text('{"severity":1}')
    first=c.evaluation_input_identity(tmp_path)
    (path/'one.json').write_text('{"severity":5}')
    assert c.evaluation_input_identity(tmp_path)!=first


def test_result_report_marks_unavailable_human_evidence(tmp_path):
    result={'evaluated_commit':'abc123','learned_detector':'not trained',
            'human_A':{'status':'PENDING recordings and actual labels'},
            'human_B':{'status':'PENDING recordings and actual labels'},'settings':{}}
    c.write_results_report(tmp_path,result)
    text=(tmp_path/'reports/phase06_results.md').read_text()
    assert 'abc123' in text and 'Human-A' in text and 'PENDING' in text
    assert 'Human-B' in text and 'not trained' in text


def test_budget_repair_can_take_infeasible_intermediate_moves():
    from test_detect import table,config
    settings=config();settings['k']={kind:3.5 for kind in c.FLAW_TYPES}
    rows=table(8)
    for row,z in zip(rows,[4.,4.,4.,2.,2.,4.,4.,4.]):
        row['z']={'rate':z,'pitchvar':-z};row['values']['pitchvar']=0.;row['reference']['pitchvar']=1.
    items=[{'table':rows,'duration_s':240.,'truth':[],'clean':True}]
    repaired=c.repair_alarm_budget(items,settings)
    assert c.evaluate_settings(items,repaired)[0]['overall']['false_alarms_per_minute']<=.5


def test_calibration_freeze_rejects_changed_dev_evidence(tmp_path):
    import csv
    directory=tmp_path/'data/manifest';directory.mkdir(parents=True)
    with (directory/'dataset_index.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=['recording_id','split','audio_path','label_path'])
        writer.writeheader();writer.writerow({'recording_id':'x','split':'dev','audio_path':'audio.wav','label_path':'label.json'})
    (tmp_path/'audio.wav').write_bytes(b'original');(tmp_path/'label.json').write_text('{}')
    audit={'freeze':c.calibration_identity(tmp_path)}
    (tmp_path/'label.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='calibration'):c.validate_calibration_freeze(tmp_path,audit)


def test_final_identity_includes_actual_audio_and_ignores_report_commit(tmp_path):
    directory=tmp_path/'data/audio/hq';directory.mkdir(parents=True)
    (directory/'clip.wav').write_bytes(b'original audio')
    first=c.evaluation_input_identity(tmp_path)
    (tmp_path/'reports').mkdir();(tmp_path/'reports/result.md').write_text('new report')
    assert c.evaluation_input_identity(tmp_path)==first
    (directory/'clip.wav').write_bytes(b'changed audio')
    assert c.evaluation_input_identity(tmp_path)!=first


def test_final_reuse_ignores_report_commit_but_refuses_changed_algorithm():
    previous={'evaluated_commit':'older','implementation':{'detector':'v1'},'inputs':{'audio':'same'}}
    assert c.reuse_final_result(previous,{'detector':'v1'},{'audio':'same'}) is previous
    with pytest.raises(ValueError,match='explicit'):
        c.reuse_final_result(previous,{'detector':'v2'},{'audio':'same'})


def test_threshold_selection_obeys_global_clean_alarm_budget():
    candidates=[{'k':1.5,'f1':.9,'false_alarms_per_minute':.6},
                {'k':2.,'f1':.8,'false_alarms_per_minute':.4},
                {'k':3.5,'f1':.8,'false_alarms_per_minute':.2}]
    assert c.choose_threshold(candidates)['k']==3.5
    for item in candidates:item['false_alarms_per_minute']=1.
    assert c.choose_threshold(candidates)['k']==3.5


def test_severity_fit_recovers_known_order_without_decreasing_bins():
    bins,score=c.fit_severity_bins([2.1,3.,4.,5.,7.],[1,2,3,4,5],[2.,2.75,3.5,4.5,6.])
    assert np.all(np.diff(bins)>0) and score==pytest.approx(1.)
    predicted=np.clip(np.searchsorted(bins,[2.1,3.,4.,5.,7.],side='right'),1,5)
    assert predicted.tolist()==[1,2,3,4,5]
