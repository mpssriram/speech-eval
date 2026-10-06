"""MFA corpus validation, supplementary pronunciations and fixed-job CPU alignment."""
from __future__ import annotations
import os
import hashlib
import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from praatio import textgrid
import yaml
from speecheval.align.base import make_alignment
from speecheval.transcripts import normalize_tokens
from speecheval.verify import _write_json


def canonical_dictionary(text: str, required: set[str]) -> str:
    """Canonical supplemental pronunciations, retaining every distinct phone variant."""
    entries={tuple(line.split()) for line in text.splitlines() if line.strip()}
    if any(len(e)<2 for e in entries):raise ValueError('Malformed pronunciation')
    missing=required-{e[0] for e in entries}
    if missing:raise ValueError(f'Dictionary missing words: {sorted(missing)}')
    return ''.join(e[0]+'\t'+' '.join(e[1:])+'\n' for e in sorted(entries))


def check_custom_dictionary(root: Path, settings: dict) -> Path | None:
    """Reject modified dictionary contents even on a cached alignment invocation."""
    if not settings.get('custom_dictionary'):return None
    path=(root/settings['custom_dictionary']).resolve()
    if not path.is_relative_to(root.resolve()):raise ValueError('Custom dictionary outside project')
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if sha!=settings.get('custom_dictionary_sha256'):raise ValueError('Stale custom dictionary SHA256')
    return path


def adoption_identity(root: Path, settings: dict) -> dict[str,str]:
    """Bind an adoption decision to dictionary, candidate, inputs and visual gold files."""
    dictionary=check_custom_dictionary(root,settings)
    paths=[dictionary,root/'data/alignment/mfa/provenance.json',root/'data/manifest/recordings.csv',
           root/'data/review/before_custom_dictionary/alignment_bakeoff.json',root/'data/gold/alignment/todo/selection.json',
           root/'data/review/number_expansion.json']
    paths.extend(root/'data/alignment/mfa'/f"{r['recording_id']}.json" for r in csv.DictReader((root/'data/manifest/recordings.csv').open()))
    paths.extend(sorted((root/'data/gold/alignment').glob('*.TextGrid')))
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p is not None}


def require_adoption(expected: dict, decision: dict) -> None:
    """Reject failed or stale pronunciation-experiment evidence before using a default."""
    if decision.get('accepted') is not True:raise ValueError('Custom dictionary rejected or not approved by comparison')
    if decision.get('artifact_hashes')!=expected:raise ValueError('Custom dictionary adoption evidence stale')


def ensure_adoption(root: Path, settings: dict) -> None:
    """Require matching accepted corpus/gold evidence for a configured custom default."""
    if not settings.get('custom_dictionary'):return
    decision=json.loads((root/'data/review/custom_dictionary_comparison.json').read_text())
    require_adoption(adoption_identity(root,settings),decision)


def link_audio(source: Path, target: Path) -> None:
    """Replace only an owned corpus link when the prepared file was replaced."""
    if target.exists() and not source.samefile(target):target.unlink()
    if not target.exists():os.link(source,target)


