"""Add derived diagnostics to existing, preserved inference evidence (no rerun claim)."""
import json
from pathlib import Path
from speecheval.alignment_analysis import annotate_audit
from speecheval.evaluate import write_bakeoff_report
from speecheval.verify import _write_json
root=Path.cwd();path=root/'data/review/alignment_bakeoff.json';audit=json.loads(path.read_text())
audit['annotation_method']='Claude visual, not listened; human spot-check PENDING'
annotate_audit(root,audit)
_write_json(path,audit);write_bakeoff_report(root,audit)
