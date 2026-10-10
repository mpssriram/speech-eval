"""Release scope and report-diff checks must not silently turn into cached success."""
from pathlib import Path
import os
import subprocess
import pytest

from speecheval.reproduce import numeric_claims, selected_rows, compare_report_numbers


def test_quick_selects_exactly_three_frozen_gettysburg_test_readers():
    rows=[{'text_id':text,'speaker_slug':speaker,'split':split,'recording_id':f'{text}__{speaker}__orig'}
          for text,speaker,split in [('gettysburg','lv_sa','test'),('gettysburg','lv_tg','test'),
                                    ('gettysburg','lv_wt','test'),('gettysburg','lv_mk','train'),('o_captain','lv_ss','test')]]
    assert len(selected_rows(rows,True))==3
    with pytest.raises(ValueError,match='three'):
        selected_rows(rows[:2],True)


def test_report_numbers_ignore_links_and_commit_but_detect_changed_ci(tmp_path):
    original='# Phase 6\nCommit: `a123456789abcdef`.\n| overall | 0.190 [0.156, 0.223] |\n![chart](img/recall_s3.png)\n'
    assert numeric_claims(original)==['6','0.190','0.156','0.223']
    left=tmp_path/'original.md';right=tmp_path/'reproduced.md'
    left.write_text(original);right.write_text(original.replace('a123456789abcdef','abcdef0123456789'))
    compare_report_numbers(left,right)
    right.write_text(original.replace('0.223','0.224'))
    with pytest.raises(ValueError,match='number 4'):
        compare_report_numbers(left,right)


def test_make_release_targets_are_cpu_container_commands():
    root=Path(__file__).resolve().parents[1]
    for name in ('up','test','reproduce-quick','reproduce'):
        result=subprocess.run(['make','-n',name],cwd=root,text=True,capture_output=True,check=True)
        assert 'docker compose' in result.stdout
        if name!='up':
            assert 'mkdir -p reports/reproduced' in result.stdout
            assert result.stdout.index('mkdir -p reports/reproduced')<result.stdout.index('docker compose')
    assert '--quick' in subprocess.check_output(['make','-n','reproduce-quick'],cwd=root,text=True)


def test_both_numeric_reports_are_part_of_the_release_checkout():
    root=Path(__file__).resolve().parents[1]
    assert (root/'reports/phase06_results.md').is_file()
    assert (root/'reports/phase07_validation.md').is_file()
    assert (root/'reports/phase08_mode_c.md').is_file()


def test_container_model_downloads_are_pinned_and_skip_github_api_discovery():
    dockerfile=(Path(__file__).resolve().parents[1]/'Dockerfile').read_text()
    assert 'mfa model download' not in dockerfile
    for tag in ('acoustic-english_mfa-v3.1.0', 'dictionary-english_us_mfa-v3.1.0',
                'g2p-english_us_mfa-v3.0.0'):
        assert f'releases/download/{tag}/' in dockerfile
    assert 'sha256sum -c /tmp/mfa_models.sha256' in dockerfile


def test_make_does_not_export_host_only_tmpdir_to_docker():
    root=Path(__file__).resolve().parents[1]
    probe_env=dict(os.environ);probe_env.pop('TMPDIR',None)
    result=subprocess.run(['make', '--no-print-directory', '--eval=_release_env_probe:;@printenv TMPDIR || true',
                           '_release_env_probe'],cwd=root,env=probe_env,text=True,
                          capture_output=True,check=True)
    assert result.stdout.strip()==''
