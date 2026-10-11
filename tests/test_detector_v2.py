"""Post-hoc detector behavior on tiny literal fixtures, never held-out corpus data."""
import copy
import math

import pytest
from typer.testing import CliRunner


def settings():
    return {
        'k': {k: 3.5 for k in ('rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause')},
        'severity_z_bins': [2.,2.75,3.5,4.059,6591.],
        'region_min_words': 3, 'region_max_gap_words': 1,
        'awkward_pause_min_s': .45, 'missing_pause_ref_min_s': .3, 'missing_pause_max_frac': .4,
        'within_k': .5, 'within_min_sentences': 3,
        'within_scale_floor': {'rate': .05, 'pitchvar': .05, 'loud': .5},
        'effects': {'rate_fraction': .1, 'pitch_fraction': .2, 'loud_db': 2., 'clarity_db': 2.,
                    'pause_excess_s': .25, 'pause_deficit_s': .1},
        'region_min_duration_s': .2, 'merge_gap_s': .1,
    }


def rows():
    return [dict(i=i, start=i*.1, end=(i+1)*.1, sentence=0, ref_i=i,
                 values={'rate':math.log(1.5)},reference={'rate':0.},z={'rate':4.}) for i in range(3)]


def test_sentence_contrast_is_robust_and_uses_recording_median():
    from speecheval.detector_v2 import sentence_contrast
    sentences=[dict(i=i,n_words=5,articulation_rate_syl_s=rate,f0_st_range=2.) for i,rate in enumerate((1.,2.,4.))]
    result=sentence_contrast(sentences,[],settings())
    assert result[0]['rate']==pytest.approx(-.6744907595)
    assert result[1]['rate']==0.
    assert result[2]['rate']==pytest.approx(.6744907595)


def test_zero_spread_and_short_recordings_do_not_create_infinite_contrast():
    from speecheval.detector_v2 import sentence_contrast
    s=[dict(i=i,n_words=5,articulation_rate_syl_s=2.,f0_st_range=2.) for i in range(3)]
    assert [v['rate'] for v in sentence_contrast(s,[],settings()).values()]==[0.,0.,0.]
    assert math.isnan(sentence_contrast(s[:2],[],settings())[0]['rate'])


def test_invalid_sentence_does_not_enter_own_median():
    from speecheval.detector_v2 import sentence_contrast
    s=[dict(i=i,n_words=5,articulation_rate_syl_s=rate,f0_st_range=2.) for i,rate in enumerate((1.,2.,4.,100.))]
    s[-1]['invalid_evidence']=True
    c=sentence_contrast(s,[],settings())
    assert c[1]['rate']==0.
    assert math.isnan(c[3]['rate'])


@pytest.mark.parametrize('reader_z,own_z,want',[(4.,2.,1),(4.,0.,0),(1.,2.,0),(4.,-2.,0)])
def test_flags_require_both_reference_and_directional_own_contrast(reader_z,own_z,want):
    from speecheval.detector_v2 import detect_v2
    r=rows()
    for row in r:row['z']['rate']=reader_z
    found=detect_v2(r,1.,settings(),{0:{'rate':own_z}})
    assert len(found)==want
    if found:assert found[0]['type']=='rushing' and found[0]['v2']['within_recording_z']==own_z


def test_practical_effect_rejects_huge_z_for_tiny_rate_difference():
    from speecheval.detector_v2 import detect_v2
    r=rows()
    for row in r:row['values']['rate']=math.log(1.05)
    assert detect_v2(r,1.,settings(),{0:{'rate':2.}})==[]


def test_region_duration_and_time_merge_gap_have_physical_units():
    from speecheval.detector_v2 import detect_v2
    r=rows();cfg=settings();cfg['region_min_duration_s']=.4
    assert detect_v2(r,1.,cfg,{0:{'rate':2.}})==[]
    extra=copy.deepcopy(r)
    for row in extra:row.update(i=row['i']+3,ref_i=row['ref_i']+3,start=row['start']+.6,end=row['end']+.6)
    cfg['region_min_duration_s']=.2
    assert len(detect_v2(r+extra,1.,cfg,{0:{'rate':2.}}))==2
    cfg['merge_gap_s']=.4
    assert len(detect_v2(r+extra,1.,cfg,{0:{'rate':2.}}))==1


