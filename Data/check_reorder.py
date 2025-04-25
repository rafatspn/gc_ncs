import pandas as pd
import pathlib
import subprocess

base_other = pathlib.Path('reordered_searches')
for rawdir in sorted(pathlib.Path('rawsearches').iterdir()):
    bench = rawdir.stem
    otherdir = base_other / bench
    missing = 0
    for expect_csv in sorted(rawdir.iterdir()):
        other_csv = otherdir / expect_csv.name
        expect = pd.read_csv(expect_csv)
        if 'actually_measured' in expect.columns:
            expect = expect[expect['actually_measured']]
        n_expect = len(expect)
        if not other_csv.exists():
            print(f"Did not find reordered search for '{other_csv}'")
            command = "python3 endToEnd.py "
                      "arafat_all_convert/{bench}/all_arafat_{bench}.csv "
                      "--rank-column score "
                      "--invert-sort "
                      "--searches {expect_csv} "
                      "--reordered-export {other_csv}"
            #subprocess.run(command.format(bench=bench,
            #                     expect_csv=str(expect_csv),
            #                     other_csv=str(other_csv),
            #                     ).split(' '))
            continue
        n_found = len(pd.read_csv(other_csv))
        missing_here = n_expect - n_found
        missing += missing_here
        if missing_here > 0:
            print(f"Found {n_found}/{n_expect} records in '{other_csv}' (missing {missing_here})")
        else:
            print(f"All records present for '{other_csv}'")
    if missing == 0:
        print(f"Benchmark {rawdir} is COMPLETE")
