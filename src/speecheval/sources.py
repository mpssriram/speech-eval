"""Licensed source manifest loading and downloads."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Literal

import internetarchive
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

LOGGER = logging.getLogger(__name__)


class TextSpec(BaseModel):
    """Metadata for one canonical speech text."""

    model_config = ConfigDict(extra="allow")

    title: str
    author: str


class DownloadSpec(BaseModel):
    """Download instructions for one source."""

    model_config = ConfigDict(extra="allow")

    method: Literal["ia_item", "manual"]
    item: str | None = None
    formats: list[str] = Field(default_factory=list)
    expected_file: str | None = None


class SourceSpec(BaseModel):
    """Validated source recording or collection metadata."""

    model_config = ConfigDict(extra="allow")

    id: str
    kind: Literal["single", "collection"]
    text_id: str | None = None
    speaker_slug: str | None = None
    download: DownloadSpec | None = None
    license: str
    status: str | None = None

    @model_validator(mode="after")
    def active_source_is_complete(self) -> "SourceSpec":
        """Require the fields needed to fetch every active source."""
        if self.status != "later" and (self.text_id is None or self.download is None):
            raise ValueError("active sources require text_id and download instructions")
        return self


class SourceManifest(BaseModel):
    """Top-level source manifest."""

    texts: dict[str, TextSpec]
    sources: list[SourceSpec]

    @property
    def day_one_sources(self) -> list[SourceSpec]:
        """Return active sources in manifest order."""
        return [source for source in self.sources if source.status != "later"]


def load_manifest(path: Path) -> SourceManifest:
    """Load and validate a UTF-8 YAML source manifest."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SourceManifest.model_validate(data)


def _reading_key(file_metadata: dict[str, Any]) -> str:
    name = Path(str(file_metadata.get("name", ""))).stem.lower()
    return re.sub(r"_64kb$", "", name)


def choose_collection_files(
    files: list[dict[str, Any]], allowed_formats: list[str]
) -> list[dict[str, Any]]:
    """Choose one highest-quality audio file for each collection reading."""
    quality = {"VBR MP3": 0, "Ogg Vorbis": 1, "64Kbps MP3": 2}
    allowed = set(allowed_formats)
    chosen: dict[str, dict[str, Any]] = {}
    for metadata in files:
        audio_format = str(metadata.get("format", ""))
        if audio_format not in allowed:
            continue
        key = _reading_key(metadata)
        current = chosen.get(key)
        if current is None or quality.get(audio_format, 99) < quality.get(
            str(current.get("format", "")), 99
        ):
            chosen[key] = metadata
    return [chosen[key] for key in sorted(chosen)]


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value or "unknown"


def speaker_slug_from_file(file_metadata: dict[str, Any], fallback_index: int) -> str:
    """Derive a stable LibriVox reader slug from file-level metadata."""
    for field in ("title", "artist", "creator"):
        value = str(file_metadata.get(field) or "")
        match = re.search(r"read by\s+(.+?)(?:\s*[-–—|]|$)", value, flags=re.IGNORECASE)
        if match:
            return f"lv_{_slugify(match.group(1))}"
    stem = _reading_key(file_metadata)
    suffix = stem.rsplit("_", 1)[-1]
    if suffix and suffix not in {"speech", "audio"}:
        return f"lv_{_slugify(suffix)}"
    LOGGER.warning("Reader metadata unavailable for %s", file_metadata.get("name"))
    return f"lv_reader{fallback_index:02d}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _probe_audio(path: Path) -> tuple[int, int, float]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate,channels:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    stream = payload["streams"][0]
    return int(stream["sample_rate"]), int(stream["channels"]), float(payload["format"]["duration"])


def _row(source: SourceSpec, speaker_slug: str, path: Path, root: Path) -> dict[str, str | int | float]:
    sample_rate, channels, duration = _probe_audio(path)
    assert source.text_id is not None
    return {
        "source_id": source.id,
        "recording_id": f"{source.text_id}__{speaker_slug}__orig",
        "speaker_slug": speaker_slug,
        "raw_path": path.relative_to(root).as_posix(),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "original_sample_rate": sample_rate,
        "channels": channels,
        "duration_s": round(duration, 3),
    }


def fetch_sources(
    manifest_path: Path = Path("data/manifest/sources.yaml"),
    output_path: Path = Path("data/manifest/raw_files.csv"),
) -> list[dict[str, str | int | float]]:
    """Download active licensed sources and write a deterministic raw-file manifest."""
    root = Path.cwd().resolve()
    manifest = load_manifest(manifest_path)
    rows: list[dict[str, str | int | float]] = []
    for source in manifest.day_one_sources:
        assert source.download is not None
        if source.download.method == "manual":
            if source.download.expected_file is None:
                LOGGER.warning("Manual source %s has no expected_file", source.id)
                continue
            path = root / source.download.expected_file
            if not path.is_file():
                LOGGER.warning("Manual source missing: %s", path)
                continue
            rows.append(_row(source, source.speaker_slug or "unknown", path, root))
            continue

        assert source.download.item is not None
        item = internetarchive.get_item(source.download.item)
        selected = choose_collection_files(list(item.files), source.download.formats)
        destination = root / "data" / "raw" / source.id
        destination.mkdir(parents=True, exist_ok=True)
        for index, metadata in enumerate(selected, start=1):
            name = str(metadata["name"])
            path = destination / Path(name).name
            if not path.exists():
                LOGGER.info("Downloading %s/%s", source.download.item, name)
                item.get_file(name).download(file_path=str(path))
            speaker_slug = speaker_slug_from_file(metadata, index)
            rows.append(_row(source, speaker_slug, path, root))

    rows.sort(key=lambda row: str(row["recording_id"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_id",
        "recording_id",
        "speaker_slug",
        "raw_path",
        "sha256",
        "bytes",
        "original_sample_rate",
        "channels",
        "duration_s",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    LOGGER.info("Wrote %d recordings to %s", len(rows), output_path)
    return rows
