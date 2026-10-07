"""Energy-only trimming and end-to-end deterministic analysis on a tiny corpus."""
import numpy as np
import pytest
from speecheval import pipeline as p


def test_trim_uses_sustained_energy_not_one_sample_spike():
    sr=16000;wave=np.zeros(sr*2)
    wave[int(.6*sr):int(1.4*sr)]=.1*np.sin(2*np.pi*200*np.arange(int(.8*sr))/sr)
    wave[int(.1*sr)]=.9
    assert p.energy_bounds(wave,sr)==pytest.approx((.35,1.65),abs=.011)
    with pytest.raises(ValueError,match='speech'):p.energy_bounds(np.zeros(sr),sr)


def test_participant_cache_identity_binds_feature_and_aligner_code(tmp_path):
    names=['pipeline.py','features.py','transcripts.py','align/mfa.py','align/base.py']
    for name in names:
        file=tmp_path/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('old')
    first=p.participant_code_identity(tmp_path)
    (tmp_path/'features.py').write_text('new')
    second=p.participant_code_identity(tmp_path)
    assert first!=second
    (tmp_path/'align/mfa.py').write_text('new')
    assert p.participant_code_identity(tmp_path)!=second


def test_analysis_json_replays_identically_on_real_features(tmp_path):
    import json
    import soundfile as sf
    import yaml
    from speecheval.features import extract_features
    from test_detect import config
    from pathlib import Path
    import hashlib,importlib.metadata
    from speecheval import features as feature_module
    (tmp_path/'configs').mkdir()
    (tmp_path/'configs/detector.yaml').write_text(yaml.safe_dump(config()))
    settings={'pitch_ceiling_q3_factor':1.5,'pause_threshold_s':.25}
    (tmp_path/'configs/default.yaml').write_text(yaml.safe_dump({'features':settings}))
    proof={'inputs':{'recordings':{},'settings':settings,
        'versions':{name:importlib.metadata.version(name) for name in ('librosa','praat-parselmouth','numpy','pandas','pyarrow','cmudict')},
        'code':{f'src/speecheval/{name}':hashlib.sha256((Path(feature_module.__file__).parent/name).read_bytes()).hexdigest() for name in ('features.py','transcripts.py')}},'artifacts':{}}
    training=[]
    for text in ['gettysburg','o_captain']:
        canonical=tmp_path/'data/transcripts/canonical'/f'{text}.txt';canonical.parent.mkdir(parents=True,exist_ok=True);canonical.write_text('One two three.')
        for reader in ['alice','bob']:
            rid=f'{text}__{reader}__orig';training.append(rid)
            audio=tmp_path/'data/audio/hq'/f'{rid}.wav';audio.parent.mkdir(parents=True,exist_ok=True)
            sf.write(audio,.1*np.sin(2*np.pi*150*np.arange(44100)/44100),44100)
            alignment={'schema':'alignment/v1','recording_id':rid,'audio':str(audio.relative_to(tmp_path)),'duration_s':1.,
                       'transcript':'text.txt','aligner':{'name':'mfa'},'warnings':[],
                       'words':[{'i':i,'text':w,'norm':w.lower().strip('.'),'sentence':0,'start':.1+.2*i,'end':.2+.2*i} for i,w in enumerate(['One','two','three.'])],
                       'sentences':[{'i':0,'word_start':0,'word_end':2,'start':.1,'end':.6}]}
            path=tmp_path/'data/alignment'/f'{rid}.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(alignment))
            proof['artifacts'].update(extract_features(tmp_path,audio,alignment,settings))
            proof['inputs']['recordings'][rid]={'audio':hashlib.sha256(audio.read_bytes()).hexdigest(),'alignment':hashlib.sha256(path.read_bytes()).hexdigest()}
    (tmp_path/'data/features/provenance.json').write_text(json.dumps(proof))
    (tmp_path/'configs/splits.yaml').write_text(yaml.safe_dump({'train':training,'dev':[],'test':[],'excluded':{}}))
    target=tmp_path/'data/audio/hq/gettysburg__alice__orig.wav'
    result=p.analyze(target,'gettysburg',exclude_speaker='alice',root=tmp_path)
    output=tmp_path/'data/analyses'/f"{result['analysis_id']}.json";before=output.read_bytes()
    assert result['reference']['n_readers']==1 and result['schema']=='analysis/v1'
    assert p.analyze(target,'gettysburg',exclude_speaker='alice',root=tmp_path)==result
    assert output.read_bytes()==before
    sf.write(target,.05*np.sin(2*np.pi*150*np.arange(44100)/44100),44100)
    with pytest.raises(ValueError,match='provenance|stale'):
        p.analyze(target,'gettysburg',exclude_speaker='alice',root=tmp_path)
    assert all('__alice__' not in r for r in json.loads((tmp_path/'data/reference/gettysburg__excl-alice.json').read_text())['inputs']['pool']['readers'])
