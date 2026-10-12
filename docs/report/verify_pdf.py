"""Optional authoring check: repeat render, compare bytes and inspect PDF structure."""
import argparse
import hashlib
import json
import re
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
    assert 1 <= len(reader.pages) <= 6, "Exceeded six-page budget"
    full_text = "\n".join(page.extract_text() for page in reader.pages)
    assert "[Pending:" not in full_text, "Body contains unresolved pending markers"
    assert full_text.count("Pending items") == 1, "Expected one consolidated pending box"
    assert "Frozen A:" in reader.pages[0].extract_text(), "Summary missing from first page"
    assert "Dashboard results:" in full_text and "Selected flaw region" in full_text
    for page in reader.pages:
        assert abs(float(page.mediabox.width) - 595.2756) < 0.01
        assert abs(float(page.mediabox.height) - 841.8898) < 0.01
        assert "{{" not in page.extract_text(), "Unrendered placeholder"
    expected_author = re.search(r'^author: "([^"]+)"$',
        (folder / 'report.md').read_text(encoding='utf-8'), re.M).group(1)
    assert reader.metadata.author == expected_author, "PDF author differs from report source"
    assert expected_author in reader.pages[0].extract_text(), "Visible author missing"
    return {
        "pdf_sha256": hashes[0],
        "repeat_sha256": hashes[1],
        "pages": len(reader.pages),
        "page_format": "A4",
        "body_font_pt": 11,
        "author": reader.metadata.author,
        "checks": "repeat bytes; A4; at most six pages; page-one summary; screenshots; one pending box",
        "visual_check": "See last final-render inspection; structural checks alone do not establish layout quality",
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
