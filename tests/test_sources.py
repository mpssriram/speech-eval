from pathlib import Path

import pytest
from pydantic import ValidationError

from speecheval.sources import (
    SourceManifest,
    choose_collection_files,
    load_manifest,
    speaker_slug_from_file,
)


def test_manifest_rejects_unlicensed_day_one_source() -> None:
    """Removing a Day 1 source license must make validation fail."""
    with pytest.raises(ValidationError):
        SourceManifest.model_validate(
            {
                "texts": {"sample": {"title": "Sample", "author": "A"}},
                "sources": [
                    {
                        "id": "sample_source",
                        "kind": "single",
                        "text_id": "sample",
                        "speaker_slug": "speaker",
                        "download": {"method": "manual", "expected_file": "data/raw/a.mp3"},
                    }
                ],
            }
        )


def test_load_manifest_skips_later_sources(tmp_path: Path) -> None:
    """Changing status filtering to include later sources must break this test."""
    manifest_path = tmp_path / "sources.yaml"
    manifest_path.write_text(
        """
texts:
  sample: {title: Sample, author: A}
sources:
  - id: now
    kind: single
    text_id: sample
    speaker_slug: speaker
    download: {method: manual, expected_file: data/raw/now.mp3}
    license: Public domain
  - id: later
    kind: single
    text_id: sample
    speaker_slug: speaker
    download: {method: manual, expected_file: data/raw/later.mp3}
    license: Public domain
    status: later
""".lstrip(),
        encoding="utf-8",
    )

    manifest = load_manifest(manifest_path)

    assert [source.id for source in manifest.day_one_sources] == ["now"]


def test_collection_prefers_one_vbr_mp3_per_reading() -> None:
    """Selecting duplicate or lower-quality formats must break this test."""
    files = [
        {"name": "speech_amb.ogg", "format": "Ogg Vorbis", "title": "01 - read by AMB"},
        {"name": "speech_amb_64kb.mp3", "format": "64Kbps MP3", "title": "01 - read by AMB"},
        {"name": "speech_amb.mp3", "format": "VBR MP3", "title": "01 - read by AMB"},
        {"name": "speech_dj.mp3", "format": "VBR MP3", "title": "02 - read by DJ"},
        {"name": "cover.jpg", "format": "JPEG"},
    ]

    selected = choose_collection_files(files, ["64Kbps MP3", "VBR MP3", "Ogg Vorbis"])

    assert [item["name"] for item in selected] == ["speech_amb.mp3", "speech_dj.mp3"]


def test_speaker_slug_uses_read_by_title() -> None:
    """Losing reader attribution in file metadata must break this test."""
    assert speaker_slug_from_file(
        {"name": "speech_amb.mp3", "title": "01 - The Speech - read by AMB"}, 1
    ) == "lv_amb"
