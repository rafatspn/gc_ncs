# Plots

This directory includes materials to produce the figures and tables in the paper after running NCS and Data directory processes (in that order).

---

## Handle everything in one command:

[generate\_all\_figures.sh](./generate_all_figures.sh): Bash script that generates the figures needed for this paper (execution: `./generate_all_figures.sh` -- no arguments supported)

---

## Actual figure- and table- generating scripts:

[immediate\_ultimate\_analysis.py](./immediate_ultimate_analysis.py): Produces stdout that can be redirected as a LaTeX table for tables in the paper. The one-shot bash script ([generate\_all\_figures.sh](generate_all_figures.sh)) will save this output to `latex_table.txt` by default (execution: `python3 immediate_ultimate_analysis.py` -- no arguments supported)

[general\_results\_figure.py](./general_results_figure.py): Produces the figures as PNG images that correspond to figures from the paper and saves them to the `Figures` directory. Requires the latex table results to already exist (see `immediate_ultimate_analysis.py`). (execution: `python3 general_results_figure.py` -- no arguments supported)

---

## Supporting directories and scripts:

[../Data/rawsearches/](../Data/rawsearches): All CSVs of searches from various techniques (without NCS sorting -- provided in ready-to-use form)

[../Data/reordered\_searches](../Data/reordered_searches): All CSVs of searches after reordering with NCS (requires running processes in [../Data](../Data/) to prepare for this directory's use)

[combine\_seeds](./combine_seeds): Output storage location for stapled searches produced by `generate_all_figures.sh`

[Figures](./Figures): Output storage location for figure images produced by `general_results_figures.py`

[stapler.py](./stapler.py): Used to append multiple CSVs together for ease of subsequent postprocessing (execution: `python3 stapler.py --help` for arguments in detail)

[endToEnd.py](./endToEnd.py): Used to sort original searches using another ranking mechanism (such as NCS) and perform initial statistical analysis (exeuction: `python3 endToEnd.py --help` for arguments in detail).
