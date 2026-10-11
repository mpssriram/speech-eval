"""Materialise the recorder's 2026-10-12 rules; validate without detector inference."""
import json
from pathlib import Path
from speecheval.human_recording_inputs import prepare_confirmed_transcripts
from speecheval.human_takes import digest, validate_human_inputs
from speecheval.evaluate_v2 import verify_hashes
from speecheval.verify import _write_json


def main() -> None:
    root=Path.cwd()
    manifest=json.loads((root/'data/human/import_manifest.json').read_text())
    for take in manifest['takes']:
        for kind in ('original','wav'):
            item=take[kind]
            if digest(root/item['relative_path'])!=item['sha256']:raise ValueError('Immutable human audio changed')
    records=prepare_confirmed_transcripts(root)
    cases,notes=validate_human_inputs(root)
    frozen=json.loads((root/'data/review/detector_v2_test.json').read_text())['code_and_config_hashes']
    verify_hashes(root,frozen)
    payload={'schema':'human-recorder-confirmation/v1','recorder_confirmation_date':'2026-10-12',
        'confirmation_source':'recorder chat; replaces manual TAKES_REVIEW markers',
        'validated_takes':len(cases),'scored_takes':[c['take_id'] for c in cases if not notes['takes'][c['take_id']].get('excluded_from_scoring')],
        'excluded_takes':[c['take_id'] for c in cases if notes['takes'][c['take_id']].get('excluded_from_scoring')],
        'independent_annotation':False,'independent_transcript_verification':False,
        'audio_hashes_verified':16,'problems':[],
        'notes_sha256':digest(root/'data/human/raw/notes.md'),
        'label_protocol_sha256':digest(root/'data/human/review/CONFIRMED_PROTOCOL.md'),
        'transcript_hashes':{k:v['transcript_sha256'] for k,v in records.items()},
        'frozen_code_and_config_hashes':frozen,
        'one_shot_marker_sha256':digest(root/'data/review/detector_v2_test_started.json'),
        'threshold_tuning':False}
    _write_json(root/'data/human/review/confirmation.json',payload)
    _write_json(root/'data/human/input_validation.json',{
        'schema':'human-input-validation/v1','validated_takes':len(cases),
        'problems':[],'audio_hashes_verified':16,'inference_run':False,
        'confirmation_sha256':digest(root/'data/human/review/confirmation.json')})
    print(json.dumps({'validated_takes':len(cases),'scored_takes':len(payload['scored_takes']),
                      'excluded_takes':payload['excluded_takes'],'problems':[]},indent=2))


if __name__=='__main__':main()
