"""Generate the supplemental English MFA dictionary twice using installed CPU G2P."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from speecheval.align.mfa import canonical_dictionary
from speecheval.verify import _write_json

root=Path.cwd();work=root/'data/.cache/mfa/custom_generation';work.mkdir(parents=True,exist_ok=True)
oovs=json.loads((root/'data/review/before_custom_dictionary/mfa_oovs.json').read_text())['oovs']
words=work/'words.txt';words.write_text('\n'.join(sorted(oovs))+'\n')
env=os.environ.copy();env.pop('PYTHONPATH',None)
env.update(MFA_ROOT_DIR=str(work/'root'),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONHASHSEED='0')
raw_hashes=[];canonical=[]
for repeat in (1,2):
    output=work/f'pronunciations{repeat}.dict'
    command=['/home/sriram/miniforge3/bin/conda','run','--no-capture-output','-n','aligner','mfa','g2p',str(words),
             '/home/sriram/Documents/MFA/pretrained_models/g2p/english_us_mfa.zip',str(output),
             '--sorted','--clean','-j','1','--no_use_mp','--no_use_postgres','-t',str(work/'temp')]
    with (work/f'run{repeat}.log').open('w') as log:subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    raw_hashes.append(hashlib.sha256(output.read_bytes()).hexdigest())
    canonical.append(canonical_dictionary(output.read_text(),set(oovs)))
assert canonical[0]==canonical[1], 'Non-deterministic G2P output'
target=root/'data/dictionaries/custom_english_us_mfa.dict';target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(canonical[0])
sha=hashlib.sha256(target.read_bytes()).hexdigest()
_write_json(root/'data/dictionaries/custom_english_us_mfa.json',{'schema':'custom_dictionary/v1','words':oovs,
    'pronunciations':len(canonical[0].splitlines()),'sha256':sha,'raw_run_sha256':raw_hashes,
    'canonical_run_sha256':[sha,sha],'model':'english_us_mfa','model_sha256':hashlib.sha256(Path(command[8]).read_bytes()).hexdigest()})
print('Generated:',target.relative_to(root),'sha256:',sha,'unique words:',len(oovs))
