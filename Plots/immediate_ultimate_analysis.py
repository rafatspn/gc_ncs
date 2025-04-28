import numpy as np
import pandas as pd
import pathlib
import warnings

CUTOFF = 100
QUICK_CUTOFF = 2

techniques = ['BO_RF','BO_RS','GPTune','GaussianCopula',
              'bliss','default','opentuner']
nonparam_cols = [
                 # BLISS
                 'actually_measured', 'acquisition_function', 'model_name', 'lookahead',
                 # GPTune
                 'isize',
                 # General results
                 'objective', 'elapsed_sec', 'elapsed_time', 'rank', 'predicted'
                 ]

def immediate_ultimate(csv, size, seed, tech, bench_prefix):
    #if size == 'XL' and tech == 'opentuner' and bench_prefix == 'sw4lite':
    #    import pdb
    #    pdb.set_trace()
    quick_result_idx = None
    quick = None
    ult_result_idx = None
    ult = None
    remain_len = None
    data = pd.read_csv(csv)
    #print(f"Read {len(data)} rows from {csv}")
    # Some data is reported as a rank rather than objective
    if 'objective' not in data.columns:
        if 'rank' not in data.columns:
            raise ValueError(f"CSV '{csv}' has neither objective nor rank columns")
        if bench_prefix != 'syr2k':
            raise ValueError(f"No oracle for benchmark {bench_prefix}; no reranking!")
        # Load the syr2k oracle
        oracle = pd.read_csv(f"collations/syr2k_all_{size}.csv")
        syr2k_cols = [f'p{_}' for _ in range(6)]
        new_objective = []
        for idx, row in data.iterrows():
            # Search term
            look_for = tuple([row[_] for _ in syr2k_cols])
            search = (oracle[syr2k_cols] == look_for).sum(axis=1)
            full_match = np.where(search == len(syr2k_cols))[0]
            if len(full_match) != 1:
                raise ValueError(f"Bad oracle search produces {len(full_match)} results for {csv}:{idx+1} '{row}'")
            new_objective.append(full_match[0])
        # Replace
        data.insert(0,'objective', new_objective)
    # Sentinel failures should be discarded
    sentinel_failures = data[data['objective'] == 1.0].index
    #print(f"Drop {len(sentinel_failures)} rows as failures")
    data = data.drop(index=sentinel_failures).reset_index(drop=True)
    # May have non-measured data that should be dropped
    if 'actually_measured' in data.columns.tolist():
        not_measured = data[data['actually_measured'] == False].index
        #print(f"Drop {len(not_measured)} rows as not measured")
        data = data.drop(index=not_measured).reset_index(drop=True)
    # Some objectives are reported as inverted values
    if len(data[data['objective'] < 0]) > 0:
        data['objective'] *= (-1)
    #print(f"Keep {len(data)} rows from {csv}")
    remain_len = len(data)
    if remain_len == 0:
        return quick, ult, ult_result_idx, remain_len

    # Ultimate-term effectiveness
    ult_result_idx = np.argmin(data['objective'])
    ult = data.loc[ult_result_idx,'objective']
    # Near-term effectiveness
    if len(data) >= QUICK_CUTOFF:
        quick_result_idx = np.argmin(data.loc[:CUTOFF,'objective'])
        quick = data.loc[quick_result_idx,'objective']
    """
    print(f"{bench_prefix} @ {size} <> {tech} @ seed {seed} (via: {csv})")
    if quick_result_idx is not None:
        print("\tIMMEDIATE BEST:"+str(data.loc[quick_result_idx,'objective']))
    print("\tULTIMATE BEST:"+str(data.loc[ult_result_idx,'objective']))
    """
    return quick, ult, ult_result_idx, remain_len

def table_prefix(idx):
    print(f"""
\\begin{{table}}[h]
\\caption{{Speedups of {'Polybench/C Apps' if idx == 0 else 'ECP Apps'}}}
\\label{{tbl:{'polybench_speedup' if idx == 0 else 'ecp_speedup'}}}
\\centering
\\begin{{tabular}}{{|c|c|c|c|c|}}
\\hline
\\multirow{{3}}*{{Benchmark}} & Target & \\multirow{{3}}*{{Search Tool}} & (First {CUTOFF}, Best) & Average \\\\
 & Size & & Speedup & \\# Trials \\\\
 & & & & to Best \\\\\\hline
""")
def table_suffix():
    print("""
\\hline
\\end{tabular}
\\end{table}
""")

