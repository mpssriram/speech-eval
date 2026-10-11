"""Confirmed orchestration uses synthetic dictionaries, never recorder ratings."""
import json
from speecheval import human_confirmed_workflow as flow


def test_routes_keep_unknown_take04_out_of_but_in_a_and_c():
    assert flow.modes_for({'take_number':4},{'excluded_from_scoring':True})==('A','C')
    assert flow.modes_for({'take_number':2},{'flaws':[]})==('A','B')
    assert flow.modes_for({'take_number':1},{'flaws':[]})==('A',)


def test_pools_exclude_unknown_and_previous_reference_durations():
    scores={'hits':1,'misses':2,'false_positives':3}
    row={'detector':'v1','mode':'B','excluded_from_scoring':False,
         'duration_s':60,'labelled_flaws':3,
         'comparison':{k:scores for k in flow.MATCHERS}}
    excluded={**row,'duration_s':600,'excluded_from_scoring':True,
              'labelled_flaws':None,'comparison':None}
    pool=flow.pooled([row,excluded])[0]
    assert pool['current_takes']==1 and pool['duration_min']==1
    assert pool['labelled_flaws']==3 and pool['false_positives_per_min']==3


def test_publish_v2_is_deterministic_preserves_scientific_result(tmp_path):
    result={'analysis_id':'abcdef123456','detector':{'version':'post-hoc-v2'},'regions':[]}
    source={'analysis_id':'123456','created_order':100}
    first=flow.publish_v2(tmp_path,result,source)
    path=tmp_path/'data/app/jobs'/f"{first['analysis_id']}.json"
    before=path.read_bytes()
    second=flow.publish_v2(tmp_path,result,source)
    assert first==second and before==path.read_bytes()
    assert json.loads(before)['analysis']==result
    assert 'post-hoc-v2' in first['identity']['detector']


def test_excluded_row_has_no_accuracy_or_clean_truth(tmp_path):
    result={'recording_id':'synthetic','mode':'A','duration_s':2,
            'regions':[{'type':'rushing','start':0,'end':1}],
            'scores':{},'warnings':[],'reference':{'n_readers':1},'detector':{}}
    row=flow.make_row(tmp_path,{'take_id':'gettysburg__user__take04'},
        {'flaws':None,'slips':'unknown','excluded_from_scoring':True,'exclusion_reason':'unknown flaws'},
        {'analysis_id':'123','analysis':result},{'words':[],'aligner':{'name':'mfa'}},
        [],{'trim_start_s':0,'trim_end_s':2},{},'v1','http://localhost:8080')
    assert row['comparison'] is None and row['labelled_flaws'] is None
    assert row['intended_regions'] is None and row['flag_count']==1


def test_partial_workflow_report_does_not_claim_complete_eight_take_evaluation():
    payload={'status':'incomplete','genuine_takes_processed':1,'results':[],'pooled':[],
             'blockers':['G03 anchor missing'],'input_freeze_commit':'synthetic',
             'confirmation_sha256':'synthetic'}
    report=flow.report_text(payload)
    assert 'INCOMPLETE' in report
    assert 'Eight genuine Voice Memos analysed' not in report
    assert '1 distinct take' in report
