#!/bin/bash

SCRIPT="REPLACE_THIS/trim_irs.py" #trim_ir.py path
INP_PATH="REPLACE_THIS" #source of untrimmed IRs
OUT_PATH="REPLACE_THIS" #destination of trimmed IRs

FUNCTION_NAMES="kernel_3mm" # if multiple functions to be extracted, they should be seperarted by comma 

python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH --function_names=$FUNCTION_NAMES
