"""Step 6 shared sentence windows, both alignment adapters and output promotion."""
from __future__ import annotations
import csv
import json
import logging
import shutil
import time
from pathlib import Path
import yaml
from speecheval.align.base import Alignment, write_textgrid
from speecheval.align.mfa import check_custom_dictionary, ensure_adoption, run_mfa
from speecheval.align.whisperx_align import align_recording
from speecheval.transcripts import _body_text
from speecheval.verify import _hash_bytes, _refresh_output_windows, _write_json

LOGGER=logging.getLogger(__name__)


def promote_outputs(root: Path, primary: str, ids: list[str]) -> None:
    """Copy only selected recording artifacts; source provenance is not a recording."""
    for rid in ids:
        for suffix in ('.json','.TextGrid'):
            shutil.copyfile(root/'data/alignment'/primary/(rid+suffix),root/'data/alignment'/(rid+suffix))


def ensure_windows(root: Path, config: dict, rows: list[dict], force: bool) -> None:
    """Reuse frozen boundaries, rejecting stale provenance unless explicitly forced."""
    refresh={}
    for row in rows:
        rid=row['recording_id'];directory=root/config['paths']['alignment']
        path=directory/'windows'/f'{rid}.json'
        if force or not path.exists():
            refresh[rid]=True;continue
        saved=json.loads(path.read_text())
        expected={'transcript_sha256':_hash_bytes((root/config['paths']['transcripts_as_spoken']/f'{rid}.txt').read_bytes()),
                  'source_asr_sha256':_hash_bytes((directory/'asr'/f'{rid}.json').read_bytes()),
                  'cut_start_s':float(row['cut_start_s']),'cut_end_s':float(row['cut_end_s'])}
        # The committed v1 windows were generated with 0.3 s padding. New ones record it explicitly.
        stale=any(saved.get(key)!=value for key,value in expected.items())
        stale=stale or saved.get('sentence_window_padding_s',.3)!=config['alignment']['sentence_window_padding_s']
        if stale:raise ValueError(f'Stale frozen sentence windows: {rid}; refresh explicitly with --force')
    if refresh:_refresh_output_windows(root,config,{'transcripts':refresh})


def run_alignment(aligner: str = 'both', force: bool = False, promote: bool = False, dictionary_experiment: bool = False) -> None:
    """Produce validated JSON/TextGrid for all prepared recordings; no gold work."""
    root=Path.cwd();config=yaml.safe_load((root/'configs/default.yaml').read_text())
    check_custom_dictionary(root,config['alignment']['mfa'])
    if dictionary_experiment and promote:raise ValueError('An unapproved dictionary experiment cannot promote')
    if not dictionary_experiment:ensure_adoption(root,config['alignment']['mfa'])
    if promote:
        primary=config['alignment']['primary']
        if primary not in ('mfa','whisperx'):raise ValueError('Set alignment.primary after Step 7 bake-off before promotion')
        from speecheval.evaluate import load_recordings, validate_dataset
        ids=[r['recording_id'] for r in csv.DictReader((root/'data/manifest/recordings.csv').open())]
        validate_dataset(root,config,load_recordings(root,ids))
        promote_outputs(root,primary,ids)
        return
    if aligner not in ('both','mfa','whisperx'):raise ValueError('Aligner must be mfa, whisperx or both')
    rows=list(csv.DictReader((root/'data/manifest/recordings.csv').open()))
    ensure_windows(root,config,rows,force)
    recordings=[]
    for row in rows:
        rid=row['recording_id'];path=root/'data/transcripts/as_spoken'/f'{rid}.txt'
        uncertain_file=root/'data/transcripts/uncertain'/f'{rid}.json'
        uncertain=json.loads(uncertain_file.read_text()) if uncertain_file.exists() else {'uncertain_words':[]}
        if uncertain.get('transcript_sha256',_hash_bytes(path.read_bytes()))!=_hash_bytes(path.read_bytes()):
            raise ValueError(f'Stale uncertain word indices: {rid}')
        recordings.append({'recording_id':rid,'body':_body_text(path.read_text()),'duration_s':float(row['duration_s']),
            'windows':json.loads((root/'data/alignment/windows'/f'{rid}.json').read_text())['sentences'],
            'uncertain':uncertain['uncertain_words'],'transcript_sha256':_hash_bytes(path.read_bytes()),
            'audio_sha256':_hash_bytes((root/'data/audio/align16k'/f'{rid}.wav').read_bytes())})
    for name in (('mfa','whisperx') if aligner=='both' else (aligner,)):
        output=root/'data/alignment'/name;output.mkdir(parents=True,exist_ok=True)
        identities={r['recording_id']:_hash_bytes(json.dumps(r,sort_keys=True).encode()) for r in recordings}
        provenance=output/'provenance.json'
        inference_settings=config['alignment']['mfa'] if name=='mfa' else {'threads':1,'model':'WAV2VEC2_ASR_BASE_960H'}
        if not force and provenance.exists() and json.loads(provenance.read_text())['input_hashes']==identities and json.loads(provenance.read_text())['settings']==inference_settings:
            for recording in recordings:
                rid=recording['recording_id'];Alignment.model_validate(json.loads((output/f'{rid}.json').read_text()))
                if not (output/f'{rid}.TextGrid').exists():raise FileNotFoundError('TextGrid missing')
            LOGGER.info('Reusing %s alignments for all 30 recordings',name);continue
        began=time.monotonic()
        if name=='mfa':
            results=run_mfa(root,recordings,config['alignment']['mfa'])
        else:
            results={}
            for r in recordings:
                LOGGER.info('WhisperX forced alignment: %s',r['recording_id'])
                results[r['recording_id']]=align_recording(root,r['recording_id'],r['body'],r['windows'],r['duration_s'],r['uncertain'])
        for rid,payload in results.items():
            _write_json(output/f'{rid}.json',payload);write_textgrid(output/f'{rid}.TextGrid',payload)
        _write_json(provenance,{'aligner':name,'device':'cpu','recordings':len(results),'input_hashes':identities,
            'runtime_s':round(time.monotonic()-began,3),'settings':inference_settings})
        LOGGER.info('Completed %s: %d recordings',name,len(results))
