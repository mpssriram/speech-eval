"""Drive transport and optional takes fail closed at the release boundary."""
import json
import shutil
import sys
from types import SimpleNamespace

import pytest

from test_dataset_release import fixture_release, script


def drive_config(root):
    path = root / 'configs/dataset.yaml'
    config = json.loads(path.read_text())
    config['drive_file_id'] = 'public-main-id'
    path.write_text(json.dumps(config))
    return path, config


def test_drive_id_imports_verified_payload(tmp_path, monkeypatch):
    root, archive, payload = fixture_release(tmp_path)
    drive_config(root)
    def download(*, id, output, **kwargs):
        if id != 'public-main-id': raise AssertionError('Wrong Drive file ID')
        shutil.copyfile(archive, output)
        return output
    monkeypatch.setitem(sys.modules, 'gdown', SimpleNamespace(download=download))
    assert script('fetch_data').fetch(root) == 2
    for name, body in payload.items():
        assert (root / 'data' / name).read_bytes() == body


def test_bad_drive_download_installs_nothing(tmp_path, monkeypatch):
    root, _, _ = fixture_release(tmp_path)
    drive_config(root)
    def download(*, output, **kwargs):
        from pathlib import Path
        Path(output).write_bytes(b'Google HTML error or wrong archive')
        return output
    monkeypatch.setitem(sys.modules, 'gdown', SimpleNamespace(download=download))
    with pytest.raises(ValueError, match='SHA'):
        script('fetch_data').fetch(root)
    assert not (root / 'data/raw').exists()


def test_rejected_human_link_is_actionable_even_if_main_is_present(tmp_path):
    root, archive, _ = fixture_release(tmp_path)
    module = script('fetch_data')
    module.fetch(root, archive)
    path, config = drive_config(root)
    config['human_takes'] = {'status': 'upload_required'}
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='human.*from-local|from-local.*human'):
        module.fetch(root, with_human_takes=True)
