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
    args=parser.parse_args();logging.basicConfig(level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    run(args.root,args.base_url,args.fixture,args.dashboard_url)