def test_unknown_word_is_hard_region_barrier():
    from speecheval.detector_v2 import detect_v2
    r=rows();r[1]['ref_i']=None
    assert detect_v2(r,1.,settings(),{0:{'rate':2.}})==[]


def test_pause_needs_practical_excess_not_just_zero_spread_z():
    from speecheval.detector_v2 import detect_v2
    r=rows();r[1]['values']['pause']=math.log(.5+.05)
    r[1]['reference']['pause']=math.log(.4+.05);r[1]['z']['pause']=1000.
    for row in r:row['z']['rate']=0.
    assert detect_v2(r,1.,settings(),{})==[]
    r[1]['values']['pause']=math.log(1.+.05)
    found=detect_v2(r,1.,settings(),{})
    assert len(found)==1 and found[0]['type']=='awkward_pause'


def test_dev_promotion_requires_guard_and_both_margins():
    from speecheval.tune_v2 import promotion_allowed
    assert promotion_allowed(.1,.2,.4)
    assert not promotion_allowed(.1,.115,.4)
    assert not promotion_allowed(.5,.525,.4)
    assert not promotion_allowed(.1,.2,.6)


def test_search_is_bounded_and_configs_are_distinct():
    from speecheval.tune_v2 import first_stage,second_stage
    import json
    configs=first_stage(settings())
    configs+=second_stage(configs[0],configs)
    assert len(configs)<=30
    assert len({json.dumps(c,sort_keys=True) for c in configs})==len(configs)


def test_last_guard_repair_uses_clean_dev_excess_and_seconds():
    from speecheval.tune_v2 import guard_repair_config
    predictions=[{'type':'awkward_pause','evidence':{'participant':v,'reference':0.}} for v in (.7,1.,1.3,1.6)]
    items=[{'clean':True,'duration_s':120.,'predicted':predictions},
           {'clean':False,'duration_s':1.,'predicted':[{'type':'awkward_pause','evidence':{'participant':100.,'reference':0.}}]}]
    cfg=guard_repair_config(settings(),items)
    assert cfg['effects']['pause_excess_s']==pytest.approx(1.35)
    assert cfg['effects']['rate_fraction']==.1


def test_dev_selector_rejects_human_paths_and_returns_only_dev(tmp_path):
    from speecheval.tune_v2 import dev_rows
    folder=tmp_path/'data/manifest';folder.mkdir(parents=True)
    path=folder/'dataset_index.csv'
    (tmp_path/'configs').mkdir()
    (tmp_path/'configs/splits.yaml').write_text('dev: [gettysburg__dev__orig]\n')
    path.write_text('recording_id,split,text_id,audio_path,label_path\ngettysburg__test__orig,test,gettysburg,data/flawed/hq/test.flac,\ngettysburg__dev__orig,dev,gettysburg,data/audio/hq/dev.wav,\n')
    assert [r['recording_id'] for r in dev_rows(tmp_path)]==['gettysburg__dev__orig']
    path.write_text('recording_id,split,text_id,audio_path,label_path\ngettysburg__user__take01,dev,gettysburg,data/human/raw/take.wav,\n')
    with pytest.raises(ValueError,match='human'):dev_rows(tmp_path)


def test_tuning_rejects_test_reader_mislabelled_as_dev(tmp_path):
    from speecheval.tune_v2 import dev_rows
    (tmp_path/'configs').mkdir();(tmp_path/'configs/splits.yaml').write_text('dev: [gettysburg__dev__orig]\n')
    folder=tmp_path/'data/manifest';folder.mkdir(parents=True)
    (folder/'dataset_index.csv').write_text('recording_id,split,text_id,audio_path,label_path\ngettysburg__test__rushing_s1_01,dev,gettysburg,data/flawed/hq/test.flac,\n')
    with pytest.raises(ValueError,match='DEV speaker'):dev_rows(tmp_path)


def test_cli_v2_is_explicit_and_rejects_unsupported_mode_before_preparation(tmp_path):
    from speecheval.cli import app
    audio=tmp_path/'tiny.wav';audio.write_bytes(b'not real audio')
    result=CliRunner().invoke(app,['analyze',str(audio),'--detector','v2','--mode','C'])
    assert result.exit_code!=0
    assert 'v2 supports modes A and B' in str(result.exception)
