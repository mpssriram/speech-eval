"""Seeded blind clip export from verified licensed release training audio."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import logging
from pathlib import Path
import random
import soundfile as sf
import yaml
from speecheval.ratings import FIELDS,clip_measurement

LOGGER=logging.getLogger(__name__)
SEED=20261010
SOURCES=('gettysburg__lv_fb','gettysburg__lv_dl','o_captain__lv_apc')
SPECS=(('rushing',1),('dragging',3),('monotone',5),('too_quiet',2),('mumbling',4),
       ('awkward_pause',3),('missing_pause',4),('rushing',5),('monotone',2))


def select_rows(rows: list[dict]) -> list[dict]:
    """Fixed convenience sample, training-only; never select based on system success."""
    indexed={row['recording_id']:row for row in rows}
    names=[source+'__orig' for source in SOURCES]
    names += [SOURCES[i%3]+f'__{kind}_s{n}_01' for i,(kind,n) in enumerate(SPECS)]
    if any(name not in indexed or indexed[name]['split']!='train' for name in names):
        raise ValueError('Rating source missing or not in training split')
    return [indexed[name] for name in names]


def crop_bounds(duration: float, flaws: list[dict]) -> tuple[float,float]:
    """Nominal 20-second clip, retaining the whole injected interval with 2 s context."""
    if duration<=0:raise ValueError('Empty source')
    if flaws:
        first=min(f['start'] for f in flaws);last=max(f['end'] for f in flaws)
        if not 0<=first<last<=duration:raise ValueError('Label outside source timeline')
        length=min(duration,max(20,last-first+4));centre=(first+last)/2
    else:length=min(duration,20);centre=duration/2
    start=max(0,min(centre-length/2,duration-length))
    return round(start,3),round(start+length,3)


def _digest(path: Path) -> str:
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def verify_source(root: Path, audio: Path, inventory: dict) -> str:
    """Fail closed unless audio bytes and provenance are members of the release."""
    relative=audio.resolve().relative_to((root/'data').resolve()).as_posix()
    if relative not in inventory['audio_sources'] or _digest(audio)!=inventory['files'][relative]['sha256']:
        raise ValueError('Source is not verified licensed release audio')
    return relative


def load_labels(root: Path, row: dict) -> list[dict]:
    """Original rows have no injection label; generated rows require explicit labels."""
    if not row['label_path']:
        if row['kind']=='source':return []
        raise ValueError('Synthetic row requires an injection label')
    return json.loads((root/row['label_path']).read_text())['flaws']


def export_clip(audio: Path, dest: Path, flaws: list[dict], alignment: dict, analysis: dict, rubric: dict) -> dict:
    """Lossless PCM16 FLAC crop, no gain edits; labels move to clip-relative seconds."""
    wave,sr=sf.read(audio);start,end=crop_bounds(len(wave)/sr,flaws)
    a,b=round(start*sr),min(len(wave),round(end*sr));start=a/sr;end=b/sr
    dest.parent.mkdir(parents=True,exist_ok=True);sf.write(dest,wave[a:b],sr,subtype='PCM_16')
    truth=[{'type':f['type'],'start':round(f['start']-start,3),'end':round(f['end']-start,3),'severity':f['severity']} for f in flaws]
    return {'duration_s':round((b-a)/sr,3),'sample_rate':sr,'sha256':_digest(dest),
            'source_start_s':round(start,3),'source_end_s':round(end,3),'truth':truth,
            'system':clip_measurement(analysis,alignment,start,end,rubric)}


def write_blank_form(path: Path, names: list[str]) -> None:
    """Idempotent blank template; never replace an edited/completed rater form."""
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator='\n')
    writer.writeheader();writer.writerows({'clip':name} for name in names)
    content=stream.getvalue().encode()
    if path.exists() and path.read_bytes().replace(b'\r\n',b'\n')!=content:raise ValueError('Refusing to overwrite edited rating form')
    path.write_bytes(content)


def build_pack(root: Path) -> dict:
    """Build exactly twelve blinded clips and an outside-folder answer key."""
    from speecheval.pipeline import analyze
    from speecheval.verify import _write_json
    inventory=json.loads((root/'data/release/inventory.json').read_text())
    with (root/'data/manifest/dataset_index.csv').open() as stream:rows=select_rows(list(csv.DictReader(stream)))
    # Check all selected bytes before analysis/export, including labels/alignment.
    for row in rows:
        verify_source(root,root/row['audio_path'],inventory)
        load_labels(root,row)
        for path in [p for p in (row['label_path'],f'data/alignment/{row["recording_id"]}.json') if p]:
            relative=Path(path).relative_to('data').as_posix()
            if relative not in inventory['files'] or _digest(root/path)!=inventory['files'][relative]['sha256']:
                raise ValueError('Selected label/alignment differs from licensed release')
    config_names=('default.yaml','detector.yaml','rubric.yaml','splits.yaml')
    before={name:_digest(root/'configs'/name) for name in config_names}
    rubric=yaml.safe_load((root/'configs/rubric.yaml').read_text())
    public=root/'data/rating_pack';public.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED);rng.shuffle(rows);clips={}
    names=[f'{rng.getrandbits(64):016x}.flac' for _ in rows]
    if any(p.name not in set(names)|{'README.md','rating_form.csv','checksums.json'} for p in public.iterdir()):
        raise ValueError('Unexpected files in blind folder; use a separate clean checkout')
    write_blank_form(public/'rating_form.csv',names)
    for row,name in zip(rows,names):
        rid=row['recording_id'];flaws=load_labels(root,row)
        alignment=json.loads((root/'data/alignment'/f'{rid}.json').read_text())
        result=analyze(root/row['audio_path'],row['text_id'],exclude_speaker=row['speaker_slug'],root=root)
        evidence=export_clip(root/row['audio_path'],public/name,flaws,alignment,result,rubric)
        clips[name]={**evidence,'recording_id':rid,'split':row['split'],
                     'source_sha256':_digest(root/row['audio_path']),
                     'licence_source':inventory['audio_sources'][Path(row['audio_path']).relative_to('data').as_posix()]}
        LOGGER.info('Exported blind clip %s',name)
    (public/'README.md').write_text('''# Blind delivery ratings

Listen to each clip in CSV order; you may replay. Work independently and do
not consult other raters, the source repository, system scores or answer key.
Fill your anonymous rater_id on every row and an overall delivery score:
1 very poor, 2 poor, 3 acceptable, 4 good, 5 excellent. Judge delivery, not content.

flaw_type: none, rushing, dragging, monotone, too_quiet, mumbling,
awkward_pause or missing_pause. Use semicolons for multiple types and give
one corresponding approximate time in seconds from clip start in flaw_time_s.
For none leave flaw_time_s empty. Overall is required even if unsure of a flaw.
Save a separate completed CSV using your anonymous ID. Do not overwrite another
rater's answers. Return that CSV only; audio remains unchanged.

These recordings are licensed public-domain source excerpts or edited derivatives
in the USA; verify local rights if redistributing elsewhere. Scores are research
annotations, not diagnoses. You can decline or leave a clip wholly blank.
''')
    manifest={name:{k:clip[k] for k in ('duration_s','sample_rate','sha256')} for name,clip in clips.items()}
    _write_json(public/'checksums.json',manifest)
    key={'schema':'blind-rating-pack/v1','seed':SEED,'clips':clips,'frozen_configuration_sha256':before,
         'selection':'fixed convenience sample from three training speakers; not selected by detection accuracy',
         'clean_definition':'no injected flaw, not a guarantee of ideal perceptual delivery',
         'system_context':'Full-source frozen Mode A detections with source speaker excluded, clipped and rescored on visible speech duration. No detector tuning.'}
    _write_json(root/'data/rating_pack_private/answer_key.json',key)
    if before!={name:_digest(root/'configs'/name) for name in config_names}:raise ValueError('Configuration changed during export')
    return key
