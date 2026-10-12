"""Add read-only genuine-take diagnostics without inference or label changes."""
import json
from pathlib import Path
from speecheval.human_demo_evidence import collect_evidence, breakdown_markdown
from speecheval.human_confirmed_workflow import verify_inputs
from speecheval.verify import _write_json

root = Path.cwd()
verify_inputs(root, json.loads((root/'data/human/review/confirmation.json').read_text()))
evidence = collect_evidence(root)
_write_json(root/'data/human/demo_evidence.json', evidence)
path = root/'reports/phase10_human_takes.md'
marker = '\n## False-alarm breakdown (primary IoU >=0.3)'
base = path.read_text().split(marker)[0].rstrip()
path.write_text(base+'\n\n'+breakdown_markdown(evidence))
print(json.dumps({'pooled_false_alarms':evidence['pooled_false_alarms'],
                  'reference_readers':evidence['reference_readers'],
                  'take_timings':evidence['take_timings']}, indent=2))
