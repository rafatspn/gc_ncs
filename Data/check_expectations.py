"""
    Verify that arafat_all_convert records have all of the records EXPECTED to
    exist there based on collation data. Always check locally to verify things
    are actually missing first :)
"""
import pandas as pd
import numpy as np
import pathlib

collations = {
        # Polybench/C
        'syr2k': pd.read_csv('../Extract_A1_Here/syr2k_collated.csv'),
        '_3mm': pd.read_csv('../Extract_A1_Here/_3mm_collated.csv'),
        'heat3d': pd.read_csv('../Extract_A1_Here/heat3d_collated.csv'),
        # ECP
        'amg': pd.read_csv('../Extract_A1_Here/amg_collated.csv'),
        'rsbench': pd.read_csv('../Extract_A1_Here/rsbench_collated.csv'),
        'sw4lite': pd.read_csv('../Extract_A1_Here/sw4lite_collated.csv'),
        }

expected_searches = ['GaussianCopula','bliss','opentuner','GPTune']

check_dir = pathlib.Path('A2_Results_convert')

for bench, csv in collations.items():
    names = sorted(set(csv['source']))
    expectation = dict()
    missing_mmp = []
    for expect in expected_searches:
        specific_names = [_ for _ in names if expect.lower() in _.lower()]
        n_results = sum([len(csv[(csv['source'] == name) & ((csv['size'] == 'SM') | (csv['size'] == 'XL'))]) for name in specific_names])
        print(f"Expect: {bench} - {expect} has {n_results} records")
        expectation[expect] = n_results
    if bench == '_3mm':
        bench = '3mm'
    check_path = check_dir / bench
    if not check_path.exists():
        print(f"No records for {bench}!")
        continue
    any_found = False
    for name in check_path.iterdir():
        if name.suffix != '.csv':
            continue
        # Stapled files only
        if "A3_T1_" not in name.name:
            continue
        any_found = True
        load = pd.read_csv(name)
        print(f"Processing {name}...")
        missed_names = set()
        for expect in expected_searches:
            specific_names = [_ for _ in names if expect.lower() in _.lower()]
            n_results = 0
            for name in specific_names:
                # Previously we summed len(subload), but that might not be accurate
                subload = load #load[load['source'] == name]
                subcsv = csv[(csv['source'] == name) & ((csv['size'] == 'SM') | (csv['size'] == 'XL'))]
                match_on = csv.columns.tolist()
                match_on = match_on[:match_on.index('size')+1]
                matched = 0
                missed = []
                for idx, row in subcsv.iterrows():
                    look_for = tuple([row[c] for c in match_on])
                    search = (subload[match_on] == look_for).sum(axis=1)
                    full = np.where(search == len(match_on))[0]
                    if len(full) >= 1:
                        matched += 1
                    else:
                        try:
                            mmp_id = int(pathlib.Path(row['id']).stem.split('_',1)[1])
                        except ValueError:
                            mmp_id = int(pathlib.Path(row['id']).stem.split('_')[-1])
                        misclassified = load['id'].apply(lambda p: int(pathlib.Path(p).stem.split('_')[-1]))
                        second_chance = np.where(misclassified == mmp_id)[0]
                        if len(second_chance) == 0:
                            missed.append(idx)
                            missing_mmp.append(pathlib.Path(row['id']).stem)
                            if name not in missed_names:
                                missed_names.add(name)
                                print(f"Missed at least one result from {name}")
                        else:
                            matched += 1
                            load.loc[second_chance]
                n_results += matched
                if len(missed) > 0:
                    pass
                    #import pdb
                    #pdb.set_trace()
            #n_results = sum([len(load[load['source'] == name]) for name in specific_names])
            if n_results > 0:
                if n_results == expectation[expect]:
                    print("\t"+f"All expected {expect} results found!")
                else:
                    print("\t"+f"{expect} has {n_results}/{expectation[expect]} records (missing {expectation[expect]-n_results})")
    if not any_found:
        raise ValueError(f"No CSVs with prefix 'A3_T1' found in {check_path}")
    if len(missing_mmp) > 0:
        print(f"Benchmark {bench} missing these MMP files:")
        print("\n".join(missing_mmp))

