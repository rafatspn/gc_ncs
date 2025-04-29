import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

import pprint

def textbffloat(string):
    if '\\textbf' in string:
        string = string[string.index('{')+1:string.index('}')]
    return float(string)

def build_results_from_table(tablefile):
    with open(tablefile,'r') as f:
        results = {}
        reading = False
        rowcolor = False
        results_key = None
        unknown_results = []
        for _ in f.readlines():
            # Help to skip the table preamble/postlude
            if not reading:
                if _.startswith('\\hline'):
                    reading = True
            if not reading:
                continue
            if _.startswith('\\multirow'):
                # Might be accidentally recognized as a result row
                continue
            if _.startswith('\\end'):
                reading = False
                continue
            # Actual result row here
            if '(' in _ and ')' in _:
                row_contents = [c.lstrip().rstrip() for c in _.split('&')]
                if 'rowcolor' in row_contents[0]:
                    # Is this a change?
                    if not rowcolor:
                        results_key = None
                    # Drop the \rowcolor{...} portion
                    rowcolor = True
                    row_contents[0] = row_contents[0][row_contents[0].index('}')+1:]
                else:
                    # Is this a change?
                    if rowcolor:
                        results_key = None
                    rowcolor = False
                # Determine benchmark
                maybe_bench = row_contents[0]
                # Determine size
                maybe_size = row_contents[1]
                # Determine tool
                tool = row_contents[2]
                # Determine performance
                first100, best = [textbffloat(n) for n in row_contents[3][row_contents[3].index('(')+1:row_contents[3].index(')')].split(', ')]
                # Determine trials
                trials = textbffloat(row_contents[4][:row_contents[4].index(' ')])
                # Log based on key status
                if results_key is None:
                    # Do we have a key now?
                    if len(maybe_bench) > 0 and len(maybe_size) > 0:
                        results_key = (maybe_bench, maybe_size)
                        results[results_key] = unknown_results
                        unknown_results = list()
                to_log = {'tool': tool, 'first100': first100, 'best': best, 'trials': trials}
                if results_key is None:
                    unknown_results.append(to_log)
                else:
                    results[results_key].append(to_log)
    return results

def normalize_results(results):
    """
    # We want normalized x-y across benchmarks, first build the benchmark x-y
    # In the pre-finalized form, not all results are available -- but at least one
    # set of results are fully defined so ensure a consistent ordering is applied
    maxlen = 0
    all_tools = None
    for k,v in results.items():
        if len(v) > maxlen:
            maxlen = len(v)
            all_tools = [d['tool'] for d in v]
    """
    # Per-benchmark normalize
    bench_max = dict()
    for k,v in results.items():
        # Max speedup will be in the 'best' key
        for subv in v:
            if k not in bench_max:
                bench_max[k] = subv['best']
            if subv['best'] > bench_max[k]:
                bench_max[k] = subv['best']
    # Normalize as we go
    norm_results = dict()
    for k,v in results.items():
        norm_results[k] = {'first100': dict(), 'best': dict(), 'trials': dict()}
        for subv in v:
            norm_results[k]['first100'][subv['tool']] = subv['first100'] / bench_max[k]
            norm_results[k]['best'][subv['tool']] = subv['best'] / bench_max[k]
            # TRIALS ARE NOT NORMALIZED
            norm_results[k]['trials'][subv['tool']] = subv['trials']
    return norm_results

def make_plots(norm_results):
    # Split plots based on size (SM / XL)
    sm_results = dict((k,norm_results[k]) for k in norm_results if k[1] == 'SM')
    xl_results = dict((k,norm_results[k]) for k in norm_results if k[1] == 'XL')
    build_plot(sm_results, 'SM')
    build_plot(xl_results, 'XL')

def build_plot(norm_results, size):
    marker_mapping = {'SyR2K': 'd',
                      '3MM': 'o',
                      'Heat3D': 's',
                      'AMG': 'P',
                      'RSBench': 'X',
                      'SW4Lite': 'v',
                      }
    # Rong: drop default and +NCS for things that aren't us
    # If too busy then just pick two applications
    color_mapping = ['BLISS', # 'tab:blue'
                     #'BLISS+NCS', # 'tab:orange'
                     #'Default', # 'tab:green'
                     'GC+NCS (ours)', # 'tab:red'
                     'GCTLA', # 'tab:purple'
                     'GPTune', # 'tab:brown'
                     #'GPTune+NCS', # 'tab:pink'
                     'OpenTuner', # 'tab:gray'
                     #'OpenTuner+NCS', # 'tab:olive'
                     ]
    # 4 plots will be built: "SM-polybench", "SM-ECP", "XL-polybench", "XL-ECP"
    plot_grouped = {'Polybench/C': ('SyR2K','3MM','Heat3D'),
                    'ECP': ('AMG','RSBench','SW4Lite'),
                    }
    for (template, benchs) in plot_grouped.items():
        used_markers = dict()
        used_colors = dict()
        fig, ax = plt.subplots()
        # Key[benchmark,size] -> {'first100': blah, 'best': blah, 'trials': blah}
        for key, values in norm_results.items():
            # Grouping consideration
            if key[0] not in benchs:
                continue
            marker = marker_mapping[key[0]]
            for toolidx, tool in enumerate(color_mapping):
                if tool not in values['first100']:
                    continue
                ax.plot([100,values['trials'][tool]], [values['first100'][tool], values['best'][tool]],
                        marker=marker, color=f"C{toolidx}",
                        markersize=7,
                        )
                used_markers[key[0]] = marker
                used_colors[tool] = f"C{toolidx}"
        # Custom legend
        marker_handles = [matplotlib.lines.Line2D([0],[0], marker=marker, color='black', label=bench)
                            for bench, marker in used_markers.items()]
        color_handles = [matplotlib.patches.Patch(color=color, label=tech)
                            for tech, color in used_colors.items()]
        ax.legend(handles=marker_handles + color_handles,
                  loc= 'lower right')
        ax.set_xlabel('# Trials')
        ax.set_ylabel('Normalized Peak Performance')
        #ax.set_title(f'{template} {size}')
        format = 'png'
        nicetemplate = template
        if '/' in nicetemplate:
            nicetemplate = nicetemplate[:nicetemplate.index('/')]
        fig.savefig(f"{nicetemplate}_{size}.{format}", dpi=300, format=format)

results = build_results_from_table('latex_table.txt')
results_norm = normalize_results(results)
pprint.pprint(results_norm)
make_plots(results_norm)

