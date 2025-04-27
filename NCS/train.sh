#!/bin/bash
#PBS -l walltime=6:00:00
#PBS -l select=1:system=sophia
#PBS -l filesystems=home
#PBS -A EE-ECP
#PBS -q by-gpu
#PBS -N t3mmcnn

cd /home/rafatspn/clemson

module use /soft/modulefiles ; module load conda; conda activate base

module list;
date;
which python3;


SCRIPT="REPLACE_THIS/multi_cnn_v3.py"
CSV_PATH="REPLACE_THIS" #path to the directory that contains the csv files generateed in the csv preprocessing step
IR_PATH="REPLACE_THIS" #path to the directory that contains trimmed IRs
OUT_PATH="REPLACE_THIS" #path to the directory to save the generated result csv

BENCHMARK="_3mm"
# other values of benchmark
# "heat3d"
# "amg"
# "rsbench"
# "syr2k"
# "sw4lite"

python3 $SCRIPT --csv_path=$CSV_PATH --csv_files="${BENCHMARK}_collated_gc.csv" --ir_path=$IR_PATH --out_path=$OUT_PATH --out_file="gc_result_${BENCHMARK}.csv"
python3 $SCRIPT --csv_path=$CSV_PATH --csv_files="${BENCHMARK}_collated_bliss.csv" --ir_path=$IR_PATH --out_path=$OUT_PATH --out_file="bliss_result_${BENCHMARK}.csv"
python3 $SCRIPT --csv_path=$CSV_PATH --csv_files="${BENCHMARK}_collated_GPTune.csv" --ir_path=$IR_PATH --out_path=$OUT_PATH --out_file="GPTune_result_${BENCHMARK}.csv"
python3 $SCRIPT --csv_path=$CSV_PATH --csv_files="${BENCHMARK}_collated_opentuner.csv" --ir_path=$IR_PATH --out_path=$OUT_PATH --out_file="opentuner_result_${BENCHMARK}.csv"

date;