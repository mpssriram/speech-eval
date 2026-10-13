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
            '75.99–77.58 s, "it can": you paused 1.59 s between "it" and "can", '
            'where good readers do not pause (1.59 s longer, more than 10 SD above). '
            'It breaks the sentence.')
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
    assert 'you left no pause' in text
    assert 'pause 0.02 s' in text
    assert '10.00 SD below' in text
    assert region == before
    region['type'] = 'rushing'
    region['evidence'] = {'participant': 6., 'reference': 3., 'z': 4300.}
    text = explanation(region, ['one', 'two'], mode='B')
    assert '6.0 syllables/s' in text and 'averaged 3.0' in text
    assert 'your previous take' in text and 'more than 10 SD above' in text
    assert not re.search(r'\d[eE][+-]\d', text)
