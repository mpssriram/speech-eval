"""The post-hoc path leaves v1 unchanged and floors only pause uncertainty."""
from copy import deepcopy
import json
import numpy as np
import pytest
from speecheval.detect import detect, z_table
from speecheval.reference import transform


def evidence():
    alignment={'duration_s':5.,'words':[{'i':i,'text':'word','sentence':0,'start':i+1.,'end':i+1.3} for i in range(4)]}
    values=[{'rate':np.log(3.),'pitchvar':np.log(1.25),'loud':-2.,'clarity':-10.,'pause':transform('pause',.5)} for _ in range(4)]
    reference={'features':{str(i):{f:{'mu':v,'sigma':.001,'n':5} for f,v in {'rate':np.log(2.),'pitchvar':np.log(2.25),'loud':0.,'clarity':-5.,'pause':transform('pause',.48)}.items()} for i in range(4)}}
    settings={'k':dict.fromkeys(('rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause'),3.5),
              'region_min_words':3,'region_max_gap_words':1,'awkward_pause_min_s':.45,
              'missing_pause_ref_min_s':.3,'missing_pause_max_frac':.4,'severity_z_bins':[2.,2.75,3.5,4.059,6591.]}
    return alignment,values,reference,settings


def test_off_is_byte_identical_to_v1():
    from speecheval.pause_floor import floor_z_table
    a,v,r,s=evidence(); mapping=list(range(4))
    original=z_table(a,v,r,mapping)
    for disabled in ({},{'pause_sigma_floor_s':None},{'pause_sigma_floor_s':0.0}):
        candidate=floor_z_table(a,v,r,mapping,disabled)
        assert json.dumps(candidate,sort_keys=True)==json.dumps(original,sort_keys=True)
        assert json.dumps(detect(candidate,5.,s),sort_keys=True)==json.dumps(detect(original,5.,s),sort_keys=True)


def test_on_uses_reference_boundary_floor_in_natural_log_units_only():
    from speecheval.pause_floor import floor_z_table
    a,v,r,s=evidence(); original=deepcopy(r)
    changed=floor_z_table(a,v,r,list(range(4)),{'pause_sigma_floor_s':.052})
    baseline=z_table(a,v,r,list(range(4)))
    expected=(np.log(.5+.05)-np.log(.48+.05))/(np.log(.48+.052+.05)-np.log(.48+.05))
    assert changed[1]['z']['pause']==float(f'{expected:.4g}')
    for old,new in zip(baseline,changed):
        assert {k:v for k,v in old['z'].items() if k!='pause'}=={k:v for k,v in new['z'].items() if k!='pause'}
        assert old['reference']==new['reference']
        assert json.dumps(old['values'],sort_keys=True)==json.dumps(new['values'],sort_keys=True)
    assert r==original


def test_larger_existing_sigma_and_missing_evidence_are_preserved():
    from speecheval.pause_floor import floor_z_table
    a,v,r,s=evidence();r['features']['1']['pause']['sigma']=2.;r['features']['2']['pause']=None
    v[3]['pause']=np.nan
    assert json.dumps(floor_z_table(a,v,r,[0,1,2,None],{'pause_sigma_floor_s':.052}),sort_keys=True)==json.dumps(z_table(a,v,r,[0,1,2,None]),sort_keys=True)


@pytest.mark.parametrize('bad',[-.052,float('inf'),float('nan'),True,'0.052'])
def test_invalid_floor_is_rejected(bad):
    from speecheval.pause_floor import floor_z_table
    a,v,r,s=evidence()
    with pytest.raises(ValueError):floor_z_table(a,v,r,list(range(4)),{'pause_sigma_floor_s':bad})
