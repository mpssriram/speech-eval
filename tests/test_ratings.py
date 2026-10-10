"""Temporary hand-derived ratings test mathematics, not real human evidence."""
import csv
import pytest


def key_fixture():
    return {'clips': {f'{n}.flac': {'duration_s':10, 'system':{'scores':{'overall':n}},
        'truth':[] if n==1 else [{'type':'rushing','start':2,'end':3}]} for n in (1,2,3)}}


def test_perfect_ranks_and_inverted_raters_have_expected_correlations():
    from speecheval.ratings import agreement
    ratings=[{'rater_id':'a','clip':f'{n}.flac','overall':n,'flaw_type':'none' if n==1 else 'rushing','flaw_time_s':'' if n==1 else '2'} for n in (1,2,3)]
    result=agreement(key_fixture(),ratings)
    assert result['system_vs_mean_human']['rho']==1
    assert result['human_vs_human']['mean_pairwise_rho'] is None
    ratings += [{**r,'rater_id':'b','overall':4-r['overall']} for r in ratings.copy()]
    result=agreement(key_fixture(),ratings)
    assert result['human_vs_human']['mean_pairwise_rho']==-1
    assert result['system_vs_mean_human']['rho'] is None
    assert result['flaw_type_agreement']['human_vs_injection_key']['fraction']==1
    assert result['flaw_type_agreement']['human_vs_human']['fraction']==1


def test_partial_forms_keep_coverage_and_invalid_scores_fail(tmp_path):
    from speecheval.ratings import read_ratings
    path=tmp_path/'ratings.csv'
    def write(rows):
        with path.open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=['rater_id','clip','overall','flaw_type','flaw_time_s']);w.writeheader();w.writerows(rows)
    row={'rater_id':'a','clip':'2.flac','overall':'4','flaw_type':'rushing','flaw_time_s':'2.5'}
    write([row,{'rater_id':'','clip':'1.flac','overall':'','flaw_type':'','flaw_time_s':''}])
    assert len(read_ratings(path,key_fixture()))==1
    for changed in [{'overall':'6'},{'overall':'NaN'},{'overall':'2.5'},{'flaw_type':'made_up'},
                    {'flaw_time_s':'11'},{'rater_id':''},{'clip':'unknown.flac'},{'flaw_type':'none'}]:
        write([{**row,**changed}])
        with pytest.raises(ValueError):read_ratings(path,key_fixture())
    write([row,row])
    with pytest.raises(ValueError,match='Duplicate'):read_ratings(path,key_fixture())


def test_clip_scores_exclude_invisible_regions_and_use_clip_speech_duration():
    import yaml
    from speecheval.ratings import clip_measurement
    from pathlib import Path
    rubric=yaml.safe_load((Path.cwd()/'configs/rubric.yaml').read_text())
    analysis={'analysis_id':'id','regions':[{'type':'rushing','start':9,'end':12,'severity':3},
                                           {'type':'mumbling','start':30,'end':40,'severity':5}]}
    measured=clip_measurement(analysis,{'words':[{'start':1,'end':39}]},10,20,rubric)
    assert measured['scores']['pace']==4
    assert measured['scores']['clarity']==10
    assert measured['regions'][0]['start']==0 and measured['regions'][0]['end']==2
    assert measured['speech_duration_s']==10


def test_multiple_flaw_times_keep_their_corresponding_type_order(tmp_path):
    from speecheval.ratings import read_ratings
    path=tmp_path/'ratings.csv'
    path.write_text('rater_id,clip,overall,flaw_type,flaw_time_s\na,2.flac,3,rushing;dragging,2;8\n')
    row=read_ratings(path,key_fixture())[0]
    assert row['flaw_type']=='rushing;dragging'
    assert row['flaw_time_s']=='2;8'
