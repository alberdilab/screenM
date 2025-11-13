import json
import subprocess
from pathlib import Path

# Required CLI config:
PACKAGE_DIR = config["package_dir"]
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
        [f"{OUTDIR}/fastp/{sample}.html" for sample in SAMPLES],
        [f"{OUTDIR}/singlem/{sample}.fraction" for sample in SAMPLES],
        [f"{OUTDIR}/nonpareil_markers/{sample}.tsv" for sample in SAMPLES],
        [f"{OUTDIR}/nonpareil_reads/{sample}.tsv" for sample in SAMPLES]

rule counts:
    input:
        r1 = lambda wc: SAMPLES_MAP[wc.sample]["forward"],
        r2 = lambda wc: SAMPLES_MAP[wc.sample].get("reverse", "")
    output:
        json = f"{OUTDIR}/counts/{{sample}}.json"
    threads: 1
    message:
        "Counting reads for {wildcards.sample}..."
    run:
        import json, subprocess, shlex
        from pathlib import Path

        def count_reads_fastq(path: str) -> int:
            if not path or not Path(path).exists():
                return 0
            cmd = f"zcat {shlex.quote(path)} | wc -l" if path.endswith(".gz") \
                  else f"wc -l < {shlex.quote(path)}"
            lines = int(subprocess.check_output(cmd, shell=True, text=True).strip())
            return lines // 4

        r1_reads = count_reads_fastq(input.r1)
        has_r2 = bool(input.r2) and Path(input.r2).exists()
        reverse_reads = r1_reads if has_r2 else 0
        total_reads = r1_reads * 2 if has_r2 else r1_reads

        result = {
            "sample": wildcards.sample,
            "forward": input.r1,
            "reverse": input.r2,
            "forward_reads": r1_reads,
            "reverse_reads": reverse_reads,
            "total_reads": total_reads,
            "paired_end": has_r2,
            "note": "R2 reads inferred to equal R1"
        }

        Path(output.json).parent.mkdir(parents=True, exist_ok=True)
        with open(output.json, "w") as f:
            json.dump(result, f, indent=2)

        print(f"[✓] {wildcards.sample}: R1={r1_reads:,} | "
              f"R2={'inferred '+str(reverse_reads) if has_r2 else 'absent'} | "
              f"total={total_reads:,} → {output.json}")

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
        r2=f"{OUTDIR}/fastp/{{sample}}_2.fq"
    output:
        r1=f"{OUTDIR}/singlem/{{sample}}/prefilter_forward/{{sample}}_1.fna",
        r2=f"{OUTDIR}/singlem/{{sample}}/prefilter_reverse/{{sample}}_2.fna",
        profile=f"{OUTDIR}/singlem/{{sample}}.profile"
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
            -p {output.profile}
        """

rule spf:
    input: 
        r1=f"{OUTDIR}/fastp/{{sample}}_1.fq",
        r2=f"{OUTDIR}/fastp/{{sample}}_2.fq",
        profile=f"{OUTDIR}/singlem/{{sample}}.profile"
    output:
        f"{OUTDIR}/singlem/{{sample}}.fraction"
    params:
        workdir = lambda wc: f"{OUTDIR}/singlem/{wc.sample}"
    threads: 1
    message: "Calculating prokaryotic fraction of {wildcards.sample}..."
    shell:
        """
        module load singlem/0.19.0
        export SINGLEM_METAPACKAGE_PATH=/maps/datasets/globe_databases/singlem/5.4.0/S5.4.0.GTDB_r226.metapackage_20250331.smpkg.zb
        singlem microbial_fraction \
            -1 {input.r1} \
            -2 {input.r2} \
            -p {input.profile} > {output}
        """

rule merge_markers:
    input: 
        r1=f"{OUTDIR}/singlem/{{sample}}/prefilter_forward/{{sample}}_1.fna",
        r2=f"{OUTDIR}/singlem/{{sample}}/prefilter_reverse/{{sample}}_2.fna"
    output:
        f"{OUTDIR}/singlem/{{sample}}.fna"
    message: "Merging markers gene reads of {wildcards.sample}..."
    shell:
        """
        cat {input.r1} {input.r2} > {output}
        """

rule nonpareil_markers:
    input: 
        f"{OUTDIR}/singlem/{{sample}}.fna"
    output:
        npa=f"{OUTDIR}/nonpareil_markers/{{sample}}.npa"
        npc=f"{OUTDIR}/nonpareil_markers/{{sample}}.npc"
        npl=f"{OUTDIR}/nonpareil_markers/{{sample}}.npl"
        npo=f"{OUTDIR}/nonpareil_markers/{{sample}}.npo"
    threads: 1
    params:
        workdir = lambda wc: f"{OUTDIR}/nonpareil_markers/{wc.sample}"
    message: "Calculating marker gene redundancy of {wildcards.sample}..."
    shell:
        """
        module load singlem/0.19.0
        conda activate nonpareil    
        nonpareil -s {input} -T kmer -f fasta -b {params.workdir}
        """

rule nonpareil_markers_out:
    input: 
        npo=f"{OUTDIR}/nonpareil_markers/{{sample}}.npo",
        counts = f"{OUTDIR}/counts/{{sample}}.json"
    output:
        f"{OUTDIR}/nonpareil_markers/{{sample}}.tsv"
    threads: 1
    params:
        subset=READS,
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/nonpareil_project.py {input.npo} \
            --subset-reads {params.subset} \
            --total-reads $(python -c "import json; print(json.load(open('{input.counts}'))['total_reads'])") \
            -o {output}
        """

rule merge_reads:
    input: 
        r1=f"{OUTDIR}/fastp/{{sample}}_1.fq",
        r2=f"{OUTDIR}/fastp/{{sample}}_2.fq",
    output:
        f"{OUTDIR}/fastp/{{sample}}.fq"
    message: "Merging reads of {wildcards.sample}..."
    shell:
        """
        cat {input.r1} {input.r2} > {output}
        """

rule nonpareil_reads:
    input: 
        f"{OUTDIR}/fastp/{{sample}}.fq"
    output:
        npa=f"{OUTDIR}/nonpareil_reads/{{sample}}.npa"
        npc=f"{OUTDIR}/nonpareil_reads/{{sample}}.npc"
        npl=f"{OUTDIR}/nonpareil_reads/{{sample}}.npl"
        npo=f"{OUTDIR}/nonpareil_reads/{{sample}}.npo"
    threads: 1
    params:
        workdir = lambda wc: f"{OUTDIR}/nonpareil_reads/{wc.sample}"
    message: "Calculating marker gene redundancy of {wildcards.sample}..."
    shell:
        """
        module load singlem/0.19.0
        conda activate nonpareil    
        nonpareil -s {input} -T kmer -f fastq -b {params.workdir}
        """

rule nonpareil_reads_out:
    input: 
        npo=f"{OUTDIR}/nonpareil_reads/{{sample}}.npo",
        counts = f"{OUTDIR}/counts/{{sample}}.json"
    output:
        f"{OUTDIR}/nonpareil_reads/{{sample}}.tsv"
    threads: 1
    params:
        subset=READS,
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/nonpareil_project.py {input.npo} \
            --subset-reads {params.subset} \
            --total-reads $(python -c "import json; print(json.load(open('{input.counts}'))['total_reads'])") \
            -o {output}
        """