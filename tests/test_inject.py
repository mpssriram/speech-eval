"""Synthetic signal checks for effects and exact source/flawed time maps."""
import numpy as np
import pytest
from speecheval import inject as f


def tone(seconds=2., sr=44100):
    return (.1*np.sin(2*np.pi*150*np.arange(round(seconds*sr))/sr)).astype('float32')


def test_rubberband_speed_and_piecewise_time_map(tmp_path):
    wet=f.stretch(tone(),44100,1.5,tmp_path)
    assert len(wet)/44100==pytest.approx(2/1.5,abs=.02)
    mapping=f.edit_map(5.,1.,3.,len(wet)/44100)
    assert f.map_time(2.,mapping)==pytest.approx(1.+len(wet)/44100/2)
    assert f.map_time(4.,mapping)==pytest.approx(2.+len(wet)/44100)


def test_flat_gain_and_muffling():
    dry=tone()
    wet=f.quiet(dry,44100,-6,'flat')
    assert np.sqrt(np.mean(wet[4410:-4410]**2)/np.mean(dry[4410:-4410]**2))==pytest.approx(.501,abs=.01)
    noise=np.random.default_rng(2).normal(0,.05,44100).astype('float32')
    low=f.muffle(noise,44100,1300,-5)
    from scipy.signal import welch
    hz,a=welch(noise[4410:-4410],44100,nperseg=2048)
    _,b=welch(low[4410:-4410],44100,nperseg=2048)
    assert b[hz>4000].sum()/a[hz>4000].sum()<.001


def test_pause_step_maps_end_left_start_right():
    mapping=f.edit_map(4.,2.,2.,1.)
    assert f.map_time(2.,mapping,side='left')==2.
    assert f.map_time(2.,mapping,side='right')==3.
    assert f.map_time(3.,mapping)==4.
    shortened=f.edit_map(4.,1.,2.,.03)
    assert f.map_time(3.,shortened)==pytest.approx(2.03)


def test_pitch_flattening_preserves_duration_and_reduces_vibrato():
    sr=44100;t=np.arange(sr*2)/sr
    hz=150*2**((2*np.sin(2*np.pi*5*t))/12)
    signal=(.1*np.sin(2*np.pi*np.cumsum(hz)/sr)).astype('float32')
    wet=f.flatten_pitch(signal,sr,.2,80.,300.)
    import parselmouth
    def spread(y):
        pitch=parselmouth.Sound(y,sampling_frequency=sr).to_pitch_ac(time_step=.01,pitch_floor=80,pitch_ceiling=300)
        hz=pitch.selected_array['frequency'];hz=hz[hz>0]
        return np.std(12*np.log2(hz/np.median(hz)))
    assert len(wet)==len(signal)
    assert spread(wet)/spread(signal)==pytest.approx(.2,abs=.05)


def alignment_fixture():
    words=[]
    for i in range(20):
        start=1.2+.3*i+(.5 if i>=10 else 0)
        words.append({'i':i,'text':'word','norm':'word','sentence':i//10,'start':start,'end':start+.2})
    return {'schema':'alignment/v1','recording_id':'sample__reader__orig','audio':'source.wav',
        'duration_s':9.,'transcript':'text.txt','aligner':{'name':'mfa'},'warnings':[],
        'words':words,'sentences':[{'i':i,'start':words[i*10]['start'],'end':words[i*10+9]['end'],
            'word_start':i*10,'word_end':i*10+9} for i in range(2)],'uncertain_words':[4]}


def config_fixture():
    import yaml
    from pathlib import Path
    return yaml.safe_load(Path('configs/flaws.yaml').read_text())


def test_sites_seeded_inside_sentence_and_avoid_uncertainty():
    alignment=alignment_fixture();cfg=config_fixture()
    first=f.choose_site(alignment,cfg,'rushing',3,1)
    assert first==f.choose_site(alignment,cfg,'rushing',3,1)
    assert first!=f.choose_site(alignment,cfg,'rushing',3,2)
    a,b=first
    assert not a<=4<=b
    assert alignment['words'][a]['sentence']==alignment['words'][b]['sentence']
    assert cfg['region_words']['min']<=b-a+1<=cfg['region_words']['max']


def test_inserted_pause_and_shortened_pause_have_correct_oracle(tmp_path):
    alignment=alignment_fixture();cfg=config_fixture();y=tone(9.)
    for kind,severity,expected in [('awkward_pause',2,1.),('missing_pause',5,-.57)]:
        site=(8,9) if kind=='awkward_pause' else (9,10)
        wet,label,mapping,oracle=f.inject_once(y,44100,alignment,{},cfg,kind,severity,1,tmp_path,site=site)
        assert len(wet)/44100-9.==pytest.approx(expected,abs=.001)
        assert oracle['words'][10]['start']-alignment['words'][10]['start']==pytest.approx(expected,abs=.001)
        assert label['schema']=='labels/v1' and label['source']=='synthetic'
        assert np.max(np.abs(wet))<1
        if kind=='missing_pause':assert label['flaws'][0]['parameters']['result_pause_s']>=.03


def test_quiet_injection_reproducible_and_unchanged_outside(tmp_path):
    alignment=alignment_fixture();cfg=config_fixture();y=tone(9.)
    first=f.inject_once(y,44100,alignment,{},cfg,'too_quiet',3,1,tmp_path,site=(10,13))
    second=f.inject_once(y,44100,alignment,{},cfg,'too_quiet',3,1,tmp_path,site=(10,13))
    assert np.array_equal(first[0],second[0]) and first[1:]==second[1:]
    assert np.array_equal(y[:44100],first[0][:44100])
    import soundfile as sf
    for name,wet in [('a',first[0]),('b',second[0])]:sf.write(tmp_path/f'{name}.flac',wet,44100,subtype='PCM_16')
    assert (tmp_path/'a.flac').read_bytes()==(tmp_path/'b.flac').read_bytes()


def test_label_rejects_invalid_severity_and_backwards_interval():
    from pydantic import ValidationError
    _,label,_,_=f.inject_once(tone(9.),44100,alignment_fixture(),{},config_fixture(),'too_quiet',3,1,__import__('pathlib').Path('.pytest_work'),site=(10,13))
    f.Label.model_validate(label)
    label['flaws'][0]['severity']=6
    with pytest.raises(ValidationError):f.Label.model_validate(label)
    label['flaws'][0]['severity']=3;label['flaws'][0]['end']=0
    with pytest.raises(ValidationError):f.Label.model_validate(label)


def test_generated_bundle_roundtrip_and_cached_hashes(tmp_path):
    import soundfile as sf
    alignment=alignment_fixture();cfg=config_fixture();audio=tmp_path/'source.wav'
    sf.write(audio,tone(9.),44100,subtype='PCM_16')
    record=f.generate_one(tmp_path,audio,alignment,{},cfg,'too_quiet',3,1)
    second=f.generate_one(tmp_path,audio,alignment,{},cfg,'too_quiet',3,1)
    assert record==second
    rid=record['recording_id']
    assert sf.info(tmp_path/'data/flawed/hq'/f'{rid}.flac').samplerate==44100
    assert sf.info(tmp_path/'data/flawed/align16k'/f'{rid}.flac').samplerate==16000
    assert len(record['artifacts'])==5


def test_effect_check_measures_gain_from_rendered_pcm_audio(tmp_path):
    import soundfile as sf
    import json
    alignment=alignment_fixture();cfg=config_fixture();audio=tmp_path/'source.wav'
    sf.write(audio,tone(9.),44100,subtype='PCM_16')
    record=f.generate_one(tmp_path,audio,alignment,{},cfg,'too_quiet',3,1)
    label=json.loads((tmp_path/'data/labels'/f"{record['recording_id']}.json").read_text())
    measurement=f.measure_effect(tmp_path,audio,label)
    assert measurement['measured']==pytest.approx(-9,abs=.02)
    assert measurement['passed']


def test_pitch_effect_check_uses_fixed_source_pitch_bounds():
    from pathlib import Path
    import json
    root=Path.cwd();rid='gettysburg__lv_dj__monotone_s3_01'
    path=root/'data/labels'/f'{rid}.json'
    source=root/'data/audio/hq/gettysburg__lv_dj__orig.wav'
    rendered=root/'data/flawed/hq'/f'{rid}.flac'
    stats=root/'data/features/speaker_stats/gettysburg__lv_dj__orig.json'
    if not all(p.exists() for p in (path,source,rendered,stats)):
        pytest.skip('Optional real-audio regression; synthetic DSP tests always run')
    label=json.loads(path.read_text())
    measurement=f.measure_effect(root,source,label)
    assert measurement['passed'] and measurement['measured']==pytest.approx(.35,rel=.1)


@pytest.mark.parametrize('kind,severity,site',[('awkward_pause',2,(8,9)),('missing_pause',3,(9,10))])
def test_pause_splice_does_not_introduce_seam_jump(tmp_path,kind,severity,site):
    sr=44100;y=(.1*np.sin(2*np.pi*173*np.arange(sr*9)/sr)).astype('float32')
    wet,_,mapping,_=f.inject_once(y,sr,alignment_fixture(),{},config_fixture(),kind,severity,1,tmp_path,site=site)
    seam=round(mapping[1][1]*sr)
    if kind=='awkward_pause':seams=[seam,round(mapping[2][1]*sr)]
    else:seams=[seam]
    for point in seams:
        assert abs(float(wet[point]-wet[point-1]))<=float(np.max(abs(np.diff(y))))*1.1


def test_room_tone_loop_has_no_hard_wrap_jump():
    sr=44100;y=(.1*np.sin(2*np.pi*173*np.arange(sr*9)/sr)).astype('float32')
    tone=f.room_tone(y,sr,alignment_fixture(),sr*2)
    assert len(tone)==sr*2
    assert float(np.max(abs(np.diff(tone))))<float(np.max(abs(np.diff(y))))*1.6


def test_zero_gap_insertion_does_not_stretch_adjacent_words(tmp_path):
    alignment=alignment_fixture();alignment['words'][8]['end']=alignment['words'][9]['start']
    sr=44100;y=(.1*np.sin(2*np.pi*173*np.arange(sr*9)/sr)).astype('float32')
    _,_,_,oracle=f.inject_once(y,sr,alignment,{},config_fixture(),'awkward_pause',2,1,tmp_path,site=(8,9))
    assert oracle['words'][8]['end']==pytest.approx(alignment['words'][8]['end'],abs=.0005)
    assert oracle['words'][9]['start']==pytest.approx(alignment['words'][9]['start']+1,abs=.0005)


def test_both_sample_rates_share_safe_peak_scaling():
    dry=np.where(np.arange(44100)<22050,-10**(-1/20),10**(-1/20)).astype('float32')
    hq,down,adjustment=f.safe_output_pair(dry,44100)
    assert np.max(abs(hq))<=10**(-1/20)+1e-7
    assert np.max(abs(down))<=10**(-1/20)+1e-7
    assert adjustment<0
    assert hq[0]/dry[0]==pytest.approx(10**(adjustment/20))
