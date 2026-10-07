"""Quantized time maps need interval checks at insertion discontinuities."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('integrity_check',Path(__file__).parents[1]/'scripts/check_dataset.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_jump_quantization_is_reported_not_hidden_as_small_error():
    mapping=[[0.,0.],[1.,1.],[1.,3.],[2.,4.]]
    result=module.mapping_edge_check(1.,3.,mapping,'left')
    assert result['valid'] and result['ambiguous_step']
    assert result['point_error_s']==2.
    assert not module.mapping_edge_check(1.,3.1,mapping,'left')['valid']


def test_nonstep_errors_still_fail_outside_rounding_bound():
    mapping=[[0.,0.],[2.,2.]]
    assert module.mapping_edge_check(1.,1.001,mapping,'left')['valid']
    assert not module.mapping_edge_check(1.,1.01,mapping,'left')['valid']
