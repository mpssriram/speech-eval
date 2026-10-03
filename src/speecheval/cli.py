"""Command-line entry point for the speech evaluation pipeline."""

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


@app.command()
def fetch() -> None:
    """Fetch licensed source audio declared in the source manifest."""


@app.command()
def prepare() -> None:
    """Prepare source audio for feature extraction and alignment."""


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
