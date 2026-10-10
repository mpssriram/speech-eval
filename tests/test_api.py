"""Actual HTTP contracts, decoding guards and audio range responses."""
import io
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient
from speecheval import service as s
import json
import time
import pytest


def wav_bytes(seconds=10, sr=44100):
    stream=io.BytesIO();sf.write(stream,.1*np.sin(2*np.pi*200*np.arange(sr*seconds)/sr),sr,format='WAV')
    return stream.getvalue()


def test_health_missing_analysis_and_invalid_upload_are_clear(tmp_path):
    with TestClient(s.create_app(tmp_path)) as client:
        assert client.get('/api/health').json()['version']=='0.1.0'
        assert client.get('/api/analyses/abcdef012345').status_code==404
        response=client.post('/api/analyses',data={'text_id':'gettysburg','mode':'A'},files={'audio':('bad.txt',b'not audio','text/plain')})
        assert response.status_code==400


def test_audio_range_is_real_and_cannot_escape_project(tmp_path):
    import json
    audio=tmp_path/'data/audio/hq/gettysburg__user__take01.wav';audio.parent.mkdir(parents=True);audio.write_bytes(wav_bytes())
    alignment=tmp_path/'data/alignment/gettysburg__user__take01.json';alignment.parent.mkdir(parents=True)
    alignment.write_text(json.dumps({'audio':str(audio.relative_to(tmp_path))}))
    with TestClient(s.create_app(tmp_path)) as client:
        response=client.get('/api/audio/gettysburg__user__take01',headers={'Range':'bytes=0-99'})
        assert response.status_code==206 and len(response.content)==100
        assert response.headers['content-range'].startswith('bytes 0-99/')
        assert client.get('/api/audio/bad..id').status_code==400


def test_long_audio_is_rejected_before_queue(tmp_path):
    with TestClient(s.create_app(tmp_path)) as client:
        response=client.post('/api/analyses',data={'text_id':'gettysburg','mode':'A'},files={'audio':('long.wav',wav_bytes(601,16000),'audio/wav')})
        assert response.status_code==400 and '10 minutes' in response.json()['detail']


