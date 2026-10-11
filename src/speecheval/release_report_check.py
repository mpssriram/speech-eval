"""Post-hoc release REPORT adapter; never alters frozen scoring/evaluation.

The public archive excludes human recordings. Human-A/B status paragraphs in
Phase6 can therefore change without becoming reproducible benchmark numbers.
Every other numeric claim, including limitations, remains strictly checked.
"""
from pathlib import Path
import re

from speecheval.reproduce import compare_report_numbers, numeric_claims


def synthetic_report_view(markdown: str) -> str:
    """Exclude only exact level-two Human-A/B sections and their subsections."""
    kept = []
    skip = False
    for line in markdown.splitlines(keepends=True):
        if re.match(r'^#{1,2} ', line):
            skip = bool(re.fullmatch(r'## Human-[AB]\s*', line))
        if not skip:
            kept.append(line)
    return ''.join(kept)


def compare_release_report_numbers(expected: Path, actual: Path) -> None:
    """Compare unchanged synthetic report numbers; other reports use frozen check."""
    if expected.name != 'phase06_results.md':
        compare_report_numbers(expected, actual)
        return
    left = numeric_claims(synthetic_report_view(expected.read_text()))
    right = numeric_claims(synthetic_report_view(actual.read_text()))
    for i in range(max(len(left), len(right))):
        a = left[i] if i < len(left) else '<missing>'
        b = right[i] if i < len(right) else '<missing>'
        if a != b:
            raise ValueError(f'{expected.name}: synthetic report number {i+1} differs: expected {a}, actual {b}')
