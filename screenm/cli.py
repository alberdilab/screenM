import argparse
import os
import sys
import subprocess
import yaml
import random
import pandas as pd
from pathlib import Path
import pathlib
from datetime import datetime
from collections import defaultdict
from screenm.utils import *

#####
# screenM installation path
#####

PACKAGE_DIR = Path(__file__).parent
CONFIG_PATH = PACKAGE_DIR / "workflow" / "config.yaml"

def load_config():
    """Load fixed variables from config.yaml."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return {}

config_vars = load_config()

###
# Define text colors
###

HEADER1 = "\033[1;95m"
ERROR = "\033[1;31m"
INFO = "\033[1;34m"
RESET = "\033[0m"
END = "\033[1;92m"

###
# Snakemake launcher
###

def run_screenm_pipeline(input, output, threads, seed):
    snakemake_command = [
        "/bin/bash", "-c",
        "snakemake "
        f"-s {PACKAGE_DIR / 'workflow' / 'screenm.smk'} "
        f"--directory {output} "
        f"--cores {threads} "
        f"--quiet 2>/dev/null "
        f"--configfile {CONFIG_PATH} "
        f"--config package_dir={PACKAGE_DIR} input={input} output={output} seed={seed}"
    ]
    subprocess.run(snakemake_command, shell=False, check=True)

#####
# ScreenM execution
#####

def main():
    parser = argparse.ArgumentParser(
        description="ScreenM: data screener for genome-resolved metagenomics",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-i", "--input", required=True, help="Path of the directory containing the metagenomic reads.")
    parser.add_argument("-o", "--output", required=False, default=os.getcwd(), type=pathlib.Path, help="Working directory. Default is the directory from which screenM is called.")
    parser.add_argument("-s", "--seed", required=False, type=int, default=random.randint(0, 9999), help="Random seed for reproducibility. If not set, results will vary across runs.")   
    parser.add_argument("-t", "--threads", default=1, required=False, help="Number of threads to use (Default: 1)")   

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    DATA_JSON =  "data.json"
    dir_to_files(input=args.input, output=args.output / DATA_JSON)

    run_screenm_pipeline(
                args.output / DATA_JSON,
                Path(args.output).resolve(), 
                args.threads, 
                args.seed)