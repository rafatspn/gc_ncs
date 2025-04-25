"""
    Load a bunch of CSVs and "staple" them together
"""
import pandas as pd

import argparse
import pathlib

def build():
    prs = argparse.ArgumentParser()
    prs.add_argument("--from", dest='_from', nargs="+", default=None, required=True, type=pathlib.Path,
                     help="Files to combine together")
    prs.add_argument("--to", dest='_to', type=pathlib.Path, required=True,
                     help="Destination file")
    prs.add_argument("--overwrite", action='store_true',
                     help="Give permission to overwrite existing destination file")
    return prs

def parse(args=None, prs=None):
    if prs is None:
        prs = build()
    if args is None:
        args = prs.parse_args()
    if args._to.exists() and not args.overwrite:
        raise ValueError(f"Destination file '{args._to}' exists! Give --overwrite to permit overwrite or rename destination")
    approved = []
    not_found = []
    for name in args._from:
        if name.exists():
            approved.append(name)
        else:
            not_found.append(name)
    args._from = approved
    if len(not_found) > 0:
        raise ValueError(f"Did not locate input files '{not_found}'")
    return args

def main():
    args = parse()
    csvs = []
    for _ in args._from:
        csvs.append(pd.read_csv(_))
    merge = pd.concat(csvs)
    if len(set(csvs[0].columns).difference(set(merge.columns))) > 0:
        raise ValueError("New columns introduced in merge")
    merge.to_csv(args._to,index=False)

if __name__ == '__main__':
    main()

