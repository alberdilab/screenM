#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import gzip
from concurrent.futures import ProcessPoolExecutor

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _count_fastq_reads(path: Path) -> int:
    """
    Count reads in a FASTQ/FASTQ.GZ file: number_of_lines / 4.
    """
    if not path.is_file():
        raise FileNotFoundError(f"FASTQ file not found: {path}")

    if path.suffix == ".gz":
        opener = gzip.open
        mode = "rt"
    else:
        opener = open
        mode = "r"

    lines = 0
    with opener(path, mode) as fh:
        for _ in fh:
            lines += 1
    return lines // 4


def _count_reads_job(job: Tuple[str, str]) -> Tuple[str, int]:
    """
    Helper for parallel execution: (sample_name, path_str) -> (sample_name, reads)
    """
    sample, path_str = job
    reads = _count_fastq_reads(Path(path_str))
    return sample, reads


def dir_to_files(input: str, output: str, min_reads: int, threads: Optional[int] = None) -> Dict[str, Any]:
    """
    Scan a directory containing FASTQ/FASTQ.GZ files, detect paired-end samples,
    count reads from the first end (forward), and write a JSON of the form:

    {
      "min_reads": <min_reads>,
      "above": {
        "SampleA": {"forward": "...", "reverse": "...", "reads": 123456},
        ...
      },
      "below": {
        "SampleB": {"forward": "...", "reverse": "...", "reads": 7890},
        ...
      }
    }

    Samples are assigned to "above" if reads >= min_reads, otherwise to "below".

    Read counting is done in parallel using a process pool.
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

    # First pass: detect forward/reverse files per sample
    samples: Dict[str, Dict[str, str]] = {}

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

    # Build jobs: (sample, path_for_counting)
    jobs: List[Tuple[str, str]] = []
    for sample, info in samples.items():
        fq_path_str: Optional[str] = info.get("forward") or info.get("reverse")
        if fq_path_str is None:
            raise ValueError(f"Sample {sample!r} has no forward or reverse file.")
        jobs.append((sample, fq_path_str))

    # Parallel counting
    reads_per_sample: Dict[str, int] = {}
    with ProcessPoolExecutor(max_workers=threads) as exe:
        for sample, reads in exe.map(_count_reads_job, jobs):
            print(f"[{ts()}] Staging sample {sample}", flush=True)
            reads_per_sample[sample] = reads

    # Bucket into above / below and attach reads
    above: Dict[str, Dict[str, Any]] = {}
    below: Dict[str, Dict[str, Any]] = {}

    for sample, info in samples.items():
        reads = reads_per_sample[sample]
        entry: Dict[str, Any] = dict(info)
        entry["reads"] = reads

        if reads >= min_reads:
            above[sample] = entry
        else:
            below[sample] = entry

    result = {
        "min_reads": int(min_reads),
        "above": above,
        "below": below,
    }

    with output_path.open("w") as f:
        json.dump(result, f, indent=2)

    print(f"[✓] Found {len(samples)} samples.")
    print(f"[✓] {len(above)} samples ≥ {min_reads} reads (above).")
    print(f"[✓] {len(below)} samples < {min_reads} reads (below).")
    print(f"[✓] Wrote JSON to {output_path.resolve()}")

    return result