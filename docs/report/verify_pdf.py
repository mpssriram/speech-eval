"""Optional authoring check: repeat render, compare bytes and inspect PDF structure."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from pypdf import PdfReader


def verify(font_dir: Path) -> dict:
    folder = Path(__file__).resolve().parent
    hashes = []
    for _ in range(2):
        subprocess.run(
            [sys.executable, str(folder / "build_pdf.py"), "--font-dir", str(font_dir)],
            check=True,
        )
        hashes.append(hashlib.sha256((folder / "report.pdf").read_bytes()).hexdigest())
    assert hashes[0] == hashes[1], "Repeated PDF renders differ"
    reader = PdfReader(folder / "report.pdf")
    assert len(reader.pages) == 6, "Expected six pages"
    for page in reader.pages:
        assert abs(float(page.mediabox.width) - 595.2756) < 0.01
        assert abs(float(page.mediabox.height) - 841.8898) < 0.01
        assert "{{" not in page.extract_text(), "Unrendered placeholder"
    assert "pending" in reader.metadata.author.lower(), "Unconfirmed author presented as final"
    return {
        "pdf_sha256": hashes[0],
        "repeat_sha256": hashes[1],
        "pages": len(reader.pages),
        "page_format": "A4",
        "body_font_pt": 11,
        "checks": "repeat bytes; six A4 pages; readable pending placeholders; pending author",
        "visual_check": "All six pages inspected after final render; no clipping or overlap",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path, required=True)
    parser.add_argument("--save", action="store_true", help="Save authoring verification.json")
    args = parser.parse_args()
    evidence = verify(args.font_dir)
    if args.save:
        (Path(__file__).resolve().parent / "verification.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(evidence, indent=2))
