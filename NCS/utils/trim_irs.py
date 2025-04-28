import os
import sys
import argparse
import llvmlite.ir as ir
import llvmlite.binding as llvm


def trim_ir(filename, ir_code, function_names, out_dir):
    module = llvm.parse_assembly(ir_code)
    try:
        for func_name in function_names:
            func = module.get_function(func_name)
            filename = os.path.basename(filename).replace('.ll', '.txt')
            with open(os.path.join(out_dir, filename), "w") as f:
                f.write(str(func))
    except Exception as e:
        print(f"Error in file: {filename}")
        print(e)


def main():
    parser = argparse.ArgumentParser("Trim IRs")

    parser.add_argument("--inp_path", type=str, required=True, help="Source of Untrimmed IRs")
    parser.add_argument("--out_path", type=str, required=True, help="Destination of Trimmed IRs")
    parser.add_argument("--function_names", type=str, required=False, help="Function names to be extracted")

    args = parser.parse_args()

    for filename in os.listdir(args.inp_path):
        if filename.endswith(".ll"):
            # print(f"Processing: {filename}")
            file_path = os.path.join(args.inp_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    content = file.read()
                    trim_ir(filename, content, args.function_names.split(","),args.out_path)

if __name__ == "__main__":
    main()
