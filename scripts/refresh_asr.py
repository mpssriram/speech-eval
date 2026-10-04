"""Regenerate full-source ASR for the explicitly repaired cuts; never alter cuts/raw."""
import csv
import json
import os
from pathlib import Path
import tempfile

import torch
import yaml

from speecheval.prepare import _decode_for_asr, _import_whisperx, _run_whisperx
from speecheval.verify import _hash_bytes, _write_json, _refresh_output_windows

root = Path.cwd()
config = yaml.safe_load((root / 'configs/default.yaml').read_text())
os.environ['HF_HOME'] = str(root / 'data/.cache/huggingface')
os.environ['TORCH_HOME'] = str(root / 'data/.cache/torch')
repairs = json.loads((root / 'data/review/audio_repairs.json').read_text())
raw = {r['recording_id']: r for r in csv.DictReader((root / 'data/manifest/raw_files.csv').open())}
rows = {r['recording_id']: r for r in csv.DictReader((root / 'data/manifest/recordings.csv').open())}
cuts = yaml.safe_load((root / 'data/manifest/excerpts.yaml').read_text())
for rid, row in rows.items():
    assert float(row['cut_start_s']) == cuts[rid]['cut_start_s']
    assert float(row['cut_end_s']) == cuts[rid]['cut_end_s']
torch.manual_seed(0)
torch.set_num_threads(1)
whisperx = _import_whisperx()
model = whisperx.load_model('large-v3', 'cuda', compute_type='float16', language='en',
    asr_options={'beam_size': 5, 'temperatures': [0.0]}, vad_method='silero',
    download_root=str(root / 'data/.cache/whisperx'))
align_model, metadata = whisperx.load_align_model(language_code='en', device='cuda', model_dir=str(root / 'data/.cache/torch'))
evidence = []
for repair in repairs:
    rid = repair['recording_id']
    path = root / 'data/alignment/asr' / f'{rid}.json'
    history = root / 'data/review/legacy_asr' / path.name
    if not history.exists():
        _write_json(history, json.loads(path.read_text()))
    marker = root / 'data/review/asr_refresh' / path.name
    if marker.exists():
        evidence.append(json.loads(marker.read_text()))
        continue
    print('Regenerating large-v3 ASR:', rid, flush=True)
    source = root / raw[rid]['raw_path']
    before = _hash_bytes(path.read_bytes())
    with tempfile.TemporaryDirectory(prefix='refresh-asr-', dir=root / 'data') as temp:
        wav = Path(temp) / 'source.wav'
        _decode_for_asr(source, wav)
        result = _run_whisperx(wav, model, align_model, metadata, 'cuda', 'en')
    _write_json(path, {'model': 'large-v3', 'language': 'en', 'device': 'cuda',
        'time_basis': 'full_source', 'raw_sha256': _hash_bytes(source.read_bytes()), **result})
    event = {**repair, 'old_asr_sha256': before, 'new_asr_sha256': _hash_bytes(path.read_bytes()),
        'raw_sha256': _hash_bytes(source.read_bytes()), 'regenerated': True, 'time_basis': 'full_source'}
    _write_json(marker, event)
    evidence.append(event)
_refresh_output_windows(root, config, {'transcripts': rows})
_write_json(root / 'data/review/asr_regeneration.json', {'recordings': evidence, 'all_30_cut_times_match': True,
    'windows_regenerated': sorted(rows), 'source_asr_regenerated': len(evidence)})
print('Refreshed 12 ASR caches and all 30 current windows; frozen cuts unchanged.', flush=True)
