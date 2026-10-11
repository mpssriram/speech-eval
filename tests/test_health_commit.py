"""Health build provenance on real empty/committed Git fixtures, never audio."""
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
from speecheval.service import create_app


def init_repo(root: Path) -> None:
    subprocess.run(['git','init',str(root)],check=True,capture_output=True)


def test_health_uses_build_environment_when_head_is_unavailable(tmp_path,monkeypatch):
    init_repo(tmp_path)
    expected='a'*40
    monkeypatch.setenv('SPEECHEVAL_GIT_COMMIT',expected)
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/api/health').json()['git_commit']==expected


def test_health_does_not_report_literal_head_for_unborn_repository(tmp_path,monkeypatch):
    init_repo(tmp_path)
    monkeypatch.delenv('SPEECHEVAL_GIT_COMMIT',raising=False)
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/api/health').json()['git_commit'] is None


def test_health_prefers_actual_checkout_over_stale_environment(tmp_path,monkeypatch):
    init_repo(tmp_path)
    (tmp_path/'version.txt').write_text('synthetic Git metadata fixture\n')
    subprocess.run(['git','-C',str(tmp_path),'add','version.txt'],check=True)
    subprocess.run(['git','-C',str(tmp_path),'-c','user.name=Fixture',
                    '-c','user.email=fixture@example.invalid','commit','-m','fixture'],
                   check=True,capture_output=True)
    expected=subprocess.check_output(['git','-C',str(tmp_path),'rev-parse','HEAD'],text=True).strip()
    monkeypatch.setenv('SPEECHEVAL_GIT_COMMIT','b'*40)
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/api/health').json()['git_commit']==expected


def test_health_uses_environment_even_without_git_executable(tmp_path,monkeypatch):
    monkeypatch.setenv('PATH',str(tmp_path))
    monkeypatch.setenv('SPEECHEVAL_GIT_COMMIT','c'*40)
    with TestClient(create_app(tmp_path)) as client:
        response=client.get('/api/health')
        assert response.status_code==200
        assert response.json()['git_commit']=='c'*40


def test_compose_passes_commit_to_both_image_builds():
    import yaml
    root=Path(__file__).resolve().parents[1]
    compose=yaml.safe_load((root/'docker-compose.yml').read_text())
    for name in ('api','tools'):
        assert compose['services'][name]['build']['args']['GIT_COMMIT']=='${SPEECHEVAL_GIT_COMMIT:-}'
    dockerfile=(root/'Dockerfile').read_text()
    assert 'ARG GIT_COMMIT' in dockerfile
    assert 'ENV SPEECHEVAL_GIT_COMMIT=${GIT_COMMIT}' in dockerfile
    makefile=(root/'Makefile').read_text()
    assert 'SPEECHEVAL_GIT_COMMIT ?= $(shell git rev-parse HEAD)' in makefile
    assert 'export SPEECHEVAL_GIT_COMMIT' in makefile
