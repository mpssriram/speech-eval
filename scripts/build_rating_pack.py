"""Build a blinded licensed training-only rating pack; no ratings are generated."""
import argparse
import logging
from pathlib import Path
from speecheval.rating_pack import build_pack

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    args=parser.parse_args();logging.basicConfig(level=logging.INFO)
    build_pack(args.root)
