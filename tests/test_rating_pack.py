"""Blind export safety on temporary generated audio; real pack verified separately."""
import hashlib
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf


def test_selection_is_training_only_and_covers_all_types():
    from speecheval.rating_pack import select_rows
    sources=('gettysburg__lv_fb','gettysburg__lv_dl','o_captain__lv_apc')
    rows=[{'recording_id':source+'__orig','kind':'source','split':'train'} for source in sources]
    specs=[('rushing',1),('dragging',3),('monotone',5),('too_quiet',2),('mumbling',4),('awkward_pause',3),('missing_pause',4),('rushing',5),('monotone',2)]
    rows += [{'recording_id':sources[i%3]+f'__{kind}_s{n}_01','kind':'synthetic','split':'train'} for i,(kind,n) in enumerate(specs)]
    chosen=select_rows(rows)
    assert len(chosen)==12
    assert sum(r['kind']=='source' for r in chosen)==3
    assert {r['recording_id'].split('__')[-1].split('_s')[0] for r in chosen if r['kind']=='synthetic'}=={
        'rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause'}
    rows[0]['split']='test'
    with pytest.raises(ValueError,match='training'):select_rows(rows)


def test_crop_retains_entire_label_with_context():
    from speecheval.rating_pack import crop_bounds
    assert crop_bounds(100,[{'start':1,'end':3}])==(0,20)
    assert crop_bounds(100,[{'start':70,'end':95}])==(68,97)
    assert crop_bounds(100,[])==(40,60)


def test_source_must_match_licensed_inventory_before_export(tmp_path):
    from speecheval.rating_pack import verify_source
    audio=tmp_path/'data/audio/hq/fixture.wav';audio.parent.mkdir(parents=True);audio.write_bytes(b'fixture')
    key='audio/hq/fixture.wav';inventory={'audio_sources':{key:'licensed'},'files':{key:{'sha256':hashlib.sha256(b'fixture').hexdigest()}}}
    assert verify_source(tmp_path,audio,inventory)==key
    audio.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='licensed'):verify_source(tmp_path,audio,inventory)


def test_export_is_lossless_blind_and_transforms_label_times(tmp_path):
    from speecheval.rating_pack import export_clip
    import yaml
    audio=tmp_path/'source.wav';sf.write(audio,np.sin(np.arange(24000)/20)*.1,1000,subtype='PCM_16')
    alignment={'words':[{'start':0,'end':24}]}
    analysis={'analysis_id':'hidden','regions':[]}
    rubric=yaml.safe_load((Path.cwd()/'configs/rubric.yaml').read_text())
    dest=tmp_path/'blind/abcd.flac'
    evidence=export_clip(audio,dest,[{'type':'rushing','start':8,'end':10,'severity':2}],alignment,analysis,rubric)
    assert sf.info(dest).duration==20
    assert evidence['truth'][0]['start']==8 and evidence['truth'][0]['end']==10
    assert sf.info(dest).subtype=='PCM_16'
    before=hashlib.sha256(dest.read_bytes()).hexdigest()
    export_clip(audio,dest,[{'type':'rushing','start':8,'end':10,'severity':2}],alignment,analysis,rubric)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==before


def test_original_rows_have_no_label_file_but_synthetic_rows_must_have_one(tmp_path):
    from speecheval.rating_pack import load_labels
    assert load_labels(tmp_path,{'kind':'source','label_path':''})==[]
    with pytest.raises(ValueError,match='label'):
        load_labels(tmp_path,{'kind':'synthetic','label_path':''})


def test_rebuild_does_not_overwrite_completed_rating_form(tmp_path):
    from speecheval.rating_pack import write_blank_form
    path=tmp_path/'rating_form.csv'
    write_blank_form(path,['opaque.flac'])
    path.write_text('rater_id,clip,overall,flaw_type,flaw_time_s\na,opaque.flac,4,none,\n')
    before=path.read_bytes()
    with pytest.raises(ValueError,match='overwrite'):write_blank_form(path,['opaque.flac'])
    assert path.read_bytes()==before


def test_blank_template_newlines_are_portable_across_git_checkout(tmp_path):
    from speecheval.rating_pack import write_blank_form
    path=tmp_path/'rating_form.csv'
    expected=b'rater_id,clip,overall,flaw_type,flaw_time_s\n,opaque.flac,,,\n'
    path.write_bytes(expected)
    write_blank_form(path,['opaque.flac'])
    assert path.read_bytes()==expected
    path.write_bytes(expected.replace(b'\n',b'\r\n'))
    write_blank_form(path,['opaque.flac'])
    assert path.read_bytes()==expected
