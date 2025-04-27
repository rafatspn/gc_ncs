import os
import json
import argparse
import pandas as pd
import numpy as np

def read_csv(data_path, files):
    dataframe = []
    for file in files:
        df = pd.read_csv(os.path.join(data_path, file))
        dataframe.append(df)

    combined_df = pd.concat(dataframe, ignore_index=True)

    return combined_df

def get_filename(data):
    data['filename'] = data.apply(
        lambda row: f"{os.path.splitext(os.path.basename(row['id']))[0]}", axis=1
    )
    return data

def calculate_speedup(data, default_time):
    data['speedup'] = data.apply(lambda row: default_time[row['size']] / row['objective'], axis=1)
    return data

def drop_duplicate_data(df, column_name):
    return df.drop_duplicates(subset=[column_name])

def filter_csv(data, filters):
    filtered_df = data.copy()
    
    if "size" in filters:
        filtered_df = filtered_df[filtered_df["size"].isin(filters["size"])]

    if "source" in filters:
        source_filter = filtered_df["source"].apply(lambda x: any(sub in str(x) for sub in filters["source"]))
        filtered_df = filtered_df[source_filter]

    return filtered_df

def clusterization_by_percentile(data, class_by, class_name, percentile):
    threshold = data[class_by].quantile(percentile / 100.0)
    data[class_name] = (data[class_by] >= threshold).astype(int)
    return data

def save_data(data, out_dir, file_name):
    output_path = os.path.join(out_dir, file_name)
    data.to_csv(output_path, index=False)
    print(f"Processed file saved as: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train Test csv splitting")
    parser.add_argument("--inp_path", type=str, required=True, help="data set path")
    parser.add_argument("--out_path", type=str, required=True, help="output path")
    parser.add_argument("--csv_files", type=str, required=True, help="csv file names")
    parser.add_argument("--filters", type=str, required=False, help="filter parameters to divide the dataset based on searches")
    parser.add_argument("--out_file", type=str, required=False, help="output file name")
    parser.add_argument("--default_time", type=str, required=False, help="default times to calculate speedup")
    parser.add_argument("--class_by", type=str, required=False, help="classify by column")
    parser.add_argument("--class_name", type=str, required=False, help="Class column name")
    parser.add_argument("--filename", type=str, required=False, help="Fix file name")
    parser.add_argument("--percentile", type=str, required=False, help="percentile for percentile based classificatoin")
    parser.add_argument("--drop_duplicate", type=str, required=False, help="removes duplicate entries")
    parser.add_argument("--dup_col", type=str, required=False, help="duplicate column")

    args = parser.parse_args()

    csv_files = args.csv_files.split(",")

    data = read_csv(args.inp_path, csv_files)

    if args.filename:
        data = get_filename(data)

    if args.default_time:
        default_time = json.loads(args.default_time)
        data = calculate_speedup(data, default_time)

    if args.drop_duplicate:
        data = drop_duplicate_data(data, 'filename')

    if args.filters:
        filters = json.loads(args.filters)
        data = filter_csv(data, filters)

    if args.percentile:
        percentile = float(args.percentile)
        data = clusterization_by_percentile(data, args.class_by, args.class_name, percentile)

        label_counts_per_size = {}

        for size in data["size"].unique():
            size_subset = data[data["size"] == size]  # Filter data by size
            label_counts = size_subset[args.class_name].value_counts().to_dict()  # Count occurrences of each label
            label_counts_per_size[size] = label_counts

        # Print the results
        for size, counts in label_counts_per_size.items():
            print(f"Size: {size}")
            for label, count in counts.items():
                print(f"  Label {label}: {count}")

    save_data(data, args.out_path, args.out_file)

if __name__ == "__main__":
    main()