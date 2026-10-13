"""Package existing v1 analyses for playback; never invoke the scoring pipeline."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / 'deploy/hf-static'
SYNTHETIC = [('05a48433edcf','awkward_pause'), ('2600de8f5bf4','rushing'),
             ('23d47562f995','mumbling'), ('066587c8820e','monotone'),
             ('51927844bef7','dragging'), ('737270e3c6f8','too_quiet'),
             ('1d90395b3f99','missing_pause')]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def export() -> None:
    """Copy stored JSON bytes and write separate presentation metadata."""
    entries = []
    sources = {}
    def copy(source: str, kind: str) -> str:
        path = ROOT / source
        target = f'data/{kind}/{path.name}'
        dest = DEMO / 'public' / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        sources[target] = {'source':source, 'sha256':digest(path)}
        return target
    def entry(analysis_id: str, title: str, note: str, **extra: object) -> None:
        source = f'data/analyses/{analysis_id}.json'
        a = json.loads((ROOT/source).read_text())
        if a.get('schema') != 'analysis/v1':
            raise ValueError(f'Not a stored v1 analysis: {source}')
        rid = a['recording_id']
        ap = f'data/alignment/{rid}.json'
        alignment = json.loads((ROOT/ap).read_text())
        item = {'id':analysis_id, 'title':title, 'note':note,
                'analysis':copy(source,'analyses'), 'alignment':copy(ap,'alignment'),
                'audioSource':alignment['audio'], 'audio':f'audio/{rid}.mp3',
                'mode':a['mode'], 'flags':len(a['regions']), **extra}
        bid = a['reference'].get('baseline_recording_id')
        if bid:
            bp = f'data/alignment/{bid}.json'
            balign = json.loads((ROOT/bp).read_text())
            item.update(baselineAlignment=copy(bp,'alignment'), baselineAudioSource=balign['audio'],
                        baselineAudio=f'audio/{bid}.mp3')
        entries.append(item)
    human = json.loads((ROOT/'data/human/evaluation.json').read_text())
    for row in human['results']:
        if row['detector'] != 'v1':
            continue
        job = json.loads((ROOT/f"data/app/jobs/{row['job_id']}.json").read_text())
        a = job['analysis']; take = row['take_id']
        title = f"{'Gettysburg' if take.startswith('gettysburg') else 'Reagan Challenger'} {take.split('__')[-1]} · Mode {row['mode']}"
        note = 'Genuine recorder-confirmed take; frozen v1 results. Labels are not independent ratings.'
        if row['excluded_from_scoring']:
            note += ' Spontaneous take04: excluded from scored human A/B comparisons.'
        default = take=='gettysburg__user__take02' and row['mode']=='B'
        idx = next((i for i,v in enumerate(a['regions']) if v['type']=='awkward_pause' and abs(v['start']-29.9)<.001),0) if default else 0
        entry(a['analysis_id'], title, note, default=default, selectedRegion=idx, takeId=take)
    for aid,typ in SYNTHETIC:
        a = json.loads((ROOT/f'data/analyses/{aid}.json').read_text())
        rid = a['recording_id']; lp=f'data/labels/{rid}.json'
        gold=json.loads((ROOT/lp).read_text())['flaws']
        matches=[]
        for i,v in enumerate(a['regions']):
            for g in gold:
                overlap=max(0,min(v['end'],g['end'])-max(v['start'],g['start']))
                union=max(v['end'],g['end'])-min(v['start'],g['start'])
                if v['type']==g['type']==typ and union and overlap/union>=.3:
                    matches.append((i,overlap/union,g['severity']))
        if not matches:raise ValueError(f'Missing labelled hit: {aid}')
        label_path=copy(lp,'labels')
        severity=matches[0][2]
        entry(aid, f'Synthetic {typ.replace("_"," ")} · synthetic edit, severity {severity} · Mode A',
              f'Synthetic edit, severity {severity}. Selected illustration with a matching injected label (same type, IoU ≥ 0.3). All other stored flags remain visible; this selection is not a precision estimate.',
              selectedRegion=matches[0][0], hitIoU=matches[0][1], label=label_path,
              injectedType=typ, injectionSeverity=severity)
    entry('13ce79b4006a','Clean Reagan reader · Mode A',
          'Unedited public-domain source recording, with no stored flags. Institutional text has a single original reader; comparison to itself is not independent validation.')
    rights = DEMO/'public/licensing/licences.json'
    if rights.exists():
        shutil.copyfile(ROOT/'data/release/licences.json', rights)
        sources['licensing/licences.json'] = {'source':'data/release/licences.json','sha256':digest(rights)}
    (ROOT/'web/src/catalog.js').write_text('export default '+json.dumps(entries,ensure_ascii=False,indent=2)+';\n')
    human_gallery = {
        '8cbb735fbbb8': 'The “larger | sense” pause compared with take01.',
        '2f4bc4859707': 'The same delivery compared with expert readers.',
        '6ea97fd66515': 'Rehearsal differences compared with the earlier take.',
        '622b2cca881e': 'Speaker norms, with separate unscored heuristic tips.',
    }
    human_titles = {'8cbb735fbbb8':'Gettysburg take02','2f4bc4859707':'Gettysburg take02',
                    '6ea97fd66515':'Reagan take02','622b2cca881e':'Reagan take04'}
    gallery = []
    for aid in [*human_gallery, *(aid for aid,_ in SYNTHETIC)]:
        e=next(e for e in entries if e['id']==aid)
        description=human_gallery.get(aid) or f'synthetic edit, severity {e["injectionSeverity"]}; matching injected label (same type, IoU ≥0.3).'
        gallery.append({'id':aid,'title':human_titles.get(aid,e['title'].rsplit(' · Mode ',1)[0]),
                        'mode':e['mode'],'description':description,'flags':e['flags']})
    (ROOT/'web/src/gallery.ts').write_text('export default '+json.dumps(gallery,ensure_ascii=False,indent=2)+';\n')
    (DEMO/'SOURCE_MAP.js').write_text('export default '+json.dumps(sources,indent=2,sort_keys=True)+';\n')
    (DEMO/'MANIFEST.sha256').write_text(''.join(f"{v['sha256']}  {k}\n" for k,v in sorted(sources.items())))
    print(f'Packaged {len(entries)} views, {len(sources)} byte-identical stored JSON files')

if __name__ == '__main__':
    export()
