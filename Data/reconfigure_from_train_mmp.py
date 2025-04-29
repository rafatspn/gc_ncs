# When doing inverted training/testing, the renaming protocol is VERY different
import argparse
import pathlib
import warnings

import pandas as pd
import numpy as np
import tqdm

def build():
    prs = argparse.ArgumentParser("Convert a CSV's record of 'mmp_*'-like "
                                  "fields to instead refer to the "
                                  "configuration associated with that name in "
                                  "training data from YTOPT-BO")
    prs.add_argument("--train", type=pathlib.Path, nargs="+", required=True,
                     help="Training data files that have configurations")
    prs.add_argument("--from", dest='_from', type=pathlib.Path, nargs="+", required=True,
                     help="CSVs to convert")
    prs.add_argument("--to", type=pathlib.Path, nargs="*", default=None,
                     help="If supplied, save resulting CSVs to different name "
                          "(default: override file in-place with same name)")
    prs.add_argument("--rename-FROM-cols", nargs="*", default=None,
                     help="use 'FROM_COL:TO_COL' to rename a column in the "
                          "FROM CSV to a new name before processing")
    prs.add_argument("--mmp-column", default="filename",
                     help="Column that contains the MMP filename data in FROM "
                          "CSVs (default: %(default)s)")
    prs.add_argument("--no-column-collisions", action="store_true",
                     help="Raise error if updating the FROM CSV with all data "
                          "in the collation CSV would cause a column name "
                          "collision (default: %(default)s)")
    prs.add_argument("--skip-exceptions", action="store_true",
                     help="Process as much as possible even if exceptions occur")
    return prs

def parse(args=None, prs=None):
    if prs is None:
        prs = build()
    if args is None:
        args = prs.parse_args()
    # File existence checks
    for train in args.train:
        if not train.exists():
            raise ValueError(f'Indicated training file "{train}" does '
                             'not exist')
    if args.to is not None and len(args.to) != len(args._from):
        raise ValueError("When specifying outputs TO CSV, require one TO name "
                         f"per FROM name (given {len(args.to)} TO names and "
                         f"{len(args._from)} FROM names)")
    elif args.to is None:
        args.to = args._from
    exist_from, exist_to = list(), list()
    for f, t in zip(args._from, args.to):
        if f.exists():
            exist_from.append(f)
            exist_to.append(t)
        else:
            warnings.warn(UserWarning, f"FROM CSV '{f}' does not exist")
    if len(exist_from) == 0:
        raise ValueError('None of the supplied FROM CSVs exist')
    args._from = exist_from
    args.to = exist_to
    # Rename formatting check
    if args.rename_FROM_cols is None:
        args.rename_FROM_cols = list()
    for rename in args.rename_FROM_cols:
        if len(rename.split(':')) != 2:
            raise ValueError(f"Column rename '{rename}' does not match expected format (FROM_NAME:TO_NAME)")
    return args

def infer_size(path):
    segments = list(map(lambda x: x.upper(), path.stem.split('_')))
    for tl in ['XL','ML','SM']:
        if tl in segments:
            return tl
    for sl in ['L','M','S']:
        if sl in segments:
            return sl
    raise ValueError(f"Size not automatically determined for file '{path}'")

def rename_columns(name, csv, columns, args):
    rename_cols = dict()
    for rename in args.rename_FROM_cols:
        from_name, to_name = rename.split(':',1)
        rename_cols[from_name] = to_name
    csv = csv.rename(columns=rename_cols)
    collisions = columns.intersection(set(csv.columns))
    if args.no_column_collisions and len(collisions) > 0:
        raise ValueError(f"FROM CSV '{name}' would collide with collation CSV "
                         f"{args.collation} on columns: {sorted(collisions)}. "
                         "Consider renaming these columns via the "
                         "--rename-FROM-cols option")
    return csv

def convert(name, csv, trains, prior_id, args):
    new_frame = csv.copy()
    for col in trains.columns:
        new_frame[col] = ""
    for (idx, row) in tqdm.tqdm(new_frame.iterrows(), total=len(new_frame)):
        mmp = pathlib.Path(row[args.mmp_column])
        mmp_name = int(mmp.stem.rsplit('_',1)[1])
        mmp_size = mmp.stem.split('_',3)[2]
        try:
            train_lookup = trains[trains['size'] == mmp_size].iloc[mmp_name]
        except:
            raise ValueError(f"Failed to find record for '{mmp_size}:{mmp_name}' from "
                             f"'{name}' in training records provided by "
                             f"'{args.train}'")
        # If > 1, different searches included it and that's no big deal, just
        # take the first result
        new_frame.loc[idx,trains.columns] = train_lookup
        new_frame.loc[idx,'id'] = prior_id[idx]
    new_frame['id'] = new_frame['id'].astype(int)
    return new_frame

def main(args=None):
    args = parse(args)
    trains = []
    for train in args.train:
        size = infer_size(train)
        csv = pd.read_csv(train)
        csv.insert(len(csv.columns),'size',[size] * len(csv))
        trains.append(csv)
    trains = pd.concat(trains)
    trains.reset_index(drop=False, inplace=True)
    prior_id_value = trains['index']
    print(f"Loaded {len(trains)} records from training data in '{args.train}'")
    train_columns = set(trains.columns).difference({'index'})
    for csv_name, output in zip(args._from, args.to):
        csv = pd.read_csv(csv_name)
        print(f"Loaded FROM CSV '{csv_name}' with {len(csv)} records")
        try:
            csv = rename_columns(csv_name, csv, train_columns, args)
            adjusted = convert(csv_name, csv, trains, prior_id_value, args)
        except Exception as E:
            exceptclass = str(type(E))
            exceptclass = exceptclass[exceptclass.index("'")+1:exceptclass.rindex("'")]
            print(f"{exceptclass} exception in processing. No output written for "
                  f"designated target '{output}'")
            if args.skip_exceptions:
                print(E)
                continue
            raise E
        adjusted.to_csv(output, index=False)
        print(f"Saved TO CSV '{output}'")

if __name__ == '__main__':
    main()

