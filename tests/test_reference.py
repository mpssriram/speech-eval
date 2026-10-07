"""Known-answer robust distributions and whole-word transcript mapping."""
import numpy as np
import pytest
from speecheval import reference as r


def test_robust_shrinkage_matches_locked_formula():
    result=r.summarize([1.,2.,3.,4.,5.],2.)
    assert result['mu']==3.
    assert result['s']==pytest.approx(1.4826)
    assert result['sigma']==pytest.approx(np.sqrt((5*1.4826**2+5*4)/10))
    assert r.summarize([3.],2.)['sigma']==pytest.approx(np.sqrt(5/6)*2)


def test_missing_values_do_not_become_reference_zeros():
    assert r.summarize([np.nan,np.inf],1.) is None
    assert r.summarize([3.,np.nan],0.)['sigma']>0


def test_word_mapping_skips_insertions_and_deletions_not_substitutions():
    assert r.map_words(['four','new','score','years'],['four','score','and','years'])==[0,None,1,3]
    assert r.map_words(['ten thousand','people'],['ten thousand','people'])==[0,1]
    assert r.map_words(['ten','people'],['ten thousand','people'])==[None,1]


def test_feature_transforms_and_inverse_units():
    assert r.transform('rate',2.)==pytest.approx(np.log(2))
    assert r.inverse('pitchvar',r.transform('pitchvar',0.))==pytest.approx(0.)
    assert np.isnan(r.transform('rate',0.))
    assert np.isnan(r.transform('pause',-1.))
    assert r.transform('loud',-4.)==-4.


def test_pause_values_mask_inserted_or_skipped_boundary_endpoints():
    values=[{'pause':1.,'loud':2.} for i in range(3)]
    result=r.mask_pause_evidence(values,[0,None,1])
    assert all(np.isnan(v['pause']) for v in result)
    result=r.mask_pause_evidence(values,[0,1,3])
    assert result[1]['pause']==1. and np.isnan(result[2]['pause'])
    assert values[0]['pause']==1. and result[0]['loud']==2.


def test_reference_identifiers_cannot_escape_output_directory(tmp_path):
    with pytest.raises(ValueError,match='identifier'):
        r.build_reference('gettysburg','x/../../../../outside',root=tmp_path)
