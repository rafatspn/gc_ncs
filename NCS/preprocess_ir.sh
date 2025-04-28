#!/bin/bash

SCRIPT="REPLACE_THIS/trim_irs.py" #trim_ir.py path
INP_PATH="REPLACE_THIS" #source of untrimmed IRs
OUT_PATH="REPLACE_THIS" #destination of trimmed IRs
BENCHMARK="REPLACE_THIS" #Benchmark name

#BENCHMARKs: _3mm, heat3d, amg, syr2k, sw4lite, rsbench

if [[ "$BENCHMARK" == "_3mm" ]]; then
    FUNCTION_NAMES="kernel_3mm"

elif [[ "$BENCHMARK" == "heat3d" ]]; then
    FUNCTION_NAMES="kernel_heat_3d"

elif [[ "$BENCHMARK" == "syr2k" ]]; then
    FUNCTION_NAMES="main"

elif [[ "$BENCHMARK" == "amg" ]]; then
    FUNCTION_NAMES="SScanIntArray,SScanDblArray,SScanProblemIndex,ReadData,IntersectBoxes,DistributeData,DestroyData,SetCosineVector,main"

elif [[ "$BENCHMARK" == "sw4lite" ]]; then
    FUNCTION_NAMES="" #not trimmed

elif [[ "$BENCHMARK" == "rsbench" ]]; then
    FUNCTION_NAMES="main,generate_poles,generate_window_params,read_CLI,run_event_based_simulation,run_history_based_simulation,run_event_based_simulation_optimization_1"

else
    echo "Unsupported BENCHMARK value: $BENCHMARK" >&2
    exit 1
fi

python3 $SCRIPT --inp_path=$INP_PATH --out_path=$OUT_PATH --function_names=$FUNCTION_NAMES
