"""Characterize retained limitations without changing frozen inference behavior."""
from pathlib import Path


def test_interpolation_warning_survives_while_word_extra_flag_is_dropped():
    from speecheval.align import base
    text='one two three'
    output=[{'word':'one','start':.1,'end':.4},{'word':'three','start':.8,'end':1.}]
    raw,warnings=base.map_words(text,output,1.2)
    assert raw[1]['interpolated'] is True
    payload=base.make_alignment('synthetic__reader__orig',text,
        [{'i':0,'char_start':0,'char_end':len(text)}],output,1.2,'mfa')
    assert 'interpolated' not in payload['words'][1]
    assert payload['warnings']==warnings==[{'type':'interpolated','word':1}]


def test_readme_documents_plotly_warning_and_retained_limitations():
    root=Path(__file__).resolve().parents[1]
    readme=(root/'README.md').read_text()
    assert 'Plotly bundle-size warning' in readme
    assert 'harmless for correctness' in readme
    assert 'initial download/parse time' in readme
    assert 'interpolated' in readme and 'warnings' in readme
    assert '/home/sriram/Documents/MFA/pretrained_models' in readme
    assert 'no refactor' in readme


def test_docker_retains_the_documented_mfa_compatibility_paths():
    root=Path(__file__).resolve().parents[1]
    dockerfile=(root/'Dockerfile').read_text()
    assert 'ENV MFA_ROOT_DIR=/home/sriram/Documents/MFA' in dockerfile
    assert 'ln -s /opt/conda /home/sriram/miniforge3' in dockerfile
    assert 'pretrained_models/acoustic' in dockerfile
    assert 'pretrained_models/dictionary' in dockerfile
    assert 'pretrained_models/g2p' in dockerfile
