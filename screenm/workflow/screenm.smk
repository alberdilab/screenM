import json
from pathlib import Path

# Required CLI config:
INPUT_JSON  = config["input"]
OUTDIR      = config["output"]
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

rule fastp:
    input: read
    output:
        r1=f"{OUTPUT_DIR}/preprocessing/fastp/{{sample}}_1.fq.gz",
        r2=f"{OUTPUT_DIR}/preprocessing/fastp/{{sample}}_2.fq.gz",
        html=f"{OUTPUT_DIR}/preprocessing/fastp/{{sample}}.html",
        json=f"{OUTPUT_DIR}/preprocessing/fastp/{{sample}}.json"
    params:
        fastp_module={FASTP_MODULE}
    threads: 4
    resources:
        mem_mb=lambda wildcards, input, attempt: max(8*1024, int(input.size_mb * 5) * 2 ** (attempt - 1)),
        runtime=lambda wildcards, input, attempt: max(15, int(input.size_mb / 1024 * 3) * 2 ** (attempt - 1))
    message: "Quality-filtering sample {wildcards.sample}..."
    shell:
        """
        module load {params.fastp_module}
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