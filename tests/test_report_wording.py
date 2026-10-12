"""Presentation wording must disclose annotation and post-hoc result limits."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_report_discloses_visual_annotation_and_v2_tradeoff():
    report = (ROOT / 'docs/report/report.md').read_text()
    disclosure = ('Boundaries were placed visually from waveform and spectrogram '
                  'by an AI assistant (Claude), without listening; no human spot-check was done.')
    assert disclosure in report
    assert '**' + disclosure not in report
    assert 'v2 halves clean alarms (1.341 to 0.671 per min)' in report
    assert 'lowers recall (0.400 to 0.288)' in report
    assert 'F1 is effectively unchanged (0.190 to 0.193); v1 stays primary.' in report
    assert ('Human agreement was not measured: no independent raters were available; '
            'no AI or self-ratings were used.') in ' '.join(report.split())
    assert 'unavailable before' not in report


def test_pdf_footer_does_not_repeat_human_pending_status():
    renderer = (ROOT / 'docs/report/build_pdf.py').read_text()
    assert "canvas.drawString(56,27,'Frozen synthetic benchmark')" in renderer
    assert 'human evidence pending' not in renderer
