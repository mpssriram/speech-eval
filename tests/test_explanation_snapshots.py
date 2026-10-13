import copy
import json
from pathlib import Path
import pytest
from speecheval.display import explanation
ROWS=json.loads((Path(__file__).parent/'fixtures/explanation_snapshots.json').read_text())
@pytest.mark.parametrize('row',ROWS,ids=[r['mode']+'-'+r['region']['type'] for r in ROWS])
def test_display_snapshot_and_evidence_identity(row):
    before=copy.deepcopy(row['region'])
    assert explanation(row['region'],['larger','sense'],row['mode'],threshold=row['threshold'])==row['expected']
    assert row['region']==before
