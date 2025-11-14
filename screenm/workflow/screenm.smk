import json
import subprocess
from pathlib import Path

# Required CLI config:
PACKAGE_DIR = config["package_dir"]
INPUT_JSON  = config["input"]
OUTDIR      = config["output"]
READS       = config["reads"]
KMER        = config["kmer"]
COMPLETENESS     = config["completeness"]
DPI         = config["dpi"]
SEED        = config["seed"]

# Load data keys and paths
with open(INPUT_JSON) as fh:
    data = json.load(fh)

# Use only the "above" group (discard the too low seq samples)
SAMPLES_MAP = data.get("above", {})

SAMPLES = sorted(SAMPLES_MAP.keys())

# Fan-out over all samples
rule all:
    input:
        [f"{OUTDIR}/counts/{sample}.json" for sample in SAMPLES],
        [f"{OUTDIR}/fastp/{sample}.html" for sample in SAMPLES],
        [f"{OUTDIR}/singlem/{sample}.json" for sample in SAMPLES],
        [f"{OUTDIR}/nonpareil_markers/{sample}.json" for sample in SAMPLES],
        [f"{OUTDIR}/nonpareil_reads/{sample}.json" for sample in SAMPLES],
        [f"{OUTDIR}/json/{sample}.json" for sample in SAMPLES],
        f"{OUTDIR}/mash/mash_markers.tsv",
        f"{OUTDIR}/mash/mash_reads.tsv",
        f"{OUTDIR}/distill.json",
        f"{OUTDIR}/mash/mash_reads.json"

rule counts:
    input:
        INPUT_JSON
    output:
        json = f"{OUTDIR}/counts/{{sample}}.json"
    threads: 1
    run:
        import json
        from pathlib import Path

        sample = wildcards.sample

        with open(input[0]) as fh:
                data = json.load(fh)

        above = data.get("above", {}) or {}

        # Only ABOVE samples should be produced
        if sample not in above:
            raise ValueError(
                f"Sample {sample!r} is not listed in 'above'; "
                f"this rule should never run for it."
            )

        entry = above[sample]

        result = {
            "sample": sample,
            "reads": entry.get("reads", 0)
        }

        Path(output.json).parent.mkdir(parents=True, exist_ok=True)
        with open(output.json, "w") as f:
            json.dump(result, f, indent=2)

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
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Subsetting sample {wildcards.sample}"
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
        json=f"{OUTDIR}/fastp/{{sample}}_full.json"
    threads: 1
    shell:
        """
        module load fastp/0.24.0
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Quality-filtering sample {wildcards.sample}"
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

rule fastp_json:
    input: 
        f"{OUTDIR}/fastp/{{sample}}_full.json"
    output:
        f"{OUTDIR}/fastp/{{sample}}.json"
    params:
        package_dir=PACKAGE_DIR
    threads: 1
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/fastp_json.py -i {input} -o {output} --sample {wildcards.sample}
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
        siglemdir = f"{OUTDIR}/singlem/",
        workdir = lambda wc: f"{OUTDIR}/singlem/{wc.sample}"
    threads: 1
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Profiling marker genes of {wildcards.sample}"
        module load singlem/0.19.0
        export SINGLEM_METAPACKAGE_PATH=/maps/datasets/globe_databases/singlem/5.4.0/S5.4.0.GTDB_r226.metapackage_20250331.smpkg.zb
        mkdir -p {params.siglemdir}
        rm -rf {params.workdir}
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
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Calculating prokaryotic fraction of {wildcards.sample}"
        module load singlem/0.19.0
        export SINGLEM_METAPACKAGE_PATH=/maps/datasets/globe_databases/singlem/5.4.0/S5.4.0.GTDB_r226.metapackage_20250331.smpkg.zb
        singlem microbial_fraction \
            -1 {input.r1} \
            -2 {input.r2} \
            -p {input.profile} > {output}
        """

rule spf_json:
    input: 
        f"{OUTDIR}/singlem/{{sample}}.fraction"
    output:
        f"{OUTDIR}/singlem/{{sample}}.json"
    params:
        package_dir=PACKAGE_DIR
    threads: 1
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/spf_to_json.py \
            -i {input} \
            -o {output}
        """

rule merge_markers:
    input: 
        r1=f"{OUTDIR}/singlem/{{sample}}/prefilter_forward/{{sample}}_1.fna",
        r2=f"{OUTDIR}/singlem/{{sample}}/prefilter_reverse/{{sample}}_2.fna"
    output:
        f"{OUTDIR}/nonpareil_markers/{{sample}}.fna"
    message: "Merging markers gene reads of {wildcards.sample}..."
    shell:
        """
        cat {input.r1} {input.r2} > {output}
        """

rule nonpareil_markers:
    input: 
        f"{OUTDIR}/nonpareil_markers/{{sample}}.fna"
    output:
        npa=f"{OUTDIR}/nonpareil_markers/{{sample}}.npa",
        npc=f"{OUTDIR}/nonpareil_markers/{{sample}}.npc",
        npl=f"{OUTDIR}/nonpareil_markers/{{sample}}.npl",
        npo=f"{OUTDIR}/nonpareil_markers/{{sample}}.npo"
    threads: 1
    params:
        workdir = lambda wc: f"{OUTDIR}/nonpareil_markers/{wc.sample}",
        kmer = KMER
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Estimating marker redundancy of {wildcards.sample}"
        module load singlem/0.19.0
        nonpareil -s {input} -T kmer -f fasta -b {params.workdir} -k {params.kmer} -t {threads} > /dev/null 2>&1
        """

rule nonpareil_markers_out:
    input: 
        npo=f"{OUTDIR}/nonpareil_markers/{{sample}}.npo",
        counts = f"{OUTDIR}/counts/{{sample}}.json"
    output:
        tsv=f"{OUTDIR}/nonpareil_markers/{{sample}}.tsv",
        json=f"{OUTDIR}/nonpareil_markers/{{sample}}.json"
    threads: 1
    params:
        subset=READS * 2,
        completeness = COMPLETENESS,
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/nonpareil_project.py {input.npo} \
            --subset-reads {params.subset} \
            --total-reads $(python -c "import json; print(json.load(open('{input.counts}'))['reads'])") \
            --tsv-out {output.tsv} \
            --json-out {output.json} \
            --targets {params.completeness}
        """

rule merge_reads:
    input: 
        r1=f"{OUTDIR}/fastp/{{sample}}_1.fq",
        r2=f"{OUTDIR}/fastp/{{sample}}_2.fq"
    output:
        f"{OUTDIR}/nonpareil_reads/{{sample}}.fq"
    message: "Merging reads of {wildcards.sample}..."
    shell:
        """
        cat {input.r1} {input.r2} > {output}
        """

rule nonpareil_reads:
    input: 
        f"{OUTDIR}/nonpareil_reads/{{sample}}.fq"
    output:
        npa=f"{OUTDIR}/nonpareil_reads/{{sample}}.npa",
        npc=f"{OUTDIR}/nonpareil_reads/{{sample}}.npc",
        npl=f"{OUTDIR}/nonpareil_reads/{{sample}}.npl",
        npo=f"{OUTDIR}/nonpareil_reads/{{sample}}.npo"
    threads: 1
    params:
        workdir = lambda wc: f"{OUTDIR}/nonpareil_reads/{wc.sample}",
        kmer = KMER
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Estimating read redundancy of {wildcards.sample}"
        module load singlem/0.19.0
        nonpareil -s {input} -T kmer -f fastq -b {params.workdir} -k {params.kmer} -t {threads} > /dev/null 2>&1
        """

rule nonpareil_reads_out:
    input: 
        npo=f"{OUTDIR}/nonpareil_reads/{{sample}}.npo",
        counts = f"{OUTDIR}/counts/{{sample}}.json"
    output:
        tsv=f"{OUTDIR}/nonpareil_reads/{{sample}}.tsv",
        json=f"{OUTDIR}/nonpareil_reads/{{sample}}.json"
    threads: 1
    params:
        subset=READS * 2,
        completeness = COMPLETENESS,
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/nonpareil_project.py {input.npo} \
            --subset-reads {params.subset} \
            --total-reads $(python -c "import json; print(json.load(open('{input.counts}'))['reads'])") \
            --tsv-out {output.tsv} \
            --json-out {output.json} \
            --targets {params.completeness}
        """

rule mash_sketch_markers:
    input:
        expand(f"{OUTDIR}/nonpareil_markers/{{sample}}.fna", sample=SAMPLES)
    output:
        f"{OUTDIR}/mash/mash_markers.msh"
    threads: 1
    params:
        base = f"{OUTDIR}/mash/mash_markers",
        seed = SEED,
        kmer = KMER
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Sketching marker kmer profile"
        module load mash/2.3
        mash sketch -k {params.kmer} -S {params.seed} -o {params.base} {input} > /dev/null 2>&1
        """

rule mash_distance_markers:
    input:
        f"{OUTDIR}/mash/mash_markers.msh"
    output:
        f"{OUTDIR}/mash/mash_markers.dist"
    threads: 1
    params:
        seed = SEED
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Calculating mash distance of marker profiles"
        module load mash/2.3
        mash dist -S {params.seed} -p {threads} {input} {input} > {output}
        """

rule mash_matrix_markers:
    input:
        f"{OUTDIR}/mash/mash_markers.dist"
    output:
        matrix=f"{OUTDIR}/mash/mash_markers.mat",
        plot=f"{OUTDIR}/mash/mash_markers.png"
    threads: 1
    params:
        base = f"{OUTDIR}/mash/mash_reads",
        dpi = DPI,
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/mash_heatmap.py {input} \
            -o {output.plot} \
            -m {output.matrix} \
            --dpi {params.dpi}
        """

rule mash_medoids_markers:
    input:
        f"{OUTDIR}/mash/mash_markers.mat"
    output:
        sil=f"{OUTDIR}/mash/mash_markers.sil",
        ass=f"{OUTDIR}/mash/mash_markers.tsv",
        med=f"{OUTDIR}/mash/mash_markers.med"
    threads: 1
    params:
        seed = SEED,
        kmax = len(SAMPLES_MAP),
        package_dir=PACKAGE_DIR,
        base=f"{OUTDIR}/mash/mash_markers"
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Calculating number of clusters based on marker genes"
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/kmedoids.py \
            -i {input} \
            -o {params.base} \
            --kmin 2 \
            --kmax {params.kmax} \
            --seed {params.seed} \
            --silhouettes-out {output.sil} \
            --assignments-out {output.ass} \
            --medoids-out {output.med}
        """

rule mash_to_json_markers:
    input:
        dist=f"{OUTDIR}/mash/mash_markers.dist",
        clusters=f"{OUTDIR}/mash/mash_markers.tsv"
    output:
        f"{OUTDIR}/mash/mash_markers.json"
    threads: 1
    params:
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/mash_to_json.py \
            --dist {input.dist} \
            --clusters {input.clusters} \
            --kind markers \
            --output {output}
        """

rule mash_sketch_reads:
    input:
        expand(f"{OUTDIR}/nonpareil_reads/{{sample}}.fq", sample=SAMPLES)
    output:
        f"{OUTDIR}/mash/mash_reads.msh"
    threads: 1
    params:
        base = f"{OUTDIR}/mash/mash_reads",
        seed = SEED,
        kmer = KMER
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Sketching read kmer profile"
        module load mash/2.3
        mash sketch -k {params.kmer} -S {params.seed} -o {params.base} {input} > /dev/null 2>&1
        """

rule mash_distance_reads:
    input:
        f"{OUTDIR}/mash/mash_reads.msh"
    output:
        f"{OUTDIR}/mash/mash_reads.dist"
    threads: 1
    params:
        seed = SEED
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Calculating mash distance of read profiles"
        module load mash/2.3
        mash dist -S {params.seed} -p {threads} {input} {input} > {output}
        """

rule mash_matrix_reads:
    input:
        f"{OUTDIR}/mash/mash_reads.dist"
    output:
        matrix=f"{OUTDIR}/mash/mash_reads.mat",
        plot=f"{OUTDIR}/mash/mash_reads.png"
    threads: 1
    params:
        base = f"{OUTDIR}/mash/mash_reads",
        dpi = DPI,
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/mash_heatmap.py {input} \
            -o {output.plot} \
            -m {output.matrix} \
            --dpi {params.dpi}
        """

rule mash_medoids_reads:
    input:
        f"{OUTDIR}/mash/mash_reads.mat"
    output:
        sil=f"{OUTDIR}/mash/mash_reads.sil",
        ass=f"{OUTDIR}/mash/mash_reads.tsv",
        med=f"{OUTDIR}/mash/mash_reads.med"
    threads: 1
    params:
        seed = SEED,
        kmax = len(SAMPLES_MAP),
        package_dir=PACKAGE_DIR,
        base=f"{OUTDIR}/mash/mash_reads"
    shell:
        """
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] Calculating number of clusters based on reads"
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/kmedoids.py \
            -i {input} \
            -o {params.base} \
            --kmin 2 \
            --kmax {params.kmax} \
            --seed {params.seed} \
            --silhouettes-out {output.sil} \
            --assignments-out {output.ass} \
            --medoids-out {output.med}
        """

rule mash_to_json_reads:
    input:
        dist=f"{OUTDIR}/mash/mash_reads.dist",
        clusters=f"{OUTDIR}/mash/mash_reads.tsv"
    output:
        f"{OUTDIR}/mash/mash_reads.json"
    threads: 1
    params:
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/mash_to_json.py \
            --dist {input.dist} \
            --clusters {input.clusters} \
            --kind reads \
            --output {output}
        """

rule sample_json:
    input:
       counts=f"{OUTDIR}/counts/{{sample}}.json",
       fastp=f"{OUTDIR}/fastp/{{sample}}.json",
       singlem=f"{OUTDIR}/singlem/{{sample}}.json",
       nonpareil_reads=f"{OUTDIR}/nonpareil_reads/{{sample}}.json",
       nonpareil_markers=f"{OUTDIR}/nonpareil_markers/{{sample}}.json"
    output:
        f"{OUTDIR}/json/{{sample}}.json"
    threads: 1
    params:
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/sample_json.py \
            --count {input.counts} \
            --fastp {input.fastp} \
            --singlem {input.singlem} \
            --nonpareil-reads {input.nonpareil_reads} \
            --nonpareil-markers {input.nonpareil_markers} \
            --output {output} 
        """

rule merge_json:
    input:
       expand(f"{OUTDIR}/json/{{sample}}.json", sample=SAMPLES)
    output:
        f"{OUTDIR}/results.json"
    threads: 1
    params:
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/merge_json.py \
            -i {input} \
            -o {output} 
        """

rule distill_results:
    input:
       data=f"{OUTDIR}/data.json",
       results=f"{OUTDIR}/results.json"
    output:
        f"{OUTDIR}/distill.json"
    threads: 1
    params:
        package_dir=PACKAGE_DIR
    shell:
        """
        module load singlem/0.19.0
        python {params.package_dir}/workflow/scripts/distill_results.py \
            --data-json {input.data} \
            --results-json {input.results} \
            -o {output} 
        """