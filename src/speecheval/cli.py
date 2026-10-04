"""Command-line entry point for the speech evaluation pipeline."""

import logging
from pathlib import Path

import typer

app = typer.Typer(help="Deterministic speech-delivery evaluation pipeline.")
transcripts_app = typer.Typer(help="Build and compare speech transcripts.")
gold_app = typer.Typer(help="Prepare human-labelled alignment gold data.")
evaluate_app = typer.Typer(help="Evaluate aligners and detectors.")
report_app = typer.Typer(help="Generate quality-assurance reports.")

app.add_typer(transcripts_app, name="transcripts")
app.add_typer(gold_app, name="gold")
app.add_typer(evaluate_app, name="evaluate")
app.add_typer(report_app, name="report")


@app.callback()
def main() -> None:
    """Configure process-wide CLI logging."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


@app.command()
def fetch(
    manifest: Path = typer.Option(Path("data/manifest/sources.yaml"), exists=True, dir_okay=False),
    output: Path = typer.Option(Path("data/manifest/raw_files.csv"), dir_okay=False),
) -> None:
    """Fetch licensed source audio declared in the source manifest."""
    from speecheval.sources import fetch_sources

    fetch_sources(manifest, output)


@app.command()
def prepare(force: bool = typer.Option(False, help="Overwrite existing prepared audio.")) -> None:
    """Prepare source audio for feature extraction and alignment."""
    from speecheval.prepare import prepare_recordings

    prepare_recordings(force=force)


@app.command()
def align() -> None:
    """Run forced alignment for prepared recordings."""


@transcripts_app.command("diff")
def transcripts_diff() -> None:
    """Compare frozen ASR output with as-spoken transcripts."""


@gold_app.command("prepare")
def gold_prepare() -> None:
    """Prepare TextGrids for manual gold-boundary annotation."""


@evaluate_app.command("alignment")
def evaluate_alignment() -> None:
    """Evaluate word-boundary alignment against human gold data."""


@report_app.command("alignment")
def report_alignment() -> None:
    """Generate the alignment quality-assurance report."""


if __name__ == "__main__":
    app()
