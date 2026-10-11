"""Local HTTP boundary for speech analysis; audio times are seconds."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
import time
import soundfile as sf
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
import yaml

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


def identifier(value: str) -> str:
    """Reject path-like identifiers before looking up project artifacts."""
    if not re.fullmatch(r'[a-zA-Z0-9_\-]{1,160}', value):
        raise HTTPException(400, 'Invalid identifier')
    return value


def contained(root: Path, relative: str) -> Path:
    """Resolve only files inside the project, including symlink targets."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(400, 'Audio path outside project')
    return path


def read_json(path: Path) -> dict:
    """Read an existing artifact or return an explicit HTTP 404."""
    if not path.is_file():
        raise HTTPException(404, 'Artifact not found')
    return json.loads(path.read_text())


def save_json(path: Path, value: dict) -> None:
    """Atomically persist queue transitions within the project."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


class JobRunner:
    """One worker, durable states and restart recovery; never parallel inference."""

    def __init__(self, root: Path):
        self.root = root
        self.folder = root / 'data/app/jobs'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='speech-analysis')
        for path in sorted(self.folder.glob('*.json')):
            job = read_json(path)
            if job['status'] in ('queued', 'running'):
                job['status'] = 'queued'; save_json(path, job)
                self.pool.submit(self.process, job)

    def submit(self, identity: dict, request: dict) -> dict:
        """Deduplicate a request by audio, transcript, mode, reference and producer identity."""
        aid = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
        path = self.folder / f'{aid}.json'
        with self.lock:
            if path.exists():
                return read_json(path)
            job = {'analysis_id': aid, 'status': 'queued', 'request': request, 'identity': identity,
                   'created_order': time.time_ns()}
            save_json(path, job)
            self.pool.submit(self.process, job)
        return job

    def process(self, job: dict) -> None:
        """Decode without normalization and call the same real pipeline as speecheval analyze."""
        path = self.folder / f"{job['analysis_id']}.json"
        try:
            job['status'] = 'running'; save_json(path, job)
            request = job['request']; source = contained(self.root, request['audio'])
            decoded = contained(self.root, request['decoded_audio'])
            # Exact existing corpus uploads can safely reuse their measured features.
            # A supplied transcript always requests new alignment instead.
            if not request['transcript']:
                for candidate in sorted((self.root / 'data/alignment').glob(f"{request['text_id']}__*.json")):
                    stored = contained(self.root, read_json(candidate)['audio'])
                    if stored.is_file() and hashlib.sha256(stored.read_bytes()).hexdigest() == job['identity']['audio_sha256']:
                        source = stored; break
                else:
                    source = decoded
            else:
                source = decoded
            transcript = None
            text = request['transcript']
            if not text and source == decoded:
                from speecheval.transcripts import _body_text
                text = _body_text((self.root / 'data/transcripts/canonical' / f"{request['text_id']}.txt").read_text())
            if text:
                transcript = self.root / 'data/app/uploads' / f"{job['analysis_id']}.txt"
                transcript.write_text(text + '\n')
            previous = None
            if request['previous_analysis_id']:
                old = read_json(self.folder / f"{request['previous_analysis_id']}.json")['analysis']
                previous = contained(self.root, read_json(self.root / 'data/alignment' / f"{old['recording_id']}.json")['audio'])
            from speecheval.pipeline import analyze
            result = analyze(source, request['text_id'], mode=request['mode'], transcript=transcript,
                             previous=previous, root=self.root)
            alignment = read_json(self.root / 'data/alignment' / f"{result['recording_id']}.json")
            unaligned = {w['word'] for w in alignment['warnings'] if w.get('type') == 'interpolated'}
            if len(unaligned) > .3 * len(alignment['words']):
                raise ValueError('Could not align: transcript does not match the audio (>30% interpolated words)')
            job.update(status='done', analysis=result)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception('Analysis job %s failed', job['analysis_id'])
            job.update(status='error', error=str(exc))
        save_json(path, job)


def create_app(root: Path | None = None) -> FastAPI:
    """Create the local API rooted in one WSL project checkout."""
    root = (root or Path.cwd()).resolve()
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.runner = JobRunner(root)
        yield
        app.state.runner.pool.shutdown(wait=True)

    app = FastAPI(title='Speech Eval', version='0.1.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173'],
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    @app.get('/api/health')
    def health() -> dict:
        commit = os.environ.get('SPEECHEVAL_GIT_COMMIT', '').strip() or None
        try:
            checkout = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                      capture_output=True, text=True)
            if checkout.returncode == 0:
                commit = checkout.stdout.strip() or commit
        except OSError:
            pass  # Git metadata/executable is optional in a built image.
        config = root / 'configs/detector.yaml'
        return {'version': '0.1.0', 'git_commit': commit,
                'detector_config_hash': hashlib.sha256(config.read_bytes()).hexdigest() if config.exists() else None,
                'reference_version': {p.stem: read_json(p).get('reference_version', read_json(p).get('version'))
                                      for p in (root / 'data/reference').glob('*.json') if '__excl-' not in p.stem or p.stem.endswith('__excl-none')}}

    @app.get('/api/texts')
    def texts() -> list[dict]:
        from speecheval.transcripts import _body_text
        baselines = yaml.safe_load((root / 'configs/baselines.yaml').read_text()) if (root / 'configs/baselines.yaml').exists() else {}
        return [{'text_id': p.stem, 'title': p.stem.replace('_', ' ').title(),
                 'category': 'poem' if p.stem == 'o_captain' else 'speech',
                 'canonical_transcript': _body_text(p.read_text()).strip(), 'baseline_recording_id': baselines.get(p.stem)}
                for p in sorted((root / 'data/transcripts/canonical').glob('*.txt'))]

    @app.get('/api/analyses/{analysis_id}')
    def analysis(analysis_id: str) -> dict:
        identifier(analysis_id)
        job = read_json(root / 'data/app/jobs' / f'{analysis_id}.json')
        # A response-only display layer also fixes cached jobs. Keep the stored
        # explanation/evidence (including extreme raw z) byte-unchanged.
        result = job.get('analysis')
        if job['status'] == 'done' and result and result.get('regions'):
            from speecheval.display import explanation
            alignment = read_json(root / 'data/alignment' / f"{identifier(result['recording_id'])}.json")
            words = [w['text'] for w in alignment['words']]
            for region in result['regions']:
                region['display_explanation'] = explanation(region, words, result['mode'])
        return {k: v for k, v in job.items() if k not in ('identity', 'request')}

    def completed(aid: str) -> dict:
        job = analysis(aid)
        if job['status'] != 'done':
            raise HTTPException(409, 'Analysis is not complete')
        return job['analysis']

    @app.get('/api/history')
    def history(text_id: str = '') -> list[dict]:
        if text_id: identifier(text_id)
        jobs = sorted([read_json(p) for p in (root / 'data/app/jobs').glob('*.json')],
                      key=lambda j: (j.get('created_order', 0), j['analysis_id']))
        return [{'analysis_id': j['analysis_id'], 'recording_id': j['analysis']['recording_id'],
                 'mode': j['analysis']['mode'], 'scores': j['analysis']['scores']}
                for j in jobs if j['status'] == 'done' and (not text_id or j['analysis']['text_id'] == text_id)]

    @app.get('/api/analyses/{aid}/tracks')
    def tracks(aid: str) -> dict:
        from speecheval.service_tracks import analysis_tracks
        return analysis_tracks(root, completed(aid))

    @app.get('/api/analyses/{aid}/baseline-segment')
    def baseline_segment(aid: str, word_start: int, word_end: int) -> dict:
        from speecheval.reference import map_words
        result = completed(aid)
        baseline = result['reference'].get('baseline_recording_id')
        if not baseline: raise HTTPException(404, 'No same-text baseline for this mode')
        a = read_json(root / 'data/alignment' / f"{result['recording_id']}.json")
        b = read_json(root / 'data/alignment' / f'{identifier(baseline)}.json')
        if not 0 <= word_start <= word_end < len(a['words']):
            raise HTTPException(400, 'Invalid word interval')
        mapping = map_words([w['norm'] for w in a['words']], [w['norm'] for w in b['words']])
        selected = mapping[word_start:word_end + 1]
        if any(i is None for i in selected) or selected != list(range(selected[0], selected[-1] + 1)):
            raise HTTPException(404, 'These words do not form a matching baseline segment')
        return {'recording_id': baseline, 'start': b['words'][selected[0]]['start'], 'end': b['words'][selected[-1]]['end']}

    @app.get('/api/audio/{recording_id}')
    def audio(recording_id: str) -> FileResponse:
        alignment = read_json(root / 'data/alignment' / f'{identifier(recording_id)}.json')
        path = contained(root, alignment['audio'])
        if not path.is_file():
            raise HTTPException(404, 'Audio not available on this server')
        return FileResponse(path)

    @app.post('/api/analyses')
    async def upload(audio: UploadFile = File(...), text_id: str = Form(''),
                     mode: str = Form('A'), transcript: str = Form(''),
                     previous_analysis_id: str = Form('')) -> dict:
        extension = Path(audio.filename or '').suffix.lower()
        if extension not in {'.wav', '.mp3', '.m4a', '.webm', '.ogg'}:
            raise HTTPException(400, 'Use wav, mp3, m4a, webm or ogg audio')
        payload = await audio.read(25 * 1024 * 1024 + 1)
        if len(payload) > 25 * 1024 * 1024:
            raise HTTPException(400, 'Audio exceeds 25 MB')
        folder = root / 'data/app/uploads'; folder.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(payload).hexdigest()
        path = folder / (digest + extension)
        if not path.exists():
            path.write_bytes(payload)
        decoded = path.with_suffix('.decoded.wav')
        try:
            # Browser WebM may not store a duration. Decode at most 601 seconds and
            # use the sample count, not advisory container metadata, for the limit.
            subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-protocol_whitelist','file,pipe',
                            '-i',str(path),'-t','601','-vn','-ac','1','-ar','44100','-c:a','pcm_s16le',str(decoded)],
                           capture_output=True,check=True,timeout=120)
            duration = sf.info(decoded).duration
            if duration <= 0: raise ValueError('Empty audio')
        except (subprocess.SubprocessError, sf.LibsndfileError, ValueError):
            raise HTTPException(400, 'Could not decode audio')
        if duration > 600:
            raise HTTPException(400, 'Audio longer than 10 minutes')
        if mode not in ('A', 'B', 'C'):
            raise HTTPException(400, 'Mode must be A, B or C')
        if mode == 'C':
            text_id = text_id or 'own_speech'
            if not transcript.strip() and not (root / 'data/transcripts/canonical' / f'{identifier(text_id)}.txt').exists():
                raise HTTPException(400, 'Paste a transcript for your own speech')
        elif not (root / 'data/transcripts/canonical' / f'{identifier(text_id)}.txt').is_file():
            raise HTTPException(400, 'Select an available reference text')
        identifier(text_id)
        if mode == 'B':
            if not previous_analysis_id:
                raise HTTPException(400, 'Mode B requires a previous completed analysis')
            old = completed(previous_analysis_id)
            if old['text_id'] != text_id:
                raise HTTPException(400, 'Previous take must use the same text')
        elif previous_analysis_id:
            raise HTTPException(400, 'Previous take is only supported in Mode B')
        if len(transcript) > 100_000:
            raise HTTPException(400, 'Transcript exceeds 100,000 characters')
        producer = Path(__file__).parent
        from speecheval.pipeline import participant_code_identity, participant_model_identity
        settings = yaml.safe_load((root / 'configs/default.yaml').read_text()) if (root / 'configs/default.yaml').exists() else {}
        identity = {'audio_sha256': digest, 'text_id': text_id, 'mode': mode,
                    'transcript': transcript.strip(), 'previous_analysis_id': previous_analysis_id,
                    'configs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / 'configs').glob('*.yaml')},
                    'reference_inputs': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for pattern in ('data/features/provenance.json', 'data/manifest/dataset_shards/*.json', 'data/reference/norms_v1.json',
                                        'data/transcripts/canonical/*.txt') for p in root.glob(pattern)},
                    'runtime': participant_code_identity(),
                    # API requests always have a supplied/canonical transcript, or
                    # reuse an exact measured recording. They never invoke ASR.
                    'models': participant_model_identity(root, settings, False) if 'alignment' in settings else {},
                    'code': {str(p.relative_to(producer)): hashlib.sha256(p.read_bytes()).hexdigest() for p in producer.rglob('*.py')}}
        # Bind actual reference measurements too: provenance may be stale or not
        # regenerated yet, which must not make a completed HTTP cache hit valid.
        if (root / 'configs/splits.yaml').exists():
            for rid in yaml.safe_load((root / 'configs/splits.yaml').read_text())['train']:
                for relative in (f'data/alignment/{rid}.json', f'data/features/words/{rid}.parquet', f'data/features/windows/{rid}.parquet'):
                    p = contained(root, relative)
                    identity['reference_inputs'][relative] = hashlib.sha256(p.read_bytes()).hexdigest()
        if previous_analysis_id:
            identity['previous_result'] = completed(previous_analysis_id)
        request = {'audio': str(path.relative_to(root)), 'decoded_audio': str(decoded.relative_to(root)), 'text_id': text_id, 'mode': mode,
                   'transcript': transcript.strip(), 'previous_analysis_id': previous_analysis_id}
        job = app.state.runner.submit(identity, request)
        return {'analysis_id': job['analysis_id'], 'status': job['status']}

    return app
