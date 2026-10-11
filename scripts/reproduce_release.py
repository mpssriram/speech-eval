"""Explicit post-hoc report-status adapter around unchanged frozen reproduction."""
from pathlib import Path
import logging

from speecheval import reproduce as frozen
from speecheval.release_report_check import compare_release_report_numbers


def main() -> None:
    """Only replace the narrative-number checker, restoring it even on failure."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    logging.warning('Post-hoc release REPORT adapter: unpublished Human-A/B sections excluded; frozen synthetic/scoring/C checks unchanged')
    original = frozen.compare_report_numbers
    try:
        frozen.compare_report_numbers = compare_release_report_numbers
        frozen.run(Path.cwd())
    finally:
        frozen.compare_report_numbers = original


if __name__ == '__main__':
    main()
