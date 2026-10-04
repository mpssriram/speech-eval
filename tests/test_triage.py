from pathlib import Path

import pytest

from speecheval.triage import (
    classify_edit,
    equivalent_text,
    parse_gettysburg_versions,
    select_version,
    write_review_html,
)
import yaml


@pytest.fixture
def equivalents() -> dict:
    return yaml.safe_load((Path(__file__).parents[1] / "configs/text_equiv.yaml").read_text())


@pytest.mark.parametrize(("left", "right"), [
    ("Oh Captain", "O Captain"), ("OK", "okay"), ("35", "thirty five"),
    ("10,000", "ten thousand"), ("to-day", "today"),
    ("battle field", "battlefield"), ("honoured", "honored"),
    ("weather’d", "weathered"), ("we’re", "we are"),
    ("can not", "cannot"),
])
def test_equivalence_rules(left: str, right: str, equivalents: dict) -> None:
    assert equivalent_text(left, equivalents) == equivalent_text(right, equivalents)


def test_equivalence_does_not_hide_content_changes(equivalents: dict) -> None:
    assert equivalent_text("were", equivalents) != equivalent_text("we are", equivalents)
    assert equivalent_text("this", equivalents) != equivalent_text("that", equivalents)


def test_edit_classification(equivalents: dict) -> None:
    assert classify_edit("replace", "colour", "color", equivalents, {}) == "IGNORE"
    assert classify_edit("replace", "note", "not", equivalents, {"note": [["N", "OW", "T"]], "not": [["N", "AA", "T"]]}) == "LIKELY_ASR"
    assert classify_edit("replace", "men", "women", equivalents, {}) == "LISTEN"
    assert classify_edit("insert", "", "and", equivalents, {}) == "LISTEN"
    assert classify_edit("delete", "here", "", equivalents, {}) == "LISTEN"


def test_version_threshold_and_bliss_tie() -> None:
    assert select_version({"bliss": 8, "hay": 5, "everett": 5}) == "hay"
    assert select_version({"bliss": 8, "hay": 6}) == "bliss"
    assert select_version({"bliss": 5, "hay": 5}) == "bliss"


def test_extract_only_manuscript_bold_blocks() -> None:
    names = ("Nicolay", "Hay", "Everett", "Bancroft", "Bliss")
    page = "".join(f"<b>{name} Copy</b><p>Background.</p><b>Four score<p>shall not perish from the earth.</b><p>" for name in names)
    versions = parse_gettysburg_versions(page)
    assert set(versions) == {name.lower() for name in names}
    assert all("Background" not in text and text.endswith("earth.") for text in versions.values())


def test_html_escapes_text_and_uses_relative_audio(tmp_path: Path) -> None:
    item = {"recording_id": "example", "start_s": 0.4, "transcript": "<script>", "asr": "&", "class": "LISTEN"}
    write_review_html(tmp_path / "index.html", [item])
    text = (tmp_path / "index.html").read_text()
    assert "../audio/hq/example.wav" in text
    assert "&lt;script&gt;" in text
    assert 'data-start="0.000"' in text
    assert 'data-end="2.900"' in text


def test_triage_preserves_reviewed_transcripts_and_caches_secondary(tmp_path: Path, monkeypatch, equivalents: dict) -> None:
    import json
    import speecheval.triage as triage

    for directory in ("configs", "data/manifest", "data/transcripts/as_spoken", "data/alignment/asr", "data/audio/hq", "reports"):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    rid = "gettysburg__reader__orig"
    paths = {"alignment": "data/alignment", "hq": "data/audio/hq", "transcripts_as_spoken": "data/transcripts/as_spoken"}
    (tmp_path / "configs/default.yaml").write_text(yaml.safe_dump({"paths": paths}))
    (tmp_path / "configs/text_equiv.yaml").write_text(yaml.safe_dump(equivalents))
    (tmp_path / "data/manifest/recordings.csv").write_text(
        f"recording_id,text_id,cut_start_s,cut_end_s,duration_s\n{rid},gettysburg,0,3,3\n"
    )
    transcript = tmp_path / f"data/transcripts/as_spoken/{rid}.txt"
    original = "# reviewed: yes\nWe help men.\n"
    transcript.write_text(original)
    words = [{"word": word, "start": float(i), "end": i + 0.4} for i, word in enumerate(["We", "help", "women"])]
    (tmp_path / f"data/alignment/asr/{rid}.json").write_text(json.dumps({"words": words}))
    (tmp_path / f"data/audio/hq/{rid}.wav").write_bytes(b"synthetic audio placeholder")
    monkeypatch.setattr(triage, "fetch_versions", lambda root: {name: "We help women." if name == "hay" else "A wholly different text today." for name in triage.VERSIONS})
    monkeypatch.setattr(triage, "build_transcript_diffs", lambda root: None)
    calls = []
    monkeypatch.setattr(triage.SecondaryASR, "transcribe", lambda self, audio, start, end: calls.append((start, end)) or "help women")
    first = triage.triage_transcripts(tmp_path)
    audit_bytes = (tmp_path / "data/review/triage.json").read_bytes()
    second = triage.triage_transcripts(tmp_path)
    assert transcript.read_text() == original
    assert first["listen_items"] == second["listen_items"] == 0
    assert first["counts"]["LIKELY_REAL"] == 1
    assert len(calls) == 1
    assert (tmp_path / "data/review/triage.json").read_bytes() == audit_bytes
    choices = yaml.safe_load((tmp_path / "data/manifest/transcript_versions.yaml").read_text())
    assert choices[rid]["selected_version"] == "hay"
    assert choices[rid]["reviewed_preserved"] is True
