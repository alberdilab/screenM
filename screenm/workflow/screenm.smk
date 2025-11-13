import json
import subprocess
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
        INPUT_JSON,
        [f"{OUTDIR}/fastp/{sample}.html" for sample in SAMPLES]

rule depth:
    input:
        json=INPUT_JSON
    output:
        json=INPUT_JSON
    threads: 2
    message: "Updating {input.json} with read counts..."
    run:
        def count_reads(fq_path):
            fq = str(fq_path)
            if fq.endswith(".gz"):
                cmd = f"zcat {fq} | wc -l"
            else:
                cmd = f"wc -l < {fq}"
            res = subprocess.check_output(cmd, shell=True, text=True)
            return int(int(res.strip()) / 4)

        with open(input.json) as f:
            samples = json.load(f)

        for sample, info in samples.items():
            total = 0
            for direction in ["forward", "reverse"]:
                fq = info.get(direction)
                if fq and Path(fq).exists():
                    n = count_reads(fq)
                    info[f"{direction}_reads"] = n
                    total += n
                else:
                    info[f"{direction}_reads"] = 0
            info["total_reads"] = total

        # overwrite original
        with open(output.json, "w") as f:
            json.dump(samples, f, indent=2)

        print(f"[✓] Updated {len(samples)} samples in {output.json}")

rule seqtk:
    input: 
        r1 = lambda wc: SAMPLES_MAP[wc.sample]["forward"],
        r2 = lambda wc: SAMPLES_MAP[wc.sample].get("reverse", "")
    output:
        r1=f"{OUTDIR}/seqtk/{{sample}}_1.fq",
        r2=f"{OUTDIR}/seqtk/{{sample}}_2.fq"
    threads: 1
    message: "Subsetting sample {wildcards.sample}..."
    shell:
        """
        module load seqtk/1.4
        seqtk sample -s100 {input.r1} 1000000 > {output.r1}
        seqtk sample -s100 {input.r2} 1000000 > {output.r12}
        """

rule fastp:
    input: 
        r1=f"{OUTDIR}/seqtk/{{sample}}_1.fq",
        r2=f"{OUTDIR}/seqtk/{{sample}}_2.fq"
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