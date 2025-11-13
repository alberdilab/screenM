import json
from pathlib import Path

# Required CLI config:
INPUT_JSON  = config["input"]
OUTDIR      = config["output_dir"]
SEED        = config["seed"]

# Load data keys and paths
with open(SAMPLES_JSON) as fh:
    SAMPLES_MAP = json.load(fh)

SAMPLES = sorted(SAMPLES_MAP.keys())

# Helper to fetch inputs from JSON for a given sample
def read(wc):
    ent = SAMPLES_MAP[wc.sample]
    fwd = ent["forward"]
    rev = ent.get("reverse")
    return [fwd] if rev is None else [fwd, rev]

# Fan-out over all samples
rule all:
    input:
        [f"{OUTDIR}/{s}/started.ok" for s in SAMPLES],
        f"{OUTDIR}/manifest.tsv"

rule start:
    input: read
    output: touch(f"{OUTDIR}/{{sample}}/started.ok")
    message:
        "Starting sample {wildcards.sample} with {len(input)} file(s): {input}"
    shell:
        r"""
        mkdir -p {OUTDIR}/{wildcards.sample}
        # >>> replace this block with your real first tool, e.g., fastp/fastqc/host-filtering <<<
        # here we just record which files would be processed:
        printf "sample\tfile\n" > {OUTDIR}/{wildcards.sample}/inputs.tsv
        for f in {{" ".join(input)}}; do
            printf "{wildcards.sample}\t%s\n" "$f" >> {OUTDIR}/{wildcards.sample}/inputs.tsv
        done
        touch {output}
        """