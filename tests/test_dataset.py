"""Speaker-separated immutable dataset splits and transcript coverage."""
import pytest
from speecheval import dataset as f


def test_dataset_feature_cache_recomputes_when_only_hq_audio_changes(tmp_path):
    import json
    import numpy as np
    import soundfile as sf
    rid='sample__reader__quiet_s1_01'
    alignment={'schema':'alignment/v1','recording_id':rid,'duration_s':1.,'audio':'input.flac','transcript':'text.txt',
               'aligner':{'name':'mfa'},'warnings':[],
               'words':[{'i':0,'text':'one','norm':'one','sentence':0,'start':.1,'end':.8}],
               'sentences':[{'i':0,'word_start':0,'word_end':0,'start':.1,'end':.8}],'uncertain_words':[]}
    path=tmp_path/'data/alignment'/f'{rid}.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(alignment))
    audio=tmp_path/'data/flawed/hq'/f'{rid}.flac';audio.parent.mkdir(parents=True)
    wave=.3*np.sin(2*np.pi*200*np.arange(44100)/44100)
    sf.write(audio,wave,44100)
    state=tmp_path/'cache/features.json'
    records=[{'recording_id':rid}]
    settings={'pitch_ceiling_q3_factor':1.5,'pause_threshold_s':.25}
    first=f.extract_dataset_features(tmp_path,records,{'unchanged.json':'same'}, settings,state)
    stats=tmp_path/'data/features/speaker_stats'/f'{rid}.json'
    before=json.loads(stats.read_text())['intensity_median_db']
    assert f.extract_dataset_features(tmp_path,records,{'unchanged.json':'same'}, settings,state)==first
    sf.write(audio,wave/2,44100)
    second=f.extract_dataset_features(tmp_path,records,{'unchanged.json':'same'}, settings,state)
    after=json.loads(stats.read_text())['intensity_median_db']
    assert after-before==pytest.approx(-6.02,abs=.2)
    assert second['inputs']!=first['inputs']


def test_human_script_cli_is_available_without_dataset_build(monkeypatch,tmp_path):
    from typer.testing import CliRunner
    from speecheval.cli import app
    import yaml
    monkeypatch.chdir(tmp_path)
    (tmp_path/'configs').mkdir()
    (tmp_path/'configs/flaws.yaml').write_text(yaml.safe_dump({'seed':123}))
    calls=[]
    monkeypatch.setattr(f,'human_script',lambda root,seed:calls.append((root,seed)))
    result=CliRunner().invoke(app,['human','script'])
    assert result.exit_code==0,result.output
    assert calls==[(tmp_path,123)]


def rows(text,n):
    return [{'recording_id':f'{text}__reader{i:02d}__orig','text_id':text,'speaker_slug':f'reader{i:02d}'} for i in range(n)]


def test_thirteenth_poem_reader_goes_to_remaining_train_not_dev():
    result=f.assign_splits(rows('o_captain',13),{})
    assert result['dev']==['o_captain__reader08__orig','o_captain__reader09__orig']
    assert result['test']==['o_captain__reader11__orig','o_captain__reader12__orig']
    assert 'o_captain__reader10__orig' in result['train'] and len(result['train'])==9


def test_exclusions_precede_split_and_speakers_never_leak():
    sources=rows('gettysburg',15)
    result=f.assign_splits(sources,{'gettysburg__reader00__orig':'clipping'})
    assert [len(result[s]) for s in ['train','dev','test']]==[9,2,3]
    assert result['excluded']=={'gettysburg__reader00__orig':'clipping'}
    assert not set(result['train'])&set(result['test'])
    duplicate={**sources[0],'recording_id':'jfk_rice__reader00__orig','text_id':'jfk_rice'}
    with pytest.raises(ValueError,match='speaker'):f.assign_splits(sources+[duplicate],{})


def test_split_freeze_rejects_changed_membership(tmp_path):
    result=f.assign_splits(rows('gettysburg',15),{})
    path=tmp_path/'splits.yaml';f.freeze_splits(path,result)
    old=path.read_bytes();f.freeze_splits(path,result);assert path.read_bytes()==old
    changed={**result,'train':result['train'][1:]}
    with pytest.raises(ValueError,match='frozen'):f.freeze_splits(path,changed)


def test_intentional_excerpt_does_not_count_unrecorded_bookends_as_deviation():
    expected='introductory remarks we choose to go to the moon closing remarks'.split()
    spoken='we choose to go to the moon'.split()
    assert f.transcript_difference(expected,spoken,excerpt=True)==(0,7)
    assert f.transcript_difference(expected,spoken,excerpt=False)==(4,11)


def test_composed_maps_keep_both_edits_exact():
    from speecheval.inject import edit_map,map_time
    first=edit_map(10.,1.,3.,1.)
    second=edit_map(9.,4.,5.,2.)
    combined=f.compose_maps(first,second)
    assert map_time(2.,combined)==1.5
    assert map_time(5.5,combined)==5.
    assert map_time(7.,combined)==7.
    assert map_time(10.,combined)==10.


