"""Temporal grouping, missing evidence barriers, duration guards and conflicts."""
from pathlib import Path
import yaml
from speecheval import detect as d


def config():return yaml.safe_load((Path(__file__).parents[1]/'configs/detector.yaml').read_text())


def table(n=24):
    return [{'i':i,'sentence':0,'start':i*.3,'end':i*.3+.2,'ref_i':i,
             'values':{'rate':0.,'pause':0.},'reference':{'rate':0.,'pause':0.},'z':{'rate':0.}} for i in range(n)]


def test_merged_gap_cannot_reverse_direction_of_region_evidence():
    import numpy as np
    rows=table(4)
    for row,z,value in zip(rows,[3.,-12.,3.,3.],[6.,.1,6.,6.]):
        row['z']['rate']=z;row['values']['rate']=np.log(value);row['reference']['rate']=np.log(3.)
    result=d.detect(rows,1.2,config())
    assert len(result)==1 and result[0]['type']=='rushing'
    assert result[0]['word_start']==0 and result[0]['word_end']==3
    assert result[0]['evidence']['z']==3.
    assert result[0]['evidence']['participant']>result[0]['evidence']['reference']


def test_pause_event_requires_matching_adjacent_reference_endpoints():
    import numpy as np
    rows=table(3);rows[1]['ref_i']=None;rows[2]['ref_i']=1
    rows[2]['z']['pause']=5.;rows[2]['values']['pause']=np.log(.7+.05);rows[2]['reference']['pause']=np.log(.1+.05)
    assert d.detect(rows,1.2,config())==[]


def test_runs_merge_one_word_gap_but_not_two_or_missing_evidence():
    rows=table()
    for i in [10,11,12,14,15,18,19,20]:rows[i]['z']['rate']=3.
    regions=d.detect(rows,7.2,config())
    assert [(r['type'],r['word_start'],r['word_end']) for r in regions]==[('rushing',10,15),('rushing',18,20)]
    rows[13]['ref_i']=None
    assert [(r['word_start'],r['word_end']) for r in d.detect(rows,7.2,config())]==[(10,12),(18,20)]


def test_boundaries_require_absolute_pause_conditions():
    import numpy as np
    rows=table(3)
    rows[1]['z']['pause']=4.
    rows[1]['values']['pause']=np.log(.5+.05)
    rows[1]['reference']['pause']=np.log(.1+.05)
    rows[1]['start']=.7
    rows[2]['z']['pause']=-4.
    rows[2]['values']['pause']=np.log(.02+.05)
    rows[2]['reference']['pause']=np.log(.4+.05)
    rows[2]['start']=.92;rows[2]['end']=1.1;rows[1]['end']=.9
    result=d.detect(rows,1.2,config())
    assert [r['type'] for r in result]==['awkward_pause','missing_pause']
    assert result[1]['end']-result[1]['start']>=.03-1e-9
    rows[1]['values']['pause']=np.log(.2+.05)
    rows[2]['reference']['pause']=np.log(.1+.05)
    assert d.detect(rows,1.2,config())==[]


def test_conflicts_apply_strict_containment_and_strength():
    def region(kind,a,b,z):return {'type':kind,'start':a,'end':b,'mean_abs_z':z}
    rows=[region('rushing',0,5,3),region('missing_pause',1,2,4),region('missing_pause',0,1,4),
          region('dragging',6,10,3),region('awkward_pause',7,8,4),
          region('mumbling',11,20,4),region('too_quiet',12,18,3),region('too_quiet',12,18,5)]
    result=d.resolve_conflicts(rows)
    assert len(result)==5
    assert region('missing_pause',0,1,4) in result
    assert region('too_quiet',12,18,5) in result
