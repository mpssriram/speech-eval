"""Published synthetic numbers remain checked despite pending human status edits."""
import pytest


def test_unpublished_human_sections_are_separate_from_frozen_benchmark(tmp_path):
    from speecheval.release_report_check import compare_release_report_numbers
    expected = tmp_path/'phase06_results.md'
    actual = tmp_path/'regenerated.md'
    benchmark = '# Phase 6\n## A-LOSO\n| F1 | 0.190 |\n'
    limitations = '## Limitations\nBootstrap 1,000 resamples.\n'
    expected.write_text(benchmark+'## Human-A\nEight unconfirmed takes.\n## Human-B\nPending B02–04.\n'+limitations)
    actual.write_text(benchmark+'## Human-A\nPending 12 takes.\n## Human-B\nPending 1 previous take.\n'+limitations)
    compare_release_report_numbers(expected,actual)
    actual.write_text(actual.read_text().replace('0.190','0.191'))
    with pytest.raises(ValueError,match='differs'):
        compare_release_report_numbers(expected,actual)
    actual.write_text(benchmark+'## Human-A\nPending.\n'+limitations.replace('1,000','2,000'))
    with pytest.raises(ValueError,match='differs'):
        compare_release_report_numbers(expected,actual)


def test_only_phase6_exact_human_sections_are_excluded(tmp_path):
    from speecheval.release_report_check import compare_release_report_numbers, synthetic_report_view
    text = '# Phase 6\n## Human-A\nPending 04.\n### Detail\nNo 8 counts.\n## A-LOSO\nF1 0.190.\n## Human-B\nPending 01.\n## Limitations\n1,000.\n'
    view = synthetic_report_view(text)
    assert '04' not in view and '01' not in view and 'No 8' not in view
    assert 'F1 0.190' in view and '1,000' in view
    assert '## Human-Accuracy\n0.123' in synthetic_report_view('## Human-Accuracy\n0.123')
    expected = tmp_path/'phase07_validation.md';actual = tmp_path/'actual.md'
    expected.write_text('## Human-A\n0.100\n');actual.write_text('## Human-A\n0.200\n')
    with pytest.raises(ValueError,match='differs'):
        compare_release_report_numbers(expected,actual)


def test_make_full_uses_explicit_release_adapter_not_new_scoring_path():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    makefile = (root/'Makefile').read_text()
    assert 'tools python scripts/reproduce_release.py' in makefile
    wrapper = (root/'scripts/reproduce_release.py').read_text()
    assert 'frozen.run(Path.cwd())' in wrapper
    assert 'finally:' in wrapper and 'frozen.compare_report_numbers = original' in wrapper


def test_adapter_restores_checker_on_failure(monkeypatch):
    from pathlib import Path
    import runpy
    from speecheval import reproduce as frozen
    original = frozen.compare_report_numbers
    namespace = runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/reproduce_release.py'))

    def fail(root):
        assert frozen.compare_report_numbers is not original
        raise RuntimeError('unit-test sentinel, not an evaluation')

    monkeypatch.setattr(frozen, 'run', fail)
    with pytest.raises(RuntimeError,match='unit-test sentinel'):
        namespace['main']()
    assert frozen.compare_report_numbers is original
