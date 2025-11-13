import json
from pathlib import Path



def dir_to_files(input: str, output: str):
    """
    Scan a directory containing FASTQ/FASTQ.GZ files, detect paired-end samples,
    and write a JSON mapping: {sample_name: {"forward": <path>, "reverse": <path>}}.

    Example:
        dir_to_files("reads/", "results/data.json")

    The function handles naming like:
        sampleA_R1.fastq.gz / sampleA_R2.fastq.gz
        sampleB_1.fq / sampleB_2.fq
        sampleC_1.fastq / sampleC_2.fastq
    """
    input_path = Path(input)
    output_path = Path(output)

    # --- verify input dir ---
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input}")
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input}")

    # --- create output dir if missing ---
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- collect fastq/fq files (case-insensitive) ---
    fastq_files = list(input_path.rglob("*.[Ff][Aa][Ss][Tt][Qq]*")) + \
                  list(input_path.rglob("*.[Ff][Qq]*"))
    if not fastq_files:
        raise ValueError(f"No FASTQ files found in {input}")

    samples = {}

    for fq in fastq_files:
        fname = fq.name
        if "_R1" in fname or "_1" in fname:
            sample_name = (
                fname.replace("_R1", "")
                .replace("_1", "")
                .replace(".fastq.gz", "")
                .replace(".fq.gz", "")
                .replace(".fastq", "")
                .replace(".fq", "")
            )
            samples.setdefault(sample_name, {})["forward"] = str(fq.resolve())

        elif "_R2" in fname or "_2" in fname:
            sample_name = (
                fname.replace("_R2", "")
                .replace("_2", "")
                .replace(".fastq.gz", "")
                .replace(".fq.gz", "")
                .replace(".fastq", "")
                .replace(".fq", "")
            )
            samples.setdefault(sample_name, {})["reverse"] = str(fq.resolve())

    # --- write JSON safely ---
    with output_path.open("w") as f:
        json.dump(samples, f, indent=2)

    print(f"[✓] Found {len(samples)} samples.")
    print(f"[✓] Wrote JSON to {output_path.resolve()}")
    return samples