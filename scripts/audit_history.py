"""Read-only full reachable Git history audit; never prints candidate secret values."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
 'OpenAI-style key':rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}',
 'Hugging Face token':rb'\bhf_[A-Za-z0-9]{30,}',
 'GitHub token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})',
 'AWS access key':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'Google API key':rb'\bAIza[A-Za-z0-9_-]{35}',
 'Slack token':rb'\bxox[baprs]-[A-Za-z0-9-]{20,}',
 'Private key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'Non-placeholder credential literal':rb'(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key|client[_-]?secret|password)[\x22\x27]?\s*[:=]\s*[\x22\x27]([^\x22\x27\r\n]{16,})[\x22\x27]',
}
PATH_PATTERNS=[b'/home/'+b'sriram',b'C:\\Users\\'+b'msrir',b'C:/Users/'+b'msrir']
LEGACY=b'input_'+b'246ca9e90194'
AUDIO={'.wav','.mp3','.flac','.ogg','.m4a','.mp4','.webm'}

def git(*args: str) -> str:
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True)

def audit() -> dict:
    """Scan every reachable blob and historical filename without editing Git."""
    objects={}
    for line in git('rev-list','--objects','--all').splitlines():
        oid,_,path=line.partition(' ');objects[oid]=path
    batch=subprocess.run(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],
                         cwd=ROOT,input='\n'.join(objects)+'\n',text=True,capture_output=True,check=True)
    blobs=[]
    for line in batch.stdout.splitlines():
        oid,typ,size=line.split()
        if typ=='blob':blobs.append((oid,int(size),objects[oid]))
    names={line.strip('"') for line in git('log','--all','--format=','--name-only','--no-renames').splitlines() if line.strip()}
    evidence={'head':git('rev-parse','HEAD').strip(),'commits':len(git('rev-list','--all').splitlines()),
              'refs':git('for-each-ref','--format=%(refname)').splitlines(),'reachable_objects':len(objects),
              'unique_blobs':len(blobs),'blob_bytes':sum(size for _,size,_ in blobs),'historical_paths':len(names),
              'secret_candidates':[],'private_path_blobs':[],'legacy_blobs':[],'media_blobs':[],
              'oversized_blobs':[],'dotenv_paths':sorted(p for p in names if Path(p).name=='.env' or Path(p).name.startswith('.env.'))}
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,size,path in blobs:
        proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
        header=proc.stdout.readline().decode().strip().split()
        content=proc.stdout.read(int(header[2]));assert proc.stdout.read(1)==b'\n'
        for label,pattern in PATTERNS.items():
            for match in re.finditer(pattern,content):
                candidate=match.group(1) if label=='Non-placeholder credential literal' else match.group()
                if label=='Non-placeholder credential literal' and (b'example' in candidate.lower() or b'placeholder' in candidate.lower() or b'getenv' in candidate.lower() or b'${' in candidate or b'os.' in candidate):continue
                evidence['secret_candidates'].append({'kind':label,'blob':oid,'path':path,'line':content[:match.start()].count(b'\n')+1,'fingerprint':hashlib.sha256(candidate).hexdigest()[:12]})
        found=[i for i,p in enumerate(PATH_PATTERNS) if p.lower() in content.lower()]
        if found:evidence['private_path_blobs'].append({'blob':oid,'path':path,'patterns':found})
        if LEGACY in content or LEGACY.decode() in path:evidence['legacy_blobs'].append({'blob':oid,'path':path})
        if size>10*1024*1024:evidence['oversized_blobs'].append({'blob':oid,'path':path,'bytes':size})
        if Path(path).suffix.lower() in AUDIO:evidence['media_blobs'].append({'blob':oid,'path':path,'bytes':size,'authorised_demo':path.startswith('deploy/hf-static/public/audio/')})
    proc.stdin.close();assert proc.wait()==0
    evidence['largest_blobs']=[{'blob':oid,'path':path,'bytes':size} for oid,size,path in sorted(blobs,key=lambda x:-x[1])[:10]]
    return evidence

if __name__=='__main__':
    result=audit();out=ROOT/'reports/history_audit_evidence.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:len(result[k]) if isinstance(result[k],list) else result[k] for k in ['commits','unique_blobs','blob_bytes','historical_paths','secret_candidates','private_path_blobs','legacy_blobs','media_blobs','oversized_blobs','dotenv_paths']},indent=2))