def scan(basepath, altpaths=None):
    if altpaths is None:
        altpaths = list()
    benchmarks = [['syr2k','_3mm','heat3d'],['amg','rsbench','sw4lite']]
    blacklisted_newtech = ['default+NN']
    # TABLE NOTES
    # FIRST existing work
    # move GC+NCS to the bottom with a minor delimiter (2nd)
    # +NCS post-analysis as a separate part of the table (also line-deliminated, 3rd)
    nicename = {'default': 'Default',
                'GPTune': 'GPTune',
                'GPTune+NN': 'GPTune+NCS',
                'bliss': 'BLISS',
                'bliss+NN': 'BLISS+NCS',
                'opentuner': 'OpenTuner',
                'opentuner+NN': 'OpenTuner+NCS',
                'GaussianCopula': 'GCTLA',
                'GaussianCopula+NN': 'GC+NCS (ours)',
                'syr2k': 'SyR2K',
                '3mm': '3MM',
                'heat3d': 'Heat3D',
                'amg': 'AMG',
                'rsbench': 'RSBench',
                'sw4lite': 'SW4Lite',
                }
    #benchmarks = ['heat3d']
    for subtable_idx, subtable in enumerate(benchmarks):
        table_prefix(subtable_idx)
        for bench in subtable:
            if not (basepath / bench).exists():
                continue
            alts = [(alt / bench) for alt in altpaths if (alt / bench).exists()]
            bench = (basepath / bench)
            bench_prefix = bench.stem.lstrip('_').split("_",1)[0]
            results = dict()
            for csv in sorted(bench.iterdir()):
                # Identify the technique
                tech = [_ for _ in techniques if _ in csv.name][0]
                if tech in ['BO_RF','BO_RS','default']:
                    size = csv.stem.rsplit('_',1)[1]
                    seed = None
                else:
                    size, seed = csv.stem.rsplit('_',2)[1:]
                #print(f"Identified {csv} as benchmark {bench_prefix} technique {tech} size {size} seed {seed}")
                if size not in results:
                    results[size] = dict()
                if tech not in results[size]:
                    results[size][tech] = {'quick': list(),
                                           'ult': list(),
                                           'trials': list(),
                                           }
                quick, ult, ult_idx, csv_trials = immediate_ultimate(csv, size, seed, tech, bench_prefix)
                if ult is None:
                    continue
                if quick is not None:
                    results[size][tech]['quick'].append(quick)
                results[size][tech]['ult'].append(ult)
                results[size][tech]['trials'].append(ult_idx)
                # Now do alternatives
                for alt in alts:
                    if not (alt / csv.name).exists():
                        continue
                    altname = (alt / csv.name)
                    # Size and seed are identical to previous parsing
                    newtech = tech + '+NN'
                    if newtech not in results[size]:
                        results[size][newtech] = {'quick': list(),
                                                  'ult': list(),
                                                  'trials': list(),
                                                  }
                    quick, ult, ult_idx, csv_trials = immediate_ultimate(altname, size, seed, newtech, bench_prefix)
                    if ult is None:
                        continue
                    if quick is not None:
                        results[size][newtech]['quick'].append(quick)
                    results[size][newtech]['ult'].append(ult)
                    results[size][newtech]['trials'].append(ult_idx)
            # Determine the best result to highlight
            best = dict()
            for size in ['SM','XL']:
                best_quick = None
                best_quick_value = None
                best_ult = None
                best_ult_value = None
                # Find best value
                for tech in ['GaussianCopula','GPTune','bliss','opentuner']:
                    if tech not in results[size].keys():
                        continue
                    baseline = results[size]['default']['ult'][0]
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        qval = baseline / np.asarray(results[size][tech]['quick']).mean()
                    if best_quick_value is None:
                        if qval < 1.0:
                            best_quick_value = 1.0
                            best_quick = 'default'
                        else:
                            best_quick_value = qval
                            best_quick = tech
                    elif qval > best_quick_value:
                        best_quick_value = qval
                        best_quick = tech
                    uval = baseline / np.asarray(results[size][tech]['ult']).mean()
                    prior_uval = uval
                    if best_ult_value is None:
                        if uval < 1.0:
                            best_ult_value = 1.0
                            best_ult = 'default'
                        else:
                            best_ult_value = uval
                            best_ult = tech
                    elif uval > best_ult_value:
                        best_ult_value = uval
                        best_ult = tech
                    newtech = tech+"+NN"
                    if newtech not in results[size].keys():
                        continue
                    if newtech in blacklisted_newtech:
                        continue
                    qval = baseline / np.asarray(results[size][newtech]['quick']).mean()
                    if best_quick_value is None:
                        best_quick_value = qval
                        best_quick = newtech
                    elif qval > best_quick_value:
                        best_quick_value = qval
                        best_quick = newtech
                    uval = baseline / np.asarray(results[size][newtech]['ult']).mean()
                    if uval != prior_uval:
                        pass
                    if best_ult_value is None:
                        best_ult_value = uval
                        best_ult = newtech
                    elif uval > best_ult_value:
                        best_ult_value = uval
                        best_ult = newtech
                # Store it
                best[size] = {'quick': best_quick,
                              'ult': best_ult,
                              }
            # Output table contents
            for size in results.keys():
                if size not in ['SM','XL']:
                    continue
                multirow_bench = True
                multirow_size = True
                row_prefix = ''
                if size == 'XL':
                    row_prefix = '\\rowcolor{gray!25}'
                # NORMAL KEY ORDER:
                # GC+NN, GPTune, GaussianCopula, bliss, default, opentuner
                baseline = results[size]['default']['ult'][0]
                techkeys = ['default','GaussianCopula','GPTune','bliss','opentuner']
                maxidx = len(results[size].keys())
                middleidx = maxidx // 2 - int(maxidx % 2 != 1)
                curidx = 0
                for tech in techkeys:
                    if tech not in results[size].keys():
                        continue
                    # +1 because zero-based indexing
                    n_evals = np.asarray(results[size][tech]['trials']).mean()+1
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        vq = baseline / np.asarray(results[size][tech]['quick']).mean()
                    vu = baseline / np.asarray(results[size][tech]['ult']).mean()
                    #print(f"{bench_prefix}@{size} <> {tech} (ULT: {vu}) (QUICK: {vq})")
                    quick_prepost = ('','')
                    if tech == best[size]['quick'] or results[size][tech]['quick'] == results[size][best[size]['quick']]['quick']:
                        quick_prepost = ('\\textbf{','}')
                    ult_prepost = ('','')
                    if tech == best[size]['ult'] or results[size][tech]['ult'] == results[size][best[size]['ult']]['ult']:
                        ult_prepost = ('\\textbf{','}')
                    # Have to know how many rows to reuse this on
                    if multirow_bench and curidx == middleidx:
                        #bench_portion = f"\\multirow{{{maxidx-curidx}}}{{*}}{{ {nicename[bench_prefix]} }}"
                        bench_portion = f"{nicename[bench_prefix]}"
                        multirow_bench = False
                    else:
                        bench_portion = " "
                    if multirow_size and curidx == middleidx:
                        #size_portion = f"\\multirow{{{maxidx-curidx}}}{{*}}{{ {size} }}"
                        size_portion = f"{size}"
                        multirow_size = False
                    else:
                        size_portion = " "
                    suffix = ""
                    if bench_portion != " " or 'ours' in nicename[tech]:
                        suffix = "\\cline{3-5}"
                    print(f"{row_prefix}{bench_portion} & {size_portion} & {nicename[tech]} & ({quick_prepost[0]}{f'{vq:.3f}' if not np.isnan(vq) else '--' if tech != 'default' else '1.000'}{quick_prepost[1]}, {ult_prepost[0]}{vu:.3f}{ult_prepost[1]}) & {f'{n_evals:.2f}' if n_evals-int(n_evals)!=0.0 else f'{n_evals:g}'} \\\\{suffix}")
                    curidx += 1
                for tech in techkeys:
                    tech = tech+"+NN"
                    if tech not in results[size].keys() or tech == 'default+NN':
                        continue
                    # +1 because zero-based indexing
                    n_evals = np.asarray(results[size][tech]['trials']).mean()+1
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        vq = baseline / np.asarray(results[size][tech]['quick']).mean()
                    vu = baseline / np.asarray(results[size][tech]['ult']).mean()
                    #print(f"{bench_prefix}@{size} <> {tech} (ULT: {vu}) (QUICK: {vq})")
                    quick_prepost = ('','')
                    if tech == best[size]['quick'] or results[size][tech]['quick'] == results[size][best[size]['quick']]['quick']:
                        quick_prepost = ('\\textbf{','}')
                    ult_prepost = ('','')
                    if tech == best[size]['ult'] or results[size][tech]['ult'] == results[size][best[size]['ult']]['ult']:
                        ult_prepost = ('\\textbf{','}')
                    # Have to know how many rows to reuse this on
                    if multirow_bench and curidx == middleidx:
                        #bench_portion = f"\\multirow{{{maxidx-curidx}}}{{*}}{{ {nicename[bench_prefix]} }}"
                        bench_portion = f"{nicename[bench_prefix]}"
                        multirow_bench = False
                    else:
                        bench_portion = " "
                    if multirow_size and curidx == middleidx:
                        #size_portion = f"\\multirow{{{maxidx-curidx}}}{{*}}{{ {size} }}"
                        size_portion = f"{size}"
                        multirow_size = False
                    else:
                        size_portion = " "
                    suffix = ""
                    if bench_portion != " " or 'ours' in nicename[tech]:
                        suffix = "\\cline{3-5}"
                    print(f"{row_prefix}{bench_portion} & {size_portion} & {nicename[tech]} & ({quick_prepost[0]}{f'{vq:.3f}' if not np.isnan(vq) else '--' if tech != 'default' else '1.000'}{quick_prepost[1]}, {ult_prepost[0]}{vu:.3f}{ult_prepost[1]}) & {f'{n_evals:.2f}' if n_evals-int(n_evals)!=0.0 else f'{n_evals:g}'} \\\\{suffix}")
                    curidx += 1
            print("\\hline")
        table_suffix()

scan(pathlib.Path('rawsearches'), altpaths=[pathlib.Path('reordered_searches')])

