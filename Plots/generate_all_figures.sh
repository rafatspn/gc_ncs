#!/bin/bash

collate=( "syr2k" "3mm" "heat3d" "amg" "rsbench" "sw4lite" );
types=( "GaussianCopula" "opentuner" "bliss" "GPTune" );
for c in ${collate[@]}; do
    for t in ${types[@]}; do
        todo=("python3 "
              "stapler.py "
              "--from rawsearches/${c}/*${t}*SM*.csv "
              "--to combine_seeds/${c}/${t}_SM.csv "
              "--overwrite "
          );
        todo="${todo[*]}";
        echo "${todo}";
        eval "${todo}";
        todo=("python3 "
             "endToEnd.py "
             "arafat_all_convert/${c}/all_arafat_${c}.csv "
             "--rank-column score "
             "--invert-sort "
             "--searches combine_seeds/${c}/${t}_SM.csv" #search_compilations/${c}/*${t}*.csv "
             "--export Figures/${c}_${t}_SM "
             );
        todo="${todo[*]}";
        echo "${todo}";
        eval "${todo}";
        if [ $? -ne 0 ]; then
            exit;
        fi;
        todo=("python3 "
              "stapler.py "
              "--from rawsearches/${c}/*${t}*XL*.csv "
              "--to combine_seeds/${c}/${t}_XL.csv "
              "--overwrite "
          );
        todo="${todo[*]}";
        echo "${todo}";
        eval "${todo}";
        todo=("python3 "
             "endToEnd.py "
             "arafat_all_convert/${c}/all_arafat_${c}.csv "
             "--rank-column score "
             "--invert-sort "
             "--searches combine_seeds/${c}/${t}_XL.csv" #search_compilations/${c}/*${t}*.csv "
             "--export Figures/${c}_${t}_XL "
             );
        todo="${todo[*]}";
        echo "${todo}";
        eval "${todo}";
        if [ $? -ne 0 ]; then
            exit;
        fi;
    done;
done;
#python3 syr2k_global.py;
python3 immediate_ultimate_analysis.py > latex_table.txt;
python3 general_results_figure.py;

