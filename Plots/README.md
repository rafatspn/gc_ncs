Plots to produce figures and tables in the paper

[generate\_all\_figures.sh](./generate_all_figures.sh): Bash script that generates the figures needed for this paper (execution: `./generate_all_figures.sh` -- no arguments supported)

[rawsearches/](./rawsearches): All CSVs of searches from various techniques (without NCS sorting)

[reordered\_searches](./reordered_searches): All CSVs of searches after reordering with NCS

[combine\_seeds](./combine_seeds) Storage location for stapled searches produced by `generate_all_figures.sh`

[stapler.py](./stapler.py): Used to append multiple CSVs together for ease of subsequent postprocessing (execution: `python3 stapler.py --help` for arguments in detail)

[endToEnd.py](./endToEnd.py): Used to sort original searches using another ranking mechanism (such as NCS) and perform initial statistical analysis (exeuction: `python3 endToEnd.py --help` for arguments in detail).

[immediate\_ultimate\_analysis.py](./immediate_ultimate_analysis.py): Produces stdout that can be redirected as a LaTeX table for tables in the paper. The calling bash script will save this output to `latex_table.txt` by default (execution: `python3 immediate_ultimate_analysis.py` -- no arguments supported)

[general\_results\_figure.py](./general_results_figure.py): Produces the figures as PNG images that correspond to figures from the paper. Requires the latex table results to already exist (see `immediate_ultimate_analysis.py`). (execution: `python3 general_results_figure.py` -- no arguments supported)
