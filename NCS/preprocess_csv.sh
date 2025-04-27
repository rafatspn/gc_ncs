#!/bin/bash
#PBS -l walltime=1:00:00
#PBS -l select=1:system=sophia
#PBS -l filesystems=home
#PBS -A EE-ECP
#PBS -q by-node
#PBS -N cnv

cd /home/rafatspn/clemson

module use /soft/modulefiles ; module load conda; conda activate base

module list;
date;
which python3;

#static variables
_3MM_DT='{"S":0.002964, "M": 0.090472, "L": 9.856659,"SM": 0.021467,"XL": 79.626002}'
HEAT3D_DT='{"S":0.000607, "M": 0.012067, "L": 5.111083,"SM": 0.003435,"XL": 48.378053}'
AMG_DT='{"S":1.3790032863616943, "M": 3.6291158199310303, "L": 10.488572359085085,"SM": 1.4934616088867188,"XL": 16.131489753723145}'
RSBENCH_DT='{"S":0.188405, "M": 0.93408, "L": 4.40241,"SM": 0.6588400000000001,"XL": 9.484095}'
SYR2K_DT='{"S":0.000245, "M": 0.007642, "L": 0.195827,"SM": 0.001656,"XL": 1.8196419999999998}'
SW4LITE_DT='{"S":4.2706800000000005, "M": 8.6565, "L": 13.0948,"SM": 5.27491,"XL": 16.0983}'

TUNERS=(gc bliss gptune opentuner)  
PCTS=(50 60 70 80 90) 

#changeable variables
SCRIPT="REPLACE_THIS/preprocess_csv.py" 
INP_PATH="REPLACE_THIS" #path to the collated csv for a particular benchmark
OUT_PATH=$INP_PATH
BENCHMARK="_3mm" #change this variable to change benchmark 
# other values of benchmark
# "heat3d"
# "amg"
# "rsbench"
# "syr2k"
# "sw4lite"
DEFAULT_TIME="$_3MM_DT" #change this variable based on benchmark variable

#extracts filenames, calculates speedup, and removes duplicates entries
python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH  --csv_files="${BENCHMARK}_collated.csv" --default_time="$DEFAULT_TIME" --filename=yes  --out_file="${BENCHMARK}_collated_speedup.csv" --drop_duplicate=true --dup_col=filename

#divide the dataset based on searches
python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH  --csv_files="${BENCHMARK}_collated_speedup.csv"  --filters='{"size":["S","M","L","SM","XL"], "source":["GaussianCopula", "rf"]}' --out_file="${BENCHMARK}_collated_gc.csv" 
python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH  --csv_files="${BENCHMARK}_collated_speedup.csv"  --filters='{"size":["S","M","L","SM","XL"], "source":["bliss", "rf"]}' --out_file="${BENCHMARK}_collated_bliss.csv" 
python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH  --csv_files="${BENCHMARK}_collated_speedup.csv"  --filters='{"size":["S","M","L","SM","XL"], "source":["gptune", "GPTune", "rf"]}' --out_file="${BENCHMARK}_collated_gptune.csv"  
python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH  --csv_files="${BENCHMARK}_collated_speedup.csv"  --filters='{"size":["S","M","L","SM","XL"], "source":["opentuner", "rf"]}' --out_file="${BENCHMARK}_collated_opentuner.csv"            

#generates labels based on percentiles
for tuner in "${TUNERS[@]}"; do
    csv="${BENCHMARK}_collated_${tuner}.csv"
    for pct in "${PCTS[@]}"; do
        python3 "$SCRIPT" \
            --inp_path="$INP_PATH" \
            --out_path="$OUT_PATH" \
            --csv_files="$csv" \
            --out_file="$csv" \
            --class_by="speedup" \
            --percentile="$pct" \
            --class_name="class_${pct}"
    done
done