"""The separate human release binds eight WAVs and frozen labels to repo bytes."""
import json
import zipfile

import pytest

from test_dataset_release import script


def inputs(root):
    rows = []
    for text in ('gettysburg', 'reagan_challenger'):
        for n in range(1, 5):
            rid = f'{text}__user__take{n:02}'
            for name, body in ((f'human/raw/{rid}.wav', b'WAV'),
                               (f'human/transcripts/{rid}.txt', b'words')):
                path = root / 'data' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
            rows.append({'take_id': rid, 'mode': 'A', 'detector': 'v1',
                         'intended_regions': [], 'excluded_from_scoring': n == 4,
                         'recording_id': rid, 'trim_start_s': 0})
    for name, body in {'CONSENT.md': 'consent', 'raw/notes.md': 'notes',
                       'evaluation.json': json.dumps({'results': rows})}.items():
        (root / 'data/human' / name).write_text(body)
    (root / 'data/release').mkdir()


def test_takes_zip_contains_repo_inputs_and_repeats(tmp_path):
    inputs(tmp_path)
    module = script('build_human_release')
    one = tmp_path / 'one.zip'; two = tmp_path / 'two.zip'
    result = module.build(tmp_path, one)
    module.build(tmp_path, two)
    assert one.read_bytes() == two.read_bytes()
    with zipfile.ZipFile(one) as z:
        assert len([n for n in z.namelist() if n.endswith('.wav')]) == 8
        assert len([n for n in z.namelist() if '/labels/' in n]) == 8
        assert z.read('human/CONSENT.md') == b'consent'
        assert 'human/hashes.sha256' in z.namelist()
    assert result['payload_files'] == 28


def test_missing_take_blocks_packaging(tmp_path):
    inputs(tmp_path)
    (tmp_path / 'data/human/raw/gettysburg__user__take04.wav').unlink()
    with pytest.raises(ValueError, match='Missing'):
        script('build_human_release').build(tmp_path, tmp_path / 'out.zip')
    assert not (tmp_path / 'out.zip').exists()


def test_human_builder_cannot_replace_main_archive(tmp_path):
    inputs(tmp_path)
    main = tmp_path / 'data/release/speech-eval-dataset-v1.zip'
    main.write_bytes(b'IMMUTABLE')
    with pytest.raises(ValueError, match='main'):
        script('build_human_release').build(tmp_path, main)
    assert main.read_bytes() == b'IMMUTABLE'
