"""Compute agreement only from explicitly supplied, completed rating CSVs."""
import argparse
import json
from pathlib import Path
from speecheval.ratings import read_ratings,agreement
from speecheval.verify import _write_json

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key',type=Path,default=Path('data/rating_pack_private/answer_key.json'))
    parser.add_argument('--ratings',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,default=Path('data/rating_pack_private/agreement.json'))
    args=parser.parse_args();key=json.loads(args.key.read_text());rows=[]
    for path in args.ratings:rows.extend(read_ratings(path,key))
    if not rows:parser.error('No completed ratings; real agreement remains pending')
    _write_json(args.output,agreement(key,rows))
