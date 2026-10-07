"""Verify complete feature bundles and cached replay without narrative reports."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from speecheval.features import features_all, features_qa


def main():
    root=Path.cwd();base=root/'data/features'
    manifest=json.loads((base/'provenance.json').read_text())
    assert len(manifest['inputs']['recordings'])==30
    assert len(manifest['artifacts'])==150
    for rid in manifest['inputs']['recordings']:
        alignment=json.loads((root/'data/alignment'/f'{rid}.json').read_text())
        frames=pd.read_parquet(base/'frames'/f'{rid}.parquet')
        words=pd.read_parquet(base/'words'/f'{rid}.parquet')
        windows=pd.read_parquet(base/'windows'/f'{rid}.parquet')
        sentences=pd.read_parquet(base/'sentences'/f'{rid}.parquet')
        assert np.allclose(np.diff(frames.t),.01)
        assert len(words)==len(windows)==len(alignment['words'])
        assert words.i.tolist()==list(range(len(words)))
        assert len(sentences)==len(alignment['sentences'])
        assert words.loc[words.uncertain,'f0_st_median'].isna().all()
        for i in alignment.get('uncertain_words',[]):
            assert pd.isna(words.loc[i,'pause_before_s']) and pd.isna(words.loc[i,'pause_after_s'])
            if i:assert pd.isna(words.loc[i-1,'pause_after_s'])
            if i+1<len(words):assert pd.isna(words.loc[i+1,'pause_before_s'])
        assert windows.loc[windows.uncertain,'rate_syl_s'].isna().all()
        assert sentences.loc[sentences.uncertain,'speech_rate_syl_s'].isna().all()
    before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in manifest['artifacts']}
    features_all()
    assert before=={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in before}
    features_qa()
    print('PASS: 30 recordings, 150 outputs, shared grids, uncertainty masks, identical cached replay')


if __name__=='__main__':main()
