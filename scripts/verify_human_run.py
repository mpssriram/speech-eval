"""Verify genuine inference artifacts, repeat bytes and live dashboard endpoints."""
import argparse
import json
from pathlib import Path
import httpx
from speecheval.human_confirmed_workflow import verify_inputs,pooled
from speecheval.human_takes import digest
from speecheval.verify import _write_json


def artifact_hashes(root: Path, payload: dict) -> dict[str,str]:
    """Bind each real result, recording measurement and prepared audio, not synthetic substitutes."""
    paths={'data/human/evaluation.json','reports/phase10_human_takes.md'}
    for row in payload['results']:
        rid=row['recording_id'];job_path=f'data/app/jobs/{row["job_id"]}.json';paths.add(job_path)
        result=json.loads((root/job_path).read_text())['analysis']
        folder='analyses_v2' if row['detector']=='v2' else 'analyses'
        paths.add(f'data/{folder}/{result["analysis_id"]}.json')
        paths.update({f'data/alignment/{rid}.json',f'data/alignment/{rid}.TextGrid',
                      f'data/transcripts/as_spoken/{rid}.txt',f'data/human/prepared/{row["take_id"]}.flac'})
        alignment=json.loads((root/f'data/alignment/{rid}.json').read_text());paths.add(alignment['audio'])
        paths.update(f'data/features/{f}/{rid}.parquet' for f in ('frames','words','windows','sentences'))
        paths.add(f'data/features/speaker_stats/{rid}.json')
    return {p:digest(root/p) for p in sorted(paths)}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',action='store_true')
    parser.add_argument('--base-url',default='http://localhost:8080')
    args=parser.parse_args();root=Path.cwd()
    confirmation=json.loads((root/'data/human/review/confirmation.json').read_text())
    verify_inputs(root,confirmation)
    payload=json.loads((root/'data/human/evaluation.json').read_text())
    assert payload['status']=='complete' and not payload['blockers'] and len(payload['results'])==26
    assert payload['pooled']==pooled(payload['results'])
    assert {p['current_takes'] for p in payload['pooled'] if p['mode']=='A'}=={6}
    assert {p['current_takes'] for p in payload['pooled'] if p['mode']=='B'}=={4}
    assert all(p['labelled_flaws']==13 for p in payload['pooled'])
    assert all(r['comparison'] is None and r['labelled_flaws'] is None for r in payload['results'] if r['excluded_from_scoring'])
    current=artifact_hashes(root,payload);snapshot=root/'data/.cache/human-work/first_complete_hashes.json'
    if args.snapshot:
        _write_json(snapshot,current);print(json.dumps({'snapshot_outputs':len(current),'evaluation_sha256':current['data/human/evaluation.json']}));return
    previous=json.loads(snapshot.read_text())
    assert current==previous,'Genuine repeated artifacts differ'
    checks=[]
    with httpx.Client(base_url=args.base_url,timeout=120) as client:
        history={r['analysis_id'] for r in client.get('/api/history').json()}
        for row in payload['results']:
            aid=row['job_id'];response=client.get('/api/analyses/'+aid);response.raise_for_status();job=response.json()
            assert job['status']=='done' and job['analysis']['recording_id']==row['recording_id'] and aid in history
            assert job['analysis']['detector'].get('version')==('post-hoc-v2' if row['detector']=='v2' else None)
            tracks=client.get('/api/analyses/'+aid+'/tracks');tracks.raise_for_status()
            checks.append({'take_id':row['take_id'],'detector':row['detector'],'mode':row['mode'],
                           'job_id':aid,'completed_status':True,'history_present':True,'tracks_http_status':tracks.status_code})
        for rid in sorted({r['recording_id'] for r in payload['results']}):
            with client.stream('GET','/api/audio/'+rid) as response:
                response.raise_for_status()
                assert int(response.headers['content-length'])>0
    verify_inputs(root,confirmation)
    evidence={'schema':'human-run-verification/v1','repeat_outputs':len(current),'byte_identical':True,
        'sha256':current,'dashboard_checks':checks,'genuine_participant_audio_endpoints':8,
        'immutable_original_raw_hashes_verified':16,'frozen_code_config_and_marker_unchanged':True,
        'independent_listening':False,'rater_responses':0}
    _write_json(root/'data/human/verification.json',evidence)
    print(json.dumps({'repeat_outputs':len(current),'byte_identical':True,'dashboard_jobs':len(checks),
                      'evaluation_sha256':current['data/human/evaluation.json']},indent=2))


if __name__=='__main__':main()
