"""One-shot test gate and fair severity cohorts on literal fixtures only."""
import copy
import pytest


def audit_fixture():
    metrics={'overall':{'f1':.25,'false_alarms_per_minute':.4}}
    config={'within_k':1.5}
    return {'split':'dev','history':[{'id':1,'metrics':metrics,'config':config}],
            'selected_id':1,'selected_metrics':metrics,'selected_config':config,
            'elapsed_seconds':10.,'v1_metrics':{'overall':{'f1':.15}}}


def test_failed_dev_guard_prevents_test_even_with_higher_f1():
    from speecheval.evaluate_v2 import validate_gate
    audit=audit_fixture()
    audit['selected_metrics']['overall']['false_alarms_per_minute']=.6
    with pytest.raises(ValueError,match='promotion'):validate_gate(audit)
    audit['selected_metrics']['overall']['false_alarms_per_minute']=.4
    validate_gate(audit)
    audit['selected_metrics']['overall']['f1']=.16
    with pytest.raises(ValueError,match='promotion'):validate_gate(audit)


def test_test_gate_refuses_selected_metrics_not_in_dev_history():
    from speecheval.evaluate_v2 import validate_gate
    audit=audit_fixture()
    audit['selected_metrics']=copy.deepcopy(audit['selected_metrics'])
    audit['selected_metrics']['overall']['f1']=.35
    with pytest.raises(ValueError,match='history'):validate_gate(audit)


def test_test_gate_refuses_selected_configuration_not_in_dev_history():
    from speecheval.evaluate_v2 import validate_gate
    audit=audit_fixture();audit['selected_config']={'within_k':9.}
    with pytest.raises(ValueError,match='history'):validate_gate(audit)


def test_test_gate_requires_the_best_guard_passing_dev_configuration():
    from speecheval.evaluate_v2 import validate_gate
    audit=audit_fixture()
    audit['history'].append({'id':2,'config':{'within_k':2.},
        'metrics':{'overall':{'f1':.30,'false_alarms_per_minute':.4}}})
    with pytest.raises(ValueError,match='objective'):validate_gate(audit)


def test_config_limit_is_enforced_before_test():
    from speecheval.evaluate_v2 import validate_gate
    with pytest.raises(ValueError,match='configuration'):
        validate_gate({'split':'dev','history':[{'id':i} for i in range(1,32)]})


def test_one_shot_test_marker_is_never_overwritten(tmp_path):
    from speecheval.evaluate_v2 import start_test_run
    start_test_run(tmp_path,'abc123')
    marker=tmp_path/'data/review/detector_v2_test_started.json';before=marker.read_bytes()
    with pytest.raises(ValueError,match='already'):start_test_run(tmp_path,'another')
    assert marker.read_bytes()==before


def test_severity_strata_use_same_files_and_exclude_mixed_strengths():
    from speecheval.evaluate_v2 import severity_cohort
    clean={'recording_id':'clean','clean':True,'truth':[]}
    one={'recording_id':'one','clean':False,'truth':[{'severity':1}]}
    mixed={'recording_id':'mixed','clean':False,'truth':[{'severity':1},{'severity':2}]}
    empty={'recording_id':'masked','clean':False,'truth':[]}
    assert [v['recording_id'] for v in severity_cohort([clean,one,mixed,empty],1)]==['clean','one']


def test_reproduction_refuses_changed_frozen_code(tmp_path):
    from speecheval.evaluate_v2 import verify_hashes
    p=tmp_path/'code.py';p.write_text('changed')
    with pytest.raises(ValueError,match='differs'):verify_hashes(tmp_path,{'code.py':'bad-sha'})
