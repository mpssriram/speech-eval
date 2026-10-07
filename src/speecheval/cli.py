"""Command-line entry point for the speech evaluation pipeline."""

import logging
import os
from pathlib import Path

import typer

app = typer.Typer(help="Deterministic speech-delivery evaluation pipeline.")
transcripts_app = typer.Typer(help="Build and compare speech transcripts.")
gold_app = typer.Typer(help="Prepare human-labelled alignment gold data.")
evaluate_app = typer.Typer(help="Evaluate aligners and detectors.")
report_app = typer.Typer(help="Generate quality-assurance reports.")
features_app = typer.Typer(help="Extract acoustic features and speaker statistics.")
inject_app = typer.Typer(help="Generate labelled synthetic speech flaws.")
dataset_app = typer.Typer(help="Build the speaker-disjoint synthetic dataset.")
human_app = typer.Typer(help="Prepare user recording instructions without synthesizing voice.")
reference_app = typer.Typer(help="Build train-only robust reference distributions.")

app.add_typer(transcripts_app, name="transcripts")
app.add_typer(gold_app, name="gold")
app.add_typer(evaluate_app, name="evaluate")
app.add_typer(report_app, name="report")
app.add_typer(features_app, name="features")
app.add_typer(inject_app, name="inject")
app.add_typer(dataset_app, name="dataset")
app.add_typer(human_app, name="human")
app.add_typer(reference_app, name="reference")


@app.command("calibrate")
def calibrate() -> None:
    from speecheval.calibration import calibrate as run
    run()


@evaluate_app.command("final")
def evaluate_final() -> None:
    from speecheval.calibration import evaluate_final as run
    run()


@reference_app.command("build")
def reference_build() -> None:
    from speecheval.reference import build_reference,build_baselines
    for text in ('gettysburg','o_captain','jfk_rice','reagan_challenger'):build_reference(text)
    build_baselines(Path.cwd())


@app.command("analyze")
def analyze(audio: Path = typer.Argument(...,exists=True,dir_okay=False),
            text: str = typer.Option(...),mode: str = typer.Option('A'),
            transcript: Path | None = typer.Option(None,exists=True,dir_okay=False),
            exclude_speaker: str | None = typer.Option(None),
            previous: Path | None = typer.Option(None,exists=True,dir_okay=False),plot: bool = typer.Option(False)) -> None:
    from speecheval.pipeline import analyze as run
    run(audio,text,mode,transcript,exclude_speaker,previous,plot)


@app.command("analyze-batch")
def analyze_batch(split: str = typer.Option('dev'),setting: str = typer.Option('A-LOSO')) -> None:
    import csv
    from speecheval.pipeline import analyze as run
    if split not in ('train','dev','test'):raise typer.BadParameter('Unknown split')
    if setting not in ('A-LOSO','B-same-speaker'):raise typer.BadParameter('Unknown evaluation setting')
    root=Path.cwd()
    rows=list(csv.DictReader((root/'data/manifest/dataset_index.csv').open()))
    for row in rows:
        if row['split']!=split:continue
        if setting=='A-LOSO' and row['text_id'] in ('gettysburg','o_captain'):
            run(root/row['audio_path'],row['text_id'],exclude_speaker=row['speaker_slug'])
        elif setting=='B-same-speaker' and row['text_id'] in ('jfk_rice','reagan_challenger'):
            rid=f"{row['text_id']}__{row['speaker_slug']}__orig"
            run(root/row['audio_path'],row['text_id'],mode='B',previous=root/'data/audio/hq'/f'{rid}.wav')


@human_app.command("script")
def human_script() -> None:
    """Write the twelve recording instructions independently of dataset construction."""
    import yaml
    from speecheval.dataset import human_script as prepare
    root=Path.cwd()
    prepare(root,yaml.safe_load((root/'configs/flaws.yaml').read_text())['seed'])


@dataset_app.command("build")
def dataset_build(stage: str = typer.Option('all'), limit_sources: int = typer.Option(0,min=0)) -> None:
    """Generate, real-align and feature-extract reader batches; stages can resume."""
    from speecheval.dataset import dataset_build as build
    build(stage=stage,limit_sources=limit_sources)


@inject_app.command("preview")
def inject_preview(force: bool = typer.Option(False)) -> None:
    """Generate the preview plus the three-reader objective-effect matrix."""
    from speecheval.inject import inject_preview as generate
    generate(force=force)


@features_app.command("all")
@features_app.command("frames")
def features_all(force: bool = typer.Option(False)) -> None:
    """Extract the complete hash-bound feature bundle for promoted recordings."""
    from speecheval.features import features_all as extract
    extract(force=force)


@report_app.command("features")
def features_qa() -> None:
    """Refresh machine-readable QA and the overlay; no narrative phase report."""
    from speecheval.features import features_qa as qa
    qa()


@app.callback()
def main() -> None:
    """Configure process-wide CLI logging."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if os.environ.get("PYTHONPATH"):
        logging.getLogger(__name__).warning(
            "PYTHONPATH is non-empty; inherited packages (for example ROS 2) may interfere. "
            "Run with env -u PYTHONPATH for an isolated environment."
        )


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
def align(aligner: str = typer.Option('both'), force: bool = typer.Option(False), promote: bool = typer.Option(False), dictionary_experiment: bool = typer.Option(False, help='Run a candidate dictionary without adoption; cannot promote.')) -> None:
    """Run forced alignment for prepared recordings."""
    from speecheval.align.pipeline import run_alignment
    run_alignment(aligner,force,promote,dictionary_experiment)


@transcripts_app.command("diff")
def transcripts_diff() -> None:
    """Compare frozen ASR output with as-spoken transcripts."""
    from speecheval.transcripts import build_transcript_diffs

    build_transcript_diffs()


@transcripts_app.command("triage")
def transcripts_triage() -> None:
    """Select manuscript versions and prioritize human transcript review."""
    from speecheval.triage import triage_transcripts

    triage_transcripts()


@transcripts_app.command("verify")
def transcripts_verify() -> None:
    """Compare transcript candidates acoustically on deterministic CPU CTC emissions."""
    from speecheval.calibrated import verify_calibrated

    verify_calibrated()


@gold_app.command("prepare")
def gold_prepare() -> None:
    """Prepare TextGrids for manual gold-boundary annotation."""
    from speecheval.gold import prepare_gold
    prepare_gold()


@evaluate_app.command("alignment")
def evaluate_alignment(force: bool = typer.Option(False, help="Actually rerun both independent determinism passes.")) -> None:
    """Evaluate word boundaries against the supplied annotated reference."""
    from speecheval.evaluate import evaluate_alignment as evaluate
    evaluate(force=force)


@report_app.command("alignment")
def report_alignment() -> None:
    """Generate the alignment quality-assurance report."""
    from speecheval.alignment_qa import report_alignment as report
    report()


if __name__ == "__main__":
    app()
