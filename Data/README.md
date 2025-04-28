# Data

This directory includes materials for postprocessing NCS and other search data (as CSVs; no IR data needs to be present here).
Prior to starting these tasks, all data should be moved into a subdirectory named `A2_Results_convert`, with a separate subdirectory beneath this level per benchmark (ie: A2\_Results\_convert/3mm, for the Polybench/C 3mm benchmark).

---

## Run both steps automatically:

[conversion.sh](./conversion.sh): Driver bash script that executes data conversion from NCS to postprocessing format (execution: `./conversion.sh` -- no arguments supported).
This script executes all other scripts in the directory, but we detail them below to assist in their understanding and usage.

---

## Step one:
Convert NCS searches from IR filenames to search space representation for subsequent analysis

[mass\_convert.py](./mass_convert.py): Runs reconfigure\_from\_mmp.py on each benchmark to prepare data from NCS for use in postprocessing (execution: `python3 mass_convert.py` -- no arguments supported)

[reconfigure\_from\_mmp.py](./reconfigure_from_mmp.py): Converts CSV "mmp" filenames to configurations for use in postprocessing, (execution: `python3 reconfigure_from_mmp.py --help` for arguments in detail)

[reconfigure\_from\_train\_mmp.py](./reconfigure_from_train_mmp.py): Converts other CSVs from "mmp" filenames to configurations used in postprocessing (execution: `python3 reconfigure_from_train_mmp.py --help` for arguments in detail)

[stapler.py](./stapler.py): Used to append multiple CSVs together for ease of subsequent postprocessing (execution: `python3 stapler.py --help` for arguments in detail)

[check\_expectations.py:](./check_expectations.py): Ensures that all expected data is converted by `mass_convert.py` (execution: `python3 check_expectations.py` -- no arguments supported; may be skipped during direct experiment replication)

---

## Step two:
Reorder autotuning searches from other techniques using NCS data.

[rawsearches/](./rawsearches): All CSVs of searches from various techniques (without NCS sorting)

[endToEnd.py](./endToEnd.py): Used to sort original searches using another ranking mechanism (such as NCS) and perform initial statistical analysis (exeuction: `python3 endToEnd.py --help` for arguments in detail).

[check\_reorder.py](./check_reorder.py): Ensures that all reordered CSVs include expected results based on the initial raw search data -- may be skipped during direct experiment replication (execution: `python3 check_reorder.py` -- no arguments supported)


