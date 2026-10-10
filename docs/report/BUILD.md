# Report authoring

The compact A4 PDF is generated from `report.md`, with natural pagination, an
11-point body and embedded DejaVu Sans. Tables use 9-point text. Unfilled fields
are consolidated in one final Pending items box. Existing result reports supply
the benchmark numbers; the illustrated real explanation links to its actual
analysis JSON and matching label, not a newly generated performance claim.

Optional authoring dependencies (not needed for Docker scientific reproduction):
ReportLab 4.4.9, Pillow 12.3.0 and pypdf 6.10.0, plus DejaVu Sans fonts.

```sh
python docs/report/verify_pdf.py --font-dir /usr/share/fonts/truetype/dejavu --save
```

This renders twice, requires identical bytes, checks at most six A4 pages, and records
the PDF hash in `verification.json`. Byte identity is demonstrated in the tested
authoring environment, not promised across dependency/font versions. After any
source change, render all pages with a PDF viewer or Poppler and inspect every
page for clipping, overlap and chart readability; the structural check cannot
replace that inspection. `verification.json` describes the last checked build.

The author and independent human evidence remain pending. See
`../TODO_PLACEHOLDERS.md` and `../../NEXT.md` before publication.
