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

SCRIPT="REPLACE_THIS/trim_irs.py" #trim_ir.py path
INP_PATH="REPLACE_THIS" #path of directory that holds the IR files
OUT_PATH="REPLACE_THIS" #path where the trimmed IRs should be saved
BENCHMARK="_3mm" #change this variable to change benchmark 
# other values of benchmark
# "heat3d"
# "amg"
# "rsbench"
# "syr2k"
# "sw4lite"

FUNCTION_NAMES="kernel_3mm" # if multiple functions to be extracted, they should be seperarted by comma 
FILE_TYPE=".ll" #for IR .ll
TASK="trim" #trim or convert

python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH --function_names=$FUNCTION_NAMES --file_type=$FILE_TYPE --task=$TASK
