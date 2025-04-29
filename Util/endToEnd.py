# To be evaluated with collation-ified results from Arafat's IR predictions
# See reconfigure_from_mmp.py to convert files before running this script,
# but the minimum requirements are:
#   * Objective column ('objective')
#   * Rank column (--rank-column: default 'predicted')
#   * Parameterization columns ('size' and a number of parameters in format r'p\d+')
#   * There is no need to filter/prune out other columns, they will not be referenced
#   * Every parameterization represented in --searches must have a matchable entry in rankcoll

import argparse
import pathlib
import re
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import tqdm

def build():
    prs = argparse.ArgumentParser("Evaluate effectiveness of a ranking "
            "collation (see reconfigure_from_mmp.py to prepare this file) "
            "when imposed on another search.")
    prs.add_argument("rankcoll", type=pathlib.Path,
            help="Ranking collation CSV that maps config to a predicted value")
    prs.add_argument("--rank-column", default="predicted",
            help="Column from [rankcoll] to use as prediction for sorting (default: %(default)s)")
    prs.add_argument("--searches", type=pathlib.Path, nargs="+", required=True,
            help="CSVs that define searches that exist within [rankcoll] to be re-ranked")
    prs.add_argument("--y", choices=['rank','objective'], default='objective',
            help="Y-axis value for charts (default: %(default)s)")
    prs.add_argument("--print-all", action='store_true',
            help="Print arrays for ordering (may lead to excessive text output, default: %(default)s)")
    prs.add_argument("--expect-partial", action='store_true',
            help="Expect for [rankcoll] to NOT identify every value in [searches] (default: %(default)s)")
    prs.add_argument("--invert-sort", action='store_true',
            help="If reranking-column should be MAXIMIZED, set this to true (default: %(default)s)")
    prs.add_argument("--export", default=None, type=pathlib.Path,
            help="Give a path to export plot image to (default: display interactively)")
    prs.add_argument("--format", default='png', choices=['png','pdf'],
            help="Specify format for export (default: %(default)s)")
    prs.add_argument("--title", default=None,
            help="Override default plot title")
    prs.add_argument("--reordered-export", default=None, type=pathlib.Path,
            help="Drop CSV with reordering at this filename")
    prs.add_argument("--no-plots", action="store_true",
            help="Skip plot outputs (default: %(default)s)")
    return prs

def parse(args=None, prs=None):
    if prs is None:
        prs = build()
    if args is None:
        args = prs.parse_args()
    # Check files
    if not args.rankcoll.exists() or not args.rankcoll.suffix == '.csv':
        raise ValueError(f"Rank collation '{args.rankcoll}' must be a valid CSV file")
    valid = []
    dropped = []
    for f in args.searches:
        if not f.exists() or not f.suffix == '.csv':
            dropped.append(f)
        else:
            valid.append(f)
    args.searches = valid
    if len(dropped) > 0:
        warnings.warn(f"Files not found or not CSVs are dropped from search: {dropped}", UserWarning)
    if args.export is not None:
        if args.export.suffix != f".{args.format}":
            args.export = args.export.with_suffix(f".{args.format}")

    return args

def get_csv_with_size(name):
    # Infer size when not present based on filename
    csv = pd.read_csv(name)
    if 'actually_measured' in csv.columns:
        csv = csv[csv['actually_measured']].reset_index(drop=True)
    if 'size' in csv.columns:
        return csv
    for size in ['SM','ML','XL','S','M','L']:
        if size in map(lambda x: x.upper(), name.stem.split('_')):
            csv.insert(len(csv.columns), 'size', [size] * len(csv))
            return csv
    raise ValueError(f"Did not find or infer a problem size for '{name}'")

def get_subset_index(searchname, search, lookup, args):
    # Get the index from lookup that matches entries in search
    index = np.zeros(len(search))
    match_cols = ['size']+[_ for _ in search.columns if re.match(r'p\d+', _) is not None]
    strsearch = search[match_cols].astype(str)
    strlookup = lookup[match_cols].astype(str)
    unmatched = []
    for (idx, row) in tqdm.tqdm(strsearch.iterrows(), total=len(strsearch)):
        rowlookup = tuple(row)
        match = np.where((strlookup == rowlookup).sum(axis=1) == len(match_cols))[0]
        if len(match) == 0:
            unmatched.append(idx)
            continue
        # Multi-matches should progressively use unique points
        # THIS MIGHT NOT BE SEMANTICALLY CORRECT
        matched = False
        for m in match:
            if m not in index[:idx]:
                index[idx] = m
                matched = True
                break
        if not matched:
            # When I combine searches, the same thing could show up more than once
            # Pick the least-used one
            use_count = [np.count_nonzero(index == m) for m in match]
            index[idx] = match[np.argmin(use_count)]
    if len(unmatched) > 0:
        #raise ValueError(f"Could not find {len(unmatched)} / {len(search)} searches {unmatched} from '{searchname}' in {args.rankcoll}")
        if not args.expect_partial:
            warnings.warn(f"Could not find {len(unmatched)} / {len(search)} searches {unmatched} from '{searchname}' in {args.rankcoll}", UserWarning)
        # Trim unallocated portion
        index = index[:-len(unmatched)]
    return index, unmatched

def rerank(searchname, search, reranker, args):
    # Rerank search using rank column from reranker
    subset_index, unmatched = get_subset_index(searchname, search, reranker, args)
    sort_by = reranker.loc[subset_index,args.rank_column]
    if args.invert_sort:
        sort_by *= -1
    rerank_sorter = np.argsort(sort_by).to_numpy()
    resorted = sort_by.index[rerank_sorter]
    if args.reordered_export is not None:
        old = None
        if args.reordered_export.suffix != ".csv":
            old = args.reordered_export
            args.reordered_export /= searchname.name
        args.reordered_export.parents[0].mkdir(exist_ok=True, parents=True)
        search.loc[rerank_sorter].to_csv(args.reordered_export,index=False)
        if old is not None:
            args.reordered_export = old
    # rerank sorter is for search.loc, resorted is for reranker.loc
    return rerank_sorter, resorted

def oracle(searchname, search, reranker, args):
    # Rerank search using objective column from reranker
    subset_index, unmatched = get_subset_index(searchname, search, reranker, args)
    sort_by = reranker.loc[subset_index,'objective']
    rerank_sorter = np.argsort(sort_by).to_numpy()
    resorted = sort_by.index[rerank_sorter]
    # rerank sorter is for search.loc, resorted is for reranker.loc
    return rerank_sorter, resorted

def main(args=None):
    args = parse(args)
    rcoll = pd.read_csv(args.rankcoll)
    for col in rcoll.columns:
        if col.startswith('p'):
            try:
                int(col[1:])
            except:
                continue
            if rcoll.dtypes[col] != object:
                rcoll[col] = rcoll[col].astype(int)
    if args.export is not None:
        iter_value = 0
        iterable_name = args.export.with_stem(f"{args.export.stem}_0")
    for search_name in args.searches:
        print(f"Evaluations for {search_name}")
        search = get_csv_with_size(search_name)

        # === SORTING ORDERS ===

        # Correct sequence of GC generations for best-to-worst results
        oracle_search, oracle_order = oracle(search_name, search, rcoll, args)
        if args.print_all:
            print(f"Oracle order: {oracle_order}")
        # Predicted sequence of GC generations for best-to-worst results
        rerank_search, reranked_order = rerank(search_name, search, rcoll, args)
        if args.print_all:
            print(f"Reranked order: {reranked_order}")
        # In the event some ranks get dropped, you have to make the initial order last
        # Based on rcoll order to guarantee matches in rcoll are consistent!
        initial_order = oracle_order[[oracle_search.tolist().index(_) for _ in range(len(oracle_search))]]
        #sorted(set(reranked_order).intersection(set(oracle_order)))

        # Rephrase above as 'which oracle value did you actually pull?'
        initial_as_oracle_order = list(map(lambda o: np.where(reranked_order == o)[0][0], initial_order))
        rerank_as_oracle_order = list(map(lambda o: np.where(reranked_order == o)[0][0], oracle_order))
        if args.print_all:
            print(f"Oracle values in initial order: {initial_as_oracle_order}")
            print(f"Oracle values in rerank order: {rerank_as_oracle_order}")


        # === METRICS ===

        # Minimum displacement: Lower is better
        # Gives a metric for how long until you find the minimum value
        mindis_initial = list(initial_order).index(oracle_order[0])
        mindis_reranked = list(reranked_order).index(oracle_order[0])
        print(f"Minimum evaluations to find optimum in search (initial->reranked): {mindis_initial} -> {mindis_reranked}")

        # Total displacement: Lower (negative) is better
        # Gives metric of sum evaluations improved (only half -- if you do the whole displacement it's always zero)
        # Maximum +/- score = (n(n+1))/2 where n=1/2 length, so normalize on that
        # To give preference to getting the best evaluations the MOST displaced, use some sort of logarithmic-ish weighting?
        initial_displacement = list(map(lambda x: list(initial_order).index(x), oracle_order))
        reranked_displacement = list(map(lambda x: list(reranked_order).index(x), oracle_order))
        total_displacement = (np.asarray(initial_displacement)-np.asarray(reranked_displacement))[:len(initial_order)//2]

        # Spearmanr +1 = perfect correl, 0 = no correl, -1 anticorrel
        # Gives a metric across the entire search
        initial_spearmanr = spearmanr(initial_order, oracle_order)
        reranked_spearmanr = spearmanr(reranked_order, oracle_order)
        print(f"Spearmanr vs Oracle (initial->reranked): {initial_spearmanr} -> {reranked_spearmanr}")


        # === PLOTS ===

        if args.no_plots:
            continue
        fig, ax = plt.subplots()
        #subset_idx, unmatched = get_subset_index(search_name, search, rcoll, args)
        if args.y == 'rank':
            y1 = initial_as_oracle_order
            y2 = rerank_as_oracle_order
            ylabel = 'Oracle goodness (lower is better)'
        else:
            y1 = search.loc[sorted(oracle_search),'objective']#rcoll.loc[initial_order,'objective']
            y2 = rcoll.loc[reranked_order,'objective']
            #subset = rcoll.loc[subset_idx, 'objective']
            #y1 = subset.to_numpy()[np.asarray(initial_order)-min(initial_order)]
            #y2 = subset.to_numpy()[np.asarray(reranked_order)-min(reranked_order)]
            # subset.to_numpy()[np.asarray(oracle_order)-min(oracle_order)]
            ax.scatter(range(len(initial_order)), rcoll.loc[oracle_order,'objective'], label='oracle')
            ylabel = 'Objective value (lower is better)'
        ax.scatter(range(len(initial_order)), y1,
                label='Initial order')
        ax.scatter(range(len(initial_order)), y2,
                label='Re-sorted order')
        ax.set_xlabel('Trial #')
        ax.set_ylabel(ylabel)
        if args.title is None:
            pass
            #ax.set_title(f"Reranking for Search {search_name.stem}")
        else:
            ax.set_title(args.title)
        ax.legend()

        if 'original' in rcoll.columns and 'predicted' in rcoll.columns:
            fig2, ax2 = plt.subplots()
            ax2.scatter(rcoll.loc[subset_idx, 'original'], rcoll.loc[subset_idx,'predicted'])
            ax2.set_xlabel('True performance bucket')
            ax2.set_ylabel('Predicted performance bucket')
            ax2.set_title(f'Bucket utilizations for Search {search_name.stem}')

        if args.export is None:
            plt.show()
            continue
        while iterable_name.exists():
            iter_value += 1
            iterable_name = args.export.with_stem(f"{args.export.stem}_{iter_value}")
        print(f"Export to {iterable_name}")
        fig.savefig(iterable_name, format=args.format, dpi=300)

if __name__ == "__main__":
    main()

