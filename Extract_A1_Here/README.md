# IR and CSV Performance Data

---

## Acquire data

Download all of the IR and CSV data from [the Zenodo artifact](https://zenodo.org/records/15282775) using the "Download All" button.
Please note that the archive download is 3.2 GB, but after fully unzipping the total dataset size on disk is 24.82 GB.
Move the file here and unzip it, then unzip all directories within the archive here as well.
This can be accomplished via the shell command: ``for f in `ls *.zip`; do unzip $f; done;``

The resulting file structure should be:

```
./*_collated.csv
./*/mmp_*.ll
./syr2k_all_SM.csv
./syr2k_all_XL.csv
```

Where \*'s will be replaced with each benchmark name (3mm, amg, heat3d, rsbench, sw4lite, syr2k).
Note that syr2k has TWO archives; the "exhaustive" archive includes every single IR for the entire tuning space of the syr2k benchmark for the SM and XL dataset sizes.
The performance of these exhaustive datasets are tracked separately in syr2k\_all\_SM.csv and syr2k\_all\_XL.csv, respectively.
The other syr2k archive includes ONLY training data (covering sizes S, M, and L), and is non-exhaustive in nature.

