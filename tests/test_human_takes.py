"""Human workflow tests use temporary generated signals, never fake user data."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
import httpx


def test_no_recordings_is_pending_not_synthetic_human_results(tmp_path):
    from speecheval.human_takes import discover_takes
    assert discover_takes(tmp_path) == []


def test_real_inputs_require_consent_notes_and_as_spoken(tmp_path):
    from speecheval.human_takes import validate_human_inputs
    raw = tmp_path / 'data/human/raw'; raw.mkdir(parents=True)
    rid = 'gettysburg__user__take01'
    sf.write(raw / f'{rid}.wav', np.ones(1600) * .1, 16000)
    with pytest.raises(ValueError, match='CONSENT'): validate_human_inputs(tmp_path)
    (raw.parent / 'CONSENT.md').write_text('I agree to publication under CC BY 4.0.')
    with pytest.raises(ValueError, match='notes'): validate_human_inputs(tmp_path)
    (raw / 'notes.md').write_text('Notes, not machine-readable labels yet.')
    with pytest.raises(ValueError, match='JSON'): validate_human_inputs(tmp_path)
    (raw / 'notes.md').write_text('```json\n' + json.dumps({'takes': {rid: {'flaws': [], 'slips': 'none'}}}) + '\n```')
    with pytest.raises(ValueError, match='as-spoken'): validate_human_inputs(tmp_path)
    transcripts = raw.parent / 'transcripts'; transcripts.mkdir()
    (transcripts / f'{rid}.txt').write_text('Four score and seven years ago.')
    cases, notes = validate_human_inputs(tmp_path)
    assert cases[0]['take_id'] == rid and notes['takes'][rid]['flaws'] == []
    (raw / 'notes.md').write_text('```json\n' + json.dumps({'takes': {rid: {'flaws': [
        {'type': 'made_up', 'start': 0, 'end': .1}], 'slips': 'none'}}}) + '\n```')
    with pytest.raises(ValueError, match='flaw'): validate_human_inputs(tmp_path)


def test_number_expansion_retains_sentence_boundaries():
    from speecheval.human_takes import expanded_transcript
    assert expanded_transcript('# reviewed: supplied\n19 years ago. We saw 7 people.').strip() == 'nineteen years ago. We saw seven people.'


def test_format_normalisation_preserves_raw_and_checks_rate(tmp_path):
    from speecheval.human_takes import normalize_upload
    raw = tmp_path / 'input.wav'; output = tmp_path / 'normalized.wav'
    tone = .1 * np.sin(np.arange(16000) * 2 * np.pi * 220 / 16000)
    sf.write(raw, np.column_stack([tone, tone]), 16000, subtype='PCM_16')
    before = hashlib.sha256(raw.read_bytes()).hexdigest()
    qa = normalize_upload(raw, output)
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == before
    assert sf.info(output).samplerate == 44100 and sf.info(output).channels == 1
    assert qa['original_sample_rate'] == 16000 and qa['gain_normalization'] is False


def test_matching_is_one_to_one_and_pause_exception_is_separate():
    from speecheval.human_takes import compare_regions
    truth = [{'type': 'rushing', 'start': 1, 'end': 3}]
    predicted = [truth[0], truth[0], {'type': 'monotone', 'start': 1, 'end': 3}]
    result = compare_regions(predicted, truth)
    assert result['strict_iou'] == {'hits': 1, 'misses': 0, 'false_positives': 2}
    truth = [{'type': 'missing_pause', 'start': 1, 'end': 1.1}]
    predicted = [{'type': 'missing_pause', 'start': 1.2, 'end': 1.3}]
    result = compare_regions(predicted, truth)
    assert result['strict_iou']['hits'] == 0
    assert result['synthetic_policy']['hits'] == 1


def test_raw_note_times_shift_with_trim_and_sentence_notes_are_declared():
    from speecheval.human_takes import intended_regions
    alignment = {'duration_s': 5, 'sentences': [{'i': 0, 'start': .2, 'end': 3.5}]}
    regions, basis = intended_regions({'flaws': [{'type': 'rushing', 'start': 2, 'end': 4}]}, alignment, 1)
    assert regions == [{'type': 'rushing', 'start': 1, 'end': 3}]
    assert basis == ['raw-time note']
    regions, basis = intended_regions({'flaws': [{'type': 'monotone', 'sentence': 1}]}, alignment, 0)
    assert regions[0]['end'] == 3.5 and basis == ['intended sentence interval, not independent timed ground truth']
    with pytest.raises(ValueError): intended_regions({'flaws': [{'type': 'made_up', 'start': 1, 'end': 2}]}, alignment, 0)


def test_missing_take01_is_an_explicit_rehearsal_blocker():
    from speecheval.human_takes import missing_rehearsal_baselines
    cases = [{'text_id': 'gettysburg', 'take_number': 2, 'take_id': 'gettysburg__user__take02'}]
    assert 'take01' in missing_rehearsal_baselines(cases)[0]
    assert not missing_rehearsal_baselines(cases + [{'text_id': 'gettysburg', 'take_number': 1}])


def test_cached_upload_fetches_completed_job_not_just_post_summary(tmp_path):
    from speecheval.human_takes import submit
    audio=tmp_path/'fixture.wav';audio.write_bytes(b'test-only upload')
    seen=[]
    def endpoint(request):
        seen.append(request.method)
        if request.method=='POST':
            return httpx.Response(200,json={'analysis_id':'cached','status':'done'})
        return httpx.Response(200,json={'analysis_id':'cached','status':'done','analysis':{'recording_id':'fixture'}})
    with httpx.Client(base_url='http://test.invalid',transport=httpx.MockTransport(endpoint)) as client:
        job=submit(client,audio,'gettysburg','Supplied words.')
    assert job['analysis']['recording_id']=='fixture'
    assert seen==['POST','GET']


@pytest.mark.parametrize('notes', [[], {'takes': []}, {}])
def test_wrong_notes_shape_is_an_actionable_input_error(tmp_path, notes):
    from speecheval.human_takes import validate_human_inputs
    raw=tmp_path/'data/human/raw';raw.mkdir(parents=True)
    sf.write(raw/'gettysburg__user__take01.wav',np.ones(1600)*.1,16000)
    (raw.parent/'CONSENT.md').write_text('Test fixture consent, not genuine consent.')
    (raw/'notes.md').write_text('```json\n'+json.dumps(notes)+'\n```')
    with pytest.raises(ValueError, match='dictionary'):
        validate_human_inputs(tmp_path)


def test_dashboard_link_can_use_public_address_not_container_dns():
    from speecheval.human_takes import dashboard_link
    assert dashboard_link('http://web', 'abc', 'http://localhost:8080/') == 'http://localhost:8080/results/abc'
    assert dashboard_link('http://localhost:8080/', 'abc') == 'http://localhost:8080/results/abc'
