"""Encode playback-only MP3 copies; source PCM and all scientific outputs remain untouched."""
from __future__ import annotations
import array
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DEMO=ROOT/'deploy/hf-static'

def read_module(path: Path) -> object:
    return json.loads(path.read_text().removeprefix('export default ').rstrip().removesuffix(';'))

def export_audio() -> None:
    """Encode at 128 kbps without gain filters and make display-only waveform peaks."""
    catalog=ROOT/'web/src/catalog.js'
    entries=read_module(catalog)
    sources={}
    for e in entries:
        pairs=[(e['audioSource'],e['audio'])]
        if e.get('baselineAudio'):pairs.append((e['baselineAudioSource'],e['baselineAudio']))
        for source,target in pairs:
            dest=DEMO/'public'/target
            if target in sources:continue
            dest.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/source),'-map_metadata','-1',
                            '-codec:a','libmp3lame','-b:a','128k',str(dest)],check=True)
            sources[target]={'source':source,'source_sha256':hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),
                             'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,
                             'encoding':'libmp3lame 128 kbps, no gain/normalisation filters; playback only'}
        pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(ROOT/e['audioSource']),
                                    '-ar','8000','-ac','1','-f','s16le','-'])
        data=array.array('h',pcm);step=max(1,len(data)//500)
        peaks=[max(abs(x) for x in data[i:i+step])/32768 for i in range(0,len(data),step)]
        e['peaks']=[round(v,4) for v in peaks]
    catalog.write_text('export default '+json.dumps(entries,ensure_ascii=False,indent=2)+';\n')
    (DEMO/'AUDIO_SOURCES.js').write_text('export default '+json.dumps(sources,indent=2,sort_keys=True)+';\n')
    print(f'{len(sources)} MP3s, {sum(v["bytes"] for v in sources.values()):,} bytes; source audio unchanged')

if __name__=='__main__':export_audio()