def run_mfa(root: Path, recordings: list[dict[str,Any]], settings: dict[str,Any], isolated: bool = False) -> dict[str,dict[str,Any]]:
    """Run installed MFA CPU with one fixed job; all temporary state remains in repo."""
    work=root/('data/.cache/mfa/bakeoff' if isolated else 'data/.cache/mfa')
    corpus=work/'corpus';corpus.mkdir(parents=True,exist_ok=True)
    home=Path('/home/sriram')
    pretrained=home/'Documents/MFA/pretrained_models'
    acoustic=pretrained/'acoustic'/f"{settings['acoustic_model']}.zip"
    dictionary=pretrained/'dictionary'/f"{settings['dictionary']}.dict"
    g2p=pretrained/'g2p'/f"{settings['g2p_model']}.zip"
    for path in (acoustic,dictionary,g2p):
        if not path.exists():raise FileNotFoundError(f'Installed MFA model missing: {path}')
    cfg=work/'align.yaml'
    cfg.write_text(yaml.safe_dump({'beam':settings['beam'],'retry_beam':settings['retry_beam'],'num_jobs':1,'use_mp':False}))
    vocab=set()
    for recording in recordings:
        rid=recording['recording_id'];duration=recording['duration_s']
        wav=corpus/f'{rid}.wav'
        link_audio(root/'data/audio/align16k'/f'{rid}.wav',wav)
        windows=recording['windows'];intervals=[]
        # A TextGrid tier cannot overlap. Resolve padded sentence overlaps at their midpoint.
        for unit in windows:
            if not unit['valid']:continue
            start,end=unit['start'],unit['end']
            label=' '.join(normalize_tokens(unit['text']));vocab.update(label.split())
            if intervals and intervals[-1][1]>start:
                previous=intervals[-1];midpoint=(previous[1]+start)/2
                intervals[-1]=(previous[0],midpoint,previous[2]);start=midpoint
            if end>start:intervals.append((start,end,label))
        tg=textgrid.Textgrid();tg.addTier(textgrid.IntervalTier(rid,intervals,0,duration))
        tg.save(str(corpus/f'{rid}.TextGrid'),format='long_textgrid',includeBlankSpaces=True)
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    env.update(MFA_ROOT_DIR=str(work/'root'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    command=[str(home/'miniforge3/bin/conda'),'run','--no-capture-output','-n','aligner','mfa']
    common=['-t',str(work/'temp'),'-j','1','--clean','--no_use_mp','--no_use_postgres']
    logs=root/'reports/mfa';logs.mkdir(parents=True,exist_ok=True)
    def call(name: str,args: list[str]) -> None:
        with (logs/f'{name}.log').open('w') as log:
            subprocess.run(command+args+common,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,cwd=root)
    validation=work/'validation';validation.mkdir(exist_ok=True)
    custom=check_custom_dictionary(root,settings)
    known={line.split()[0].lower() for line in dictionary.read_text().splitlines() if line.strip()}
    base_dictionary=dictionary
    if custom:
        known.update(line.split()[0].lower() for line in custom.read_text().splitlines() if line.strip())
        base_dictionary=work/'custom_combined.dict'
        base_dictionary.write_text(dictionary.read_text().rstrip()+'\n'+custom.read_text())
    call('validate',['validate',str(corpus),str(base_dictionary),'--ignore_acoustics','--output_directory',str(validation)])
    oov=sorted(vocab-known)
    final_dictionary=base_dictionary
    if oov:
        oov_path=work/'oovs.txt';oov_path.write_text('\n'.join(oov)+'\n')
        generated=work/'supplementary.dict'
        call('g2p',['g2p',str(oov_path),str(g2p),str(generated),'--sorted'])
        final_dictionary=work/'combined.dict'
        final_dictionary.write_text(base_dictionary.read_text().rstrip()+'\n'+generated.read_text())
        missing=set(oov)-{line.split()[0] for line in generated.read_text().splitlines() if line.strip()}
        if missing:raise ValueError(f'G2P did not generate pronunciations for {sorted(missing)}')
    _write_json(work/'oov_audit.json' if isolated else root/'data/alignment/mfa_oovs.json',{'oovs':oov,'num_jobs':1,'beam':settings['beam'],
        'retry_beam':settings['retry_beam'],'dictionary':settings['dictionary'],'g2p_model':settings['g2p_model']})
    output=work/'output'
    call('align',['align',str(corpus),str(final_dictionary),str(acoustic),str(output),'--config_path',str(cfg),'--overwrite'])
    results={}
    for recording in recordings:
        rid=recording['recording_id']
        files=list(output.rglob(f'{rid}.TextGrid'))
        if len(files)!=1:raise ValueError(f'MFA output missing/ambiguous: {rid}')
        tg=textgrid.openTextgrid(str(files[0]),includeEmptyIntervals=False)
        word_tiers=[name for name in tg.tierNames if name.endswith('words')]
        if not word_tiers:raise ValueError(f'MFA word tier missing: {rid}')
        words=[{'word':entry.label,'start':entry.start,'end':entry.end}
               for name in word_tiers for entry in tg.getTier(name).entries if entry.label]
        warnings=[{'type':'oov','text':word} for word in oov if word in normalize_tokens(recording['body'])]
        results[rid]=make_alignment(rid,recording['body'],recording['windows'],words,recording['duration_s'],
                                    'mfa',recording['uncertain'],warnings)
    return results
