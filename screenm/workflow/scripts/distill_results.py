#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List
import statistics as stats


def load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Input JSON not found: {path}")
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"JSON in {path} is not an object/dict.")
    return data


def compute_screening_threshold(data_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    From data.json of the form:
      { "min_reads": N, "above": {...}, "below": {...} }
    compute counts and flag.
    """
    min_reads = data_json.get("min_reads")
    above = data_json.get("above", {}) or {}
    below = data_json.get("below", {}) or {}

    n_above = len(above)
    n_below = len(below)
    n_total = n_above + n_below

    if n_total == 0:
        percent_above = 0.0
    else:
        percent_above = 100.0 * n_above / n_total

    # Determine flag and message
    if n_total == 0:
        flag = 3
        message = (
            "No samples were found in the input data; cannot evaluate read threshold."
        )
    else:
        if percent_above == 100.0:
            flag = 1
            message = (
                f"All samples ({n_above}/{n_total}, {percent_above:.1f}%) are above the "
                f"read threshold ({min_reads} reads)."
            )
        elif percent_above >= 80.0:
            flag = 2
            message = (
                f"Most samples ({n_above}/{n_total}, {percent_above:.1f}%) are above the "
                f"read threshold ({min_reads} reads), but some are below."
            )
        else:
            flag = 3
            message = (
                f"Only {n_above}/{n_total} samples ({percent_above:.1f}%) are above the "
                f"read threshold ({min_reads} reads). "
                "As less than 80% of the samples are above the number of reads used for "
                "the estimations, a lower threshold should be chosen using the -r flag; "
                "note that this will make the estimations less accurate."
            )

    return {
        "reads_threshold": min_reads,
        "n_samples_total": n_total,
        "n_samples_above_threshold": n_above,
        "percent_above_threshold": percent_above,
        "flag_reads_threshold": flag,
        "message_reads_threshold": message,
    }


def compute_sequencing_depth(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute sequencing depth statistics from results.json, using
    samples[*].count.reads.
    """
    samples = results_json.get("samples", {}) or {}

    reads_list: List[int] = []
    for name, sample_data in samples.items():
        count_block = sample_data.get("count", {}) or {}
        reads = count_block.get("reads")
        if isinstance(reads, (int, float)):
            reads_list.append(int(reads))

    n_samples = len(reads_list)

    if n_samples == 0:
        return {
            "n_samples": 0,
            "mean_reads": None,
            "median_reads": None,
            "sd_reads": None,
            "cv_reads": None,
            "message_depth_balance": "No per-sample read counts were found; sequencing depth cannot be assessed.",
        }

    mean_reads = stats.mean(reads_list)
    median_reads = stats.median(reads_list)
    # Use population SD; for many samples it makes little difference
    sd_reads = stats.pstdev(reads_list) if n_samples > 1 else 0.0
    cv_reads = sd_reads / mean_reads if mean_reads > 0 else None

    # Interpret CV to decide if depth is “leveled”
    # (simple heuristic: <0.1 very balanced, 0.1–0.3 moderate, >0.3 uneven)
    if cv_reads is None:
        message = "Sequencing depth could not be evaluated due to missing values."
    else:
        if cv_reads < 0.10:
            message = (
                f"Sequencing depth is well balanced across samples "
                f"(CV = {cv_reads:.3f})."
            )
        elif cv_reads < 0.30:
            message = (
                f"Sequencing depth shows moderate variation across samples "
                f"(CV = {cv_reads:.3f})."
            )
        else:
            message = (
                f"Sequencing depth is uneven across samples (CV = {cv_reads:.3f}); "
                "some samples have substantially higher or lower read counts than others."
            )

    return {
        "n_samples": n_samples,
        "mean_reads": mean_reads,
        "median_reads": median_reads,
        "sd_reads": sd_reads,
        "cv_reads": cv_reads,
        "message_depth_balance": message,
    }


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Distill ScreenM outputs (data.json + results.json) into a summary JSON.\n"
            "Includes: screening threshold coverage and sequencing depth statistics."
        )
    )
    ap.add_argument(
        "--data-json",
        required=True,
        help="Path to data.json (global counts with above/below structure).",
    )
    ap.add_argument(
        "--results-json",
        required=True,
        help="Path to results.json (per-sample merged results).",
    )
    ap.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output distilled summary JSON.",
    )
    args = ap.parse_args()

    data_path = Path(args.data_json)
    results_path = Path(args.results_json)

    data_json = load_json(data_path)
    results_json = load_json(results_path)

    screening_threshold = compute_screening_threshold(data_json)
    sequencing_depth = compute_sequencing_depth(results_json)

    distilled: Dict[str, Any] = {
        "meta": {
            "n_samples_in_results": int(results_json.get("n_samples", 0)),
            "source_files": {
                "data_json": str(data_path),
                "results_json": str(results_path),
            },
        },
        "summary": {
            "screening_threshold": screening_threshold,
            "sequencing_depth": sequencing_depth,
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(distilled, f, indent=2)

    print(f"[✓] Wrote distilled summary → {out_path}")


if __name__ == "__main__":
    main()
