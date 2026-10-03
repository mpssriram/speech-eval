from typer.testing import CliRunner

from speecheval.cli import app


def test_help_lists_phase_one_commands() -> None:
    """Removing any Phase 1 command from the CLI must break this test."""
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("fetch", "prepare", "transcripts", "align", "gold", "evaluate", "report"):
        assert command in result.stdout