@pytest.fixture
def corpus(tmp_path):
    """Real measured 10-second, two-sentence corpus, not a mocked pipeline."""
    import hashlib, importlib.metadata, yaml
    from pathlib import Path
    from speecheval import features
    from test_detect import config
    from test_score import config as rubric
    (tmp_path/'configs').mkdir()
    settings={'pitch_ceiling_q3_factor':1.5,'pause_threshold_s':.25}
    for name, value in [('detector',config()),('rubric',rubric()),('default',{'features':settings})]:
        (tmp_path/f'configs/{name}.yaml').write_text(yaml.safe_dump(value))
    proof={'inputs':{'recordings':{},'settings':settings,
        'versions':{n:importlib.metadata.version(n) for n in ('librosa','praat-parselmouth','numpy','pandas','pyarrow','cmudict')},
        'code':{f'src/speecheval/{n}':hashlib.sha256((Path(features.__file__).parent/n).read_bytes()).hexdigest() for n in ('features.py','transcripts.py')}},'artifacts':{}}
    train=[]
    for text in ['gettysburg','o_captain']:
        canonical=tmp_path/f'data/transcripts/canonical/{text}.txt';canonical.parent.mkdir(parents=True,exist_ok=True)
        canonical.write_text('One two three. Four five six.')
        for reader in ['alice','bob']:
            rid=f'{text}__{reader}__orig';train.append(rid)
            audio=tmp_path/f'data/audio/hq/{rid}.wav';audio.parent.mkdir(parents=True,exist_ok=True);audio.write_bytes(wav_bytes())
            words=[{'i':i,'text':w,'norm':w.lower().strip('.'),'sentence':i//3,'start':.5+i,'end':1.+i} for i,w in enumerate('One two three. Four five six.'.split())]
            alignment={'schema':'alignment/v1','recording_id':rid,'audio':str(audio.relative_to(tmp_path)),'duration_s':10.,'transcript':'text.txt','aligner':{'name':'mfa'},'warnings':[],
                'words':words,'sentences':[{'i':i,'word_start':i*3,'word_end':i*3+2,'start':.5+i*3,'end':3.+i*3} for i in range(2)]}
            path=tmp_path/f'data/alignment/{rid}.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(alignment))
            proof['artifacts'].update(features.extract_features(tmp_path,audio,alignment,settings))
            proof['inputs']['recordings'][rid]={'audio':hashlib.sha256(audio.read_bytes()).hexdigest(),'alignment':hashlib.sha256(path.read_bytes()).hexdigest()}
    (tmp_path/'data/features/provenance.json').write_text(json.dumps(proof))
    (tmp_path/'configs/splits.yaml').write_text(yaml.safe_dump({'train':train,'dev':[],'test':[],'excluded':{}}))
    (tmp_path/'configs/baselines.yaml').write_text(yaml.safe_dump({'gettysburg':'gettysburg__bob__orig'}))
    return tmp_path


def test_upload_real_analysis_dedup_tracks_baseline_and_persistent_history(corpus):
    with TestClient(s.create_app(corpus)) as client:
        assert client.get('/api/texts').json()[0]['canonical_transcript']=='One two three. Four five six.'
        data={'text_id':'gettysburg','mode':'A'}
        first=client.post('/api/analyses',data=data,files={'audio':('fixture.wav',wav_bytes(),'audio/wav')})
        assert first.status_code==200, first.text
        aid=first.json()['analysis_id']
        for _ in range(100):
            result=client.get(f'/api/analyses/{aid}').json()
            if result['status'] in ('done','error'):break
            time.sleep(.05)
        assert result['status']=='done', result
        assert result['analysis']['schema']=='analysis/v1' and isinstance(result['analysis']['scores']['overall'],float)
        second=client.post('/api/analyses',data=data,files={'audio':('renamed.wav',wav_bytes(),'audio/wav')}).json()
        assert second['analysis_id']==aid and second['status']=='done'
        tracks=client.get(f'/api/analyses/{aid}/tracks').json()
        assert len(tracks['words'])==6 and 'reference' in tracks['words'][0]
        segment=client.get(f'/api/analyses/{aid}/baseline-segment?word_start=0&word_end=1').json()
        assert segment['recording_id']=='gettysburg__bob__orig' and segment['start']==.5 and segment['end']==2.
        assert client.get(f'/api/analyses/{aid}/baseline-segment?word_start=-1&word_end=1').status_code==400
    with TestClient(s.create_app(corpus)) as client:
        assert client.get('/api/history?text_id=gettysburg').json()[0]['analysis_id']==aid
        assert client.get(f'/api/analyses/{aid}').json()['status']=='done'


def test_mode_and_reference_guards_do_not_enqueue(tmp_path):
    with TestClient(s.create_app(tmp_path)) as client:
        for data in [{'text_id':'gettysburg','mode':'B'}, {'text_id':'bad','mode':'A'}, {'mode':'C'}, {'text_id':'../bad','mode':'A'}, {'mode':'X'}]:
            response=client.post('/api/analyses',data=data,files={'audio':('fixture.wav',wav_bytes(),'audio/wav')})
            assert response.status_code==400
        assert not list((tmp_path/'data/app/jobs').glob('*.json'))


def test_canonical_change_invalidates_completed_upload_and_old_tracks(corpus):
    with TestClient(s.create_app(corpus)) as client:
        first=client.post('/api/analyses',data={'text_id':'gettysburg'},files={'audio':('a.wav',wav_bytes())}).json()
        aid=first['analysis_id']
        for _ in range(100):
            if client.get(f'/api/analyses/{aid}').json()['status']=='done':break
            time.sleep(.05)
        (corpus/'data/transcripts/canonical/gettysburg.txt').write_text('One two three. Four five seven.')
        second=client.post('/api/analyses',data={'text_id':'gettysburg'},files={'audio':('a.wav',wav_bytes())}).json()
        assert second['analysis_id']!=aid
        assert client.get(f'/api/analyses/{aid}/tracks').status_code==409


def test_streaming_webm_is_decoded_without_container_duration(tmp_path):
    import subprocess
    wave=tmp_path/'input.wav';wave.write_bytes(wav_bytes())
    payload=subprocess.run(['ffmpeg','-v','error','-i',str(wave),'-c:a','libopus','-f','webm','pipe:1'],capture_output=True,check=True).stdout
    with TestClient(s.create_app(tmp_path)) as client:
        response=client.post('/api/analyses',data={'mode':'C','transcript':'One two three. Four five six.'},files={'audio':('stream.webm',payload,'audio/webm')})
        assert response.status_code==200, response.text


def test_health_reports_active_reference_and_history_is_chronological(tmp_path):
    folder=tmp_path/'data/reference';folder.mkdir(parents=True)
    (folder/'gettysburg__excl-none.json').write_text(json.dumps({'reference_version':'active-version'}))
    jobs=tmp_path/'data/app/jobs';jobs.mkdir(parents=True)
    for aid,order in [('zzzz',1),('aaaa',2)]:
        (jobs/f'{aid}.json').write_text(json.dumps({'analysis_id':aid,'status':'done','created_order':order,'analysis':{'recording_id':'rid','text_id':'gettysburg','mode':'A','scores':{'overall':9.0}}}))
    with TestClient(s.create_app(tmp_path)) as client:
        assert client.get('/api/health').json()['reference_version']['gettysburg__excl-none']=='active-version'
        assert [r['analysis_id'] for r in client.get('/api/history').json()]==['zzzz','aaaa']


def test_baseline_segment_rejects_partial_phrase_and_plays_exact_matching_words(tmp_path):
    """Same-words playback must never silently drop an unmatched participant word."""
    alignments = tmp_path / 'data/alignment'
    alignments.mkdir(parents=True)
    participant_words = [
        {'norm': 'it', 'start': 1.0, 'end': 1.2},
        {'norm': 'far', 'start': 1.2, 'end': 1.5},
    ]
    baseline_words = [{'norm': 'far', 'start': 4.0, 'end': 4.4}]
    (alignments / 'speech__user__take01.json').write_text(json.dumps({
        'audio': 'data/audio/hq/speech__user__take01.wav',
        'words': participant_words,
    }))
    (alignments / 'speech__reader__orig.json').write_text(json.dumps({
        'audio': 'data/audio/hq/speech__reader__orig.wav',
        'words': baseline_words,
    }))
    jobs = tmp_path / 'data/app/jobs'
    jobs.mkdir(parents=True)
    (jobs / 'partial.json').write_text(json.dumps({
        'analysis_id': 'partial',
        'status': 'done',
        'analysis': {
            'recording_id': 'speech__user__take01',
            'reference': {'baseline_recording_id': 'speech__reader__orig'},
        },
    }))
    with TestClient(s.create_app(tmp_path)) as client:
        response = client.get('/api/analyses/partial/baseline-segment?word_start=0&word_end=1')
        exact = client.get('/api/analyses/partial/baseline-segment?word_start=1&word_end=1')
    assert response.status_code == 404
    assert exact.status_code == 200
    assert exact.json() == {
        'recording_id': 'speech__reader__orig',
        'start': 4.0,
        'end': 4.4,
    }
