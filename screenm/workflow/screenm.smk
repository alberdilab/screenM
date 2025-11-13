import json
from pathlib import Path

# Required CLI config:
INPUT_JSON  = config["input"]
OUTDIR      = config["output"]
SEED        = config["seed"]

# Load data keys and paths
with open(INPUT_JSON) as fh:
    SAMPLES_MAP = json.load(fh)

SAMPLES = sorted(SAMPLES_MAP.keys())

# Fan-out over all samples
rule all:
    input:
        [f"{OUTDIR}/{s}/started.ok" for s in SAMPLES],
        f"{OUTDIR}/manifest.tsv"

rule start:
    input: 
        r1 = lambda wc: SAMPLES_MAP[wc.sample]["forward"],
        r2 = lambda wc: SAMPLES_MAP[wc.sample].get("reverse", "")
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

rule fastp:
    input: 
        r1 = lambda wc: SAMPLES_MAP[wc.sample]["forward"],
        r2 = lambda wc: SAMPLES_MAP[wc.sample].get("reverse", "")
    output:
        r1=f"{OUTDIR}/fastp/{{sample}}_1.fq.gz",
        r2=f"{OUTDIR}/fastp/{{sample}}_2.fq.gz",
        html=f"{OUTDIR}/fastp/{{sample}}.html",
        json=f"{OUTDIR}/fastp/{{sample}}.json"
    threads: 1
    message: "Quality-filtering sample {wildcards.sample}..."
    shell:
        """
        module load fastp/0.24.0
        fastp \
            --in1 {input.r1} --in2 {input.r2} \
            --out1 {output.r1} --out2 {output.r2} \
            --trim_poly_g \
            --trim_poly_x \
            --low_complexity_filter \
            --n_base_limit 5 \
            --qualified_quality_phred 20 \
            --length_required 60 \
            --thread {threads} \
            --html {output.html} \
            --json {output.json} \
            --adapter_sequence AGATCGGAAGAGCACACGTCTGAACTCCAGTCA \
            --adapter_sequence_r2 AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT
        """