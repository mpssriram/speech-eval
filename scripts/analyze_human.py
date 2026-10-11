"""Analyse consented raw takes, or explicitly smoke-test with licensed synthetic crops."""
import argparse
import logging
from pathlib import Path
from speecheval.human_takes import run

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--base-url',default='http://localhost:8080')
    parser.add_argument('--dashboard-url',help='Browser-visible address when API uses container DNS')
    parser.add_argument('--fixture',action='store_true',help='Synthetic workflow check, never user takes')
    parser.add_argument('--detector',choices=('v1','v2','both'),default='v1',help='Frozen v1 primary or post-hoc v2; both reports side by side')
    parser.add_argument('--v2-runtime',choices=('host','docker'),default='host',help='Use the same environment that produced the MFA features; never bypass provenance')
    args=parser.parse_args();logging.basicConfig(level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    if not args.fixture and (args.root/'data/human/review/confirmation.json').exists():
        from speecheval.human_confirmed_workflow import run_confirmed
        payload=run_confirmed(args.root,args.base_url,args.dashboard_url,args.detector,args.v2_runtime)
        if payload['blockers']:raise SystemExit('Human workflow has processing problems; see Phase10 and BLOCKERS')
    else:
        if args.detector!='v1':parser.error('v2 requires confirmed genuine inputs, not a fixture')
        run(args.root,args.base_url,args.fixture,args.dashboard_url)