def test_mixed_sites_are_deterministic_different_and_separated():
    from test_inject import config_fixture
    words=[]
    for i in range(80):
        start=1.2+.3*i+.5*(i//10)
        words.append({'i':i,'text':'word','norm':'word','sentence':i//10,'start':start,'end':start+.2})
    alignment={'recording_id':'sample__reader__orig','words':words,'duration_s':30.,'uncertain_words':[]}
    chosen=f.choose_mixed_sites(alignment,config_fixture(),1)
    assert chosen==f.choose_mixed_sites(alignment,config_fixture(),1)
    assert len(chosen)==3 and len({x['type'] for x in chosen})==3
    for first,second in zip(chosen,chosen[1:]):
        assert words[second['site'][0]]['start']-words[first['site'][1]]['end']>=2.


def test_mixed_bundle_has_three_labels_and_composed_oracle(tmp_path):
    import json
    import numpy as np
    import soundfile as sf
    from test_inject import alignment_fixture,config_fixture
    from speecheval.align.base import Alignment
    from speecheval.inject import Label,map_time
    alignment=alignment_fixture();words=[]
    for i in range(80):
        start=1.2+.3*i+.5*(i//10)
        words.append({'i':i,'text':'word','norm':'word','sentence':i//10,'start':start,'end':start+.2})
    alignment.update(words=words,duration_s=30.,uncertain_words=[],sentences=[
        {'i':i,'word_start':i*10,'word_end':i*10+9,'start':words[i*10]['start'],'end':words[i*10+9]['end']} for i in range(8)])
    audio=tmp_path/'source.wav';sr=44100
    sf.write(audio,.1*np.sin(2*np.pi*150*np.arange(sr*30)/sr),sr,subtype='PCM_16')
    record=f.generate_mixed(tmp_path,audio,alignment,{'pitch_floor_hz':80.,'pitch_ceiling_hz':300.},config_fixture(),1)
    rid=record['recording_id'];label=json.loads((tmp_path/'data/labels'/f'{rid}.json').read_text())
    oracle=json.loads((tmp_path/'data/alignment/oracle'/f'{rid}.json').read_text())
    mapping=json.loads((tmp_path/'data/flawed/timemaps'/f'{rid}.json').read_text())['breakpoints']
    Label.model_validate(label);Alignment.model_validate(oracle)
    assert len(label['flaws'])==3 and len(record['artifacts'])==5
    assert rid=='sample__reader__mixed_01'
    assert oracle['words'][-1]['end']==pytest.approx(map_time(words[-1]['end'],mapping,side='left'),abs=.003)
    assert f.generate_mixed(tmp_path,audio,alignment,{'pitch_floor_hz':80.,'pitch_ceiling_hz':300.},config_fixture(),1)==record


def test_real_alignment_sentences_come_from_text_indices_not_oracle_times():
    from test_inject import alignment_fixture
    import copy
    source=alignment_fixture();real=copy.deepcopy(source)
    for word in real['words']:word['start']+=.1;word['end']+=.1;word['sentence']=0
    real['sentences']=[{'i':0,'start':0.,'end':9.,'word_start':0,'word_end':19}]
    result=f.restore_sentences(real,source)
    assert result['words'][10]['sentence']==1
    assert result['sentences'][1]['start']==pytest.approx(source['words'][10]['start']+.1)
    assert result['sentences'][1]['end']==pytest.approx(source['words'][19]['end']+.1)
    assert result['uncertain_words']==[4]


def test_source_worker_generates_declared_variants_without_changing_source(tmp_path):
    import json
    import soundfile as sf
    from test_inject import alignment_fixture,config_fixture,tone
    source=alignment_fixture();rid=source['recording_id'];config=config_fixture()
    config['types']={'too_quiet':config['types']['too_quiet']}
    alignment=tmp_path/'data/alignment'/f'{rid}.json';alignment.parent.mkdir(parents=True)
    alignment.write_text(json.dumps(source))
    audio=tmp_path/'data/audio/hq'/f'{rid}.wav';audio.parent.mkdir(parents=True)
    sf.write(audio,tone(9.),44100,subtype='PCM_16');before=audio.read_bytes()
    stats=tmp_path/'data/features/speaker_stats'/f'{rid}.json';stats.parent.mkdir(parents=True)
    stats.write_text('{}')
    result=f.build_source(tmp_path,rid,config,{'dataset':{'mixed_per_source':0}},stage='generate')
    assert len(result['records'])==5 and not result['skipped']
    assert audio.read_bytes()==before
    rows=[{'recording_id':rid,'text_id':'sample','speaker_slug':'reader','duration_s':9.}]
    index=f.write_dataset_index(tmp_path,rows,[result],{'train':[rid],'dev':[],'test':[],'excluded':{}})
    assert len(index)==6 and {r['split'] for r in index}=={'train'}
    assert sum(r['kind']=='synthetic' for r in index)==5


def test_recording_script_is_deterministic_and_has_twelve_takes(tmp_path):
    import json
    canonical=tmp_path/'data/transcripts/canonical';canonical.mkdir(parents=True)
    for name in ('gettysburg','reagan_challenger'):(canonical/f'{name}.txt').write_text('One. Two. Three. Four.')
    (canonical/'o_captain.txt').write_text('One.\nTwo.\nThree.\nFour.\n')
    words=[{'i':i,'text':word+'.','norm':word.lower(),'start':i*30.,'end':(i+1)*30.,'sentence':i} for i,word in enumerate(['One','Two','Three','Four'])]
    alignment={'schema':'alignment/v1','recording_id':'reagan_challenger__reagan__orig','audio':'audio.wav',
        'duration_s':120.,'transcript':'text.txt','aligner':{'name':'mfa'},'warnings':[],'words':words,
        'sentences':[{'i':i,'start':w['start'],'end':w['end'],'word_start':i,'word_end':i} for i,w in enumerate(words)]}
    path=tmp_path/'data/alignment/reagan_challenger__reagan__orig.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(alignment))
    result=f.human_script(tmp_path,20261001)
    assert len(result['takes'])==12 and result['audio_recorded'] is False
    script=tmp_path/'data/human/RECORDING_SCRIPT.md';old=script.read_bytes()
    assert f.human_script(tmp_path,20261001)==result and script.read_bytes()==old
    assert 'Four.' not in (tmp_path/'data/human/scripts/reagan_challenger.txt').read_text()
