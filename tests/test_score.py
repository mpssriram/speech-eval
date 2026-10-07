"""Hand-derived rubric arithmetic, bounds and decimal half-up behavior."""
from pathlib import Path
import pytest
import yaml
from speecheval import score as s


def config():return yaml.safe_load((Path(__file__).parents[1]/'configs/rubric.yaml').read_text())


def test_worked_example_and_half_up_overall():
    result=s.rubric_scores([{'type':'rushing','start':0.,'end':10.,'severity':3}],100.,config())
    assert result['pace']==7. and result['overall']==9.3
    assert result['pitch']==10. and result['pauses']==10.


def test_pause_event_penalty_and_combined_example():
    result=s.rubric_scores([{'type':'rushing','start':0.,'end':10.,'severity':3},
                           {'type':'missing_pause','start':11.,'end':11.03,'severity':1}],100.,config())
    assert result['pauses']==9.6 and result['overall']==9.2


def test_empty_is_ten_clamping_and_invalid_duration():
    assert set(s.rubric_scores([],10.,config()).values())=={10.}
    result=s.rubric_scores([{'type':'monotone','start':0.,'end':10.,'severity':5}],10.,config())
    assert result['pitch']==0.
    with pytest.raises(ValueError):s.rubric_scores([],0.,config())


def test_negative_weights_cannot_produce_overall_above_ten():
    settings=config();settings['weights']={'pace':2.,'pitch':-1.}
    with pytest.raises(ValueError,match='weights'):
        s.rubric_scores([{'type':'monotone','start':0.,'end':10.,'severity':5}],10.,settings)
