import math

import pytest
import torch

from speecheval import verify


def test_total_ctc_not_frame_average():
    assert hasattr(verify, 'ctc_total')
    probs = torch.log(torch.tensor([[.5, .5], [.5, .5]], dtype=torch.float64))
    assert verify.ctc_total(probs, [1]) == pytest.approx(math.log(.75))


def test_margin_uses_inclusive_false_acceptance_and_ties():
    from speecheval import calibrated
    margin, rate = calibrated.choose_margin([-4., -4., -2., 1., 2.], .2)
    assert margin > 4 and margin <= 4.000001
    assert rate == 0.  # Both tied 4-nat fakes must be excluded to allow at most one.


def test_local_window_keeps_one_neighbor_each_side_and_padding():
    from speecheval import calibrated
    body = 'one two three four five'
    words = [{'start': i, 'end': i+.5} for i in range(5)]
    result = calibrated.local_window(body, 8, 13, 'six', words, 5., .2)
    assert result['candidate_a'] == 'two three four'
    assert result['candidate_b'] == 'two six four'
    assert result['start_s'] == .8
    assert result['end_s'] == 3.7


def test_uncertain_indices_shift_after_applied_edit():
    from speecheval import calibrated
    body, indices = calibrated.apply_and_uncertain('one two three four', [
        {'transcript_start': 4, 'transcript_end': 7, 'asr': 'new second', 'decision': 'APPLY_B'},
        {'transcript_start': 8, 'transcript_end': 13, 'asr': 'six', 'decision': 'UNSURE'},
    ])
    assert body == 'one new second three four'
    assert indices == [3]


def test_edge_insertion_keeps_clip_edge_without_missing_neighbor():
    from speecheval import calibrated
    words=[{'start':.5,'end':1.},{'start':1.5,'end':2.}]
    result=calibrated.local_window('one two',7,7,'three',words,3.,.2)
    assert result['candidate_a']=='two'
    assert result['candidate_b']=='two three'
    assert result['end_s']==3.
    first=calibrated.local_window('one two',0,0,'three',words,3.,.2)
    assert first['start_s']==0.


def test_unlisted_transcript_edits_are_not_overwritten():
    from speecheval import calibrated
    assert hasattr(calibrated,'check_baseline')
    with pytest.raises(ValueError,match='modified'):
        calibrated.check_baseline('user edit','original',None)
    calibrated.check_baseline('original','original',None)


def test_cpu_backend_settings_are_pinned(tmp_path):
    from speecheval.calibrated import LocalScorer
    checkpoint=tmp_path/'data/.cache/torch/wav2vec2_fairseq_base_ls960_asr_ls960.pth'
    checkpoint.parent.mkdir(parents=True);checkpoint.write_bytes(b'identity-only-test')
    torch.backends.mkldnn.enabled=True
    torch.backends.mha.set_fastpath_enabled(True)
    LocalScorer(tmp_path,{'device':'cpu','threads':1,'model':'WAV2VEC2_ASR_BASE_960H'})
    assert not torch.backends.mkldnn.enabled
    assert not torch.backends.mha.get_fastpath_enabled()
