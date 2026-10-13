"""Presentation changes must not alter frozen numeric evidence or stored outputs."""
import copy
import json
import re

from fastapi.testclient import TestClient
from speecheval import service


def test_cached_pause_is_readable_without_rewriting_scientific_json(tmp_path):
    region = {'type': 'awkward_pause', 'start': 75.99, 'end': 77.58,
              'word_start': 0, 'word_end': 1, 'severity': 4, 'tags': [],
              'evidence': {'participant': 1.59, 'reference': 6.9e-18, 'z': 6046.},
              'explanation': 'old 6.9e-18 s; 6e+03 SD above'}
    analysis = {'mode': 'A', 'recording_id': 'example', 'regions': [region]}
    job = {'status': 'done', 'analysis_id': 'example', 'analysis': analysis}
    path = tmp_path / 'data/app/jobs/example.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(job))
    alignment = tmp_path / 'data/alignment/example.json'
    alignment.parent.mkdir(parents=True)
    alignment.write_text(json.dumps({'words': [{'text': 'it'}, {'text': 'can'}]}))
    before = path.read_bytes()
    with TestClient(service.create_app(tmp_path)) as client:
        result = client.get('/api/analyses/example').json()['analysis']['regions'][0]
        assert result['display_explanation'] == (
            'Awkward pause · 75.99–77.58 s · "it can"\n'
            'What happened: You paused in the middle of a phrase.\n'
            "Measured: pause after 'it': 1.59 s (you) vs no pause (good readers)\n"
            "How far off: 1.59 s longer, which is more than 10 SD above the good readers' average. Flags start at 3.5 SD.\n"
            'Why it matters: It breaks the sentence.')
        assert result['evidence'] == region['evidence']
        assert result['explanation'] == region['explanation']
    assert path.read_bytes() == before


def test_display_pause_cutoff_z_cutoff_and_fixed_point_numbers():
    from speecheval.display import explanation
    region = {'type': 'missing_pause', 'start': 1., 'end': 2.,
              'word_start': 0, 'word_end': 1, 'tags': [],
              'evidence': {'participant': .019, 'reference': .02, 'z': -10.}}
    before = copy.deepcopy(region)
    text = explanation(region, ['one', 'two'])
    assert 'none (you)' in text
    assert 'vs 0.02 s' in text
    assert '10.0 SD below' in text
    assert region == before
    region['type'] = 'rushing'
    region['evidence'] = {'participant': 6., 'reference': 3., 'z': 4300.}
    text = explanation(region, ['one', 'two'], mode='B')
    assert '6.0 syllables per second' in text and 'vs 3.0' in text
    assert 'your earlier take' in text and 'more than 10 SD above' in text
    assert not re.search(r'\d[eE][+-]\d', text)

def test_display_uses_root_configuration_and_preserves_cached_job(tmp_path):
    from speecheval.display import explanation
    region={'type':'missing_pause','start':1.,'end':2.,'word_start':0,'word_end':1,'tags':[],
            'evidence':{'participant':.07,'reference':.6,'z':-3.14},'explanation':'legacy'}
    root=tmp_path
    path=root/'data/app/jobs/example.json';path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'status':'done','analysis_id':'example','analysis':{'mode':'B','recording_id':'example','regions':[region]}}))
    alignment=root/'data/alignment/example.json';alignment.parent.mkdir(parents=True)
    alignment.write_text(json.dumps({'words':[{'text':'one'},{'text':'two'}]}))
    config=root/'configs/detector.yaml';config.parent.mkdir();config.write_text('k: {missing_pause: 4.1}\n')
    before=path.read_bytes()
    with TestClient(service.create_app(root)) as client:
        result=client.get('/api/analyses/example').json()['analysis']['regions'][0]
    assert 'Flags start at 4.1 SD.' in result['display_explanation']
    assert 'Your pause was too short' in result['display_explanation']
    assert '0.07 s (you)' in result['display_explanation']
    assert 'the your' not in result['display_explanation']
    assert result['evidence']==region['evidence']
    assert path.read_bytes()==before


def test_display_halfway_rounding_matches_browser_fixed_point():
    from speecheval.display import explanation
    region={'type':'awkward_pause','start':4.255,'end':10.645,'word_start':0,'word_end':1,'tags':[],
            'evidence':{'participant':.885,'reference':.825,'z':3.45}}
    text=explanation(region,['one','two'],threshold=3.5)
    assert text.startswith('Awkward pause · 4.26–10.65 s · "one two"')
    assert "pause after 'one': 0.89 s (you) vs 0.83 s (good readers)" in text
    assert '0.06 s longer, which is 3.5 SD above' in text
