import json
import subprocess
from pathlib import Path

# Required CLI config:
INPUT_JSON  = config["input"]
OUTDIR      = config["output"]
READS       = config["reads"]
SEED        = config["seed"]

# Load data keys and paths
with open(INPUT_JSON) as fh:
    SAMPLES_MAP = json.load(fh)

SAMPLES = sorted(SAMPLES_MAP.keys())

# Fan-out over all samples
rule all:
    input:
        [f"{OUTDIR}/counts/{sample}.json" for sample in SAMPLES],
        [f"{OUTDIR}/fastp/{sample}.html" for sample in SAMPLES]

rule counts:
    input:
        json=INPUT_JSON
    output:
        f"{OUTDIR}/counts/{{sample}}.json"
    threads: 2
    message: "Updating {input.json} with read counts..."
    run:
            def count_reads(fq_path):
                """Fast system-level read counter"""
                if not fq_path or not Path(fq_path).exists():
                    return 0
                cmd = f"zcat {fq_path} | wc -l" if fq_path.endswith(".gz") else f"wc -l < {fq_path}"
                res = subprocess.check_output(cmd, shell=True, text=True)
                return int(int(res.strip()) / 4)

            r1_reads = count_reads(input.r1)
            r2_reads = count_reads(input.r2)
            total = r1_reads + r2_reads

            result = {
                "sample": wildcards.sample,
                "forward": input.r1,
                "reverse": input.r2,
                "forward_reads": r1_reads,
                "reverse_reads": r2_reads,
                "total_reads": total
            }

            Path(output[0]).parent.mkdir(parents=True, exist_ok=True)
            with open(output[0], "w") as f:
                json.dump(result, f, indent=2)

            print(f"[✓] {wildcards.sample}: {total:,} total reads")

rule seqtk:
    input: 
        r1 = lambda wc: SAMPLES_MAP[wc.sample]["forward"],
        r2 = lambda wc: SAMPLES_MAP[wc.sample].get("reverse", "")
    output:
        r1=f"{OUTDIR}/seqtk/{{sample}}_1.fq",
        r2=f"{OUTDIR}/seqtk/{{sample}}_2.fq"
    threads: 1
    params:
        reads=READS
    message: "Subsetting sample {wildcards.sample}..."
    shell:
        """
        module load seqtk/1.4
        seqtk sample -s100 {input.r1} {params.reads} > {output.r1}
        seqtk sample -s100 {input.r2} {params.reads} > {output.r2}
        """

rule fastp:
    input: 
        r1=f"{OUTDIR}/seqtk/{{sample}}_1.fq",
        r2=f"{OUTDIR}/seqtk/{{sample}}_2.fq"
    output:
        r1=f"{OUTDIR}/fastp/{{sample}}_1.fq",
        r2=f"{OUTDIR}/fastp/{{sample}}_2.fq",
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

rule singlem:
    input: 
        r1=f"{OUTDIR}/fastp/{{sample}}_1.fq",
        r2=f"{OUTDIR}/fastp/{{sample}}_2.fq",
    output:
        f"{OUTDIR}/singlem/{{sample}}.profile"
    params:
        workdir = lambda wc: f"{OUTDIR}/singlem/{wc.sample}"
    threads: 1
    message: "Profiling {wildcards.sample} with SingleM..."
    shell:
        """
        module load singlem/0.19.0
        export SINGLEM_METAPACKAGE_PATH=/maps/datasets/globe_databases/singlem/5.4.0/S5.4.0.GTDB_r226.metapackage_20250331.smpkg.zb
        singlem pipe \
            -1 {input.r1} \
            -2 {input.r2} \
            --working-directory {params.workdir} \
            -p {putput}
        """