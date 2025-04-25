# Convert a CSV's record of 'mmp_*'-like fields to instead refer to the configuration associated with that name in a collation CSV
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
                                  "a collation CSV")
    prs.add_argument("collation", type=pathlib.Path,
                     help="Collation CSV to handle remapping")
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
    if not args.collation.exists():
        raise ValueError(f'Indicated collation file "{args.collation}" does '
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
            warnings.warn(f"FROM CSV '{f}' does not exist", UserWarning)
        t.parents[0].mkdir(exist_ok=True,parents=True)
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

def convert(name, csv, collation, prior_id, args):
    new_frame = csv.copy()
    for col in collation.columns:
        new_frame[col] = ""
    drop = []
    for (idx, row) in tqdm.tqdm(new_frame.iterrows(), total=len(new_frame)):
        mmp_name = int(pathlib.Path(row[args.mmp_column]).stem.rsplit('_',1)[1])
        mmp_size = "SM" if "SM" in row[args.mmp_column] else "XL"
        search = np.where(np.logical_and(collation['size'] == mmp_size,
                                         collation['id'] == mmp_name))[0]
        if len(search) == 0:
            drop.append(idx)
            continue
        # If > 1, different searches included it and that's no big deal, just
        # take the first result
        new_frame.loc[idx,collation.columns] = collation.loc[search[0]]
        new_frame.loc[idx,'id'] = prior_id[search[0]]
    if len(drop) > 0:
        print(f"Dropping {len(drop)} results that couldn't be found")
        new_frame = new_frame.drop(index=drop).reset_index(drop=True)
        """
        # +2 on line for 1-based indexing and CSV header
        raise ValueError(f"Failed to find record for '{mmp_name}' from "
                         f"'{name}:{idx+2}' in collation records provided by "
                         f"'{args.collation}'")
        """
    return new_frame

def main(args=None):
    args = parse(args)
    collation = pd.read_csv(args.collation)
    # RSBench had some unlabeled data
    collation = collation[collation['id'] != '-1'].reset_index(drop=True)
    prior_id_value = collation['id']
    collation['id'] = collation['id'].apply(lambda x: int(pathlib.Path(x).stem.rsplit('_',1)[1]))
    print(f"Loaded collation '{args.collation}' with {len(collation)} records")
    collation_columns = set(collation.columns)
    for csv_name, output in zip(args._from, args.to):
        csv = pd.read_csv(csv_name)
        print(f"Loaded FROM CSV '{csv_name}' with {len(csv)} records")
        try:
            csv = rename_columns(csv_name, csv, collation_columns, args)
            adjusted = convert(csv_name, csv, collation, prior_id_value, args)
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

