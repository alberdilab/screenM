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


# ---------- 1) Screening threshold (above/below) ----------

def compute_screening_threshold(data_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    From data.json of the form:
      { "min_reads": N, "above": {...}, "below": {...} }
    compute counts, percentages and flag.
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


# ---------- 2) Sequencing depth ----------

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
            "flag_sequencing_depth": 3,
            "message_sequencing_depth": (
                "No per-sample read counts were found; sequencing depth cannot be assessed."
            ),
        }

    mean_reads = stats.mean(reads_list)
    median_reads = stats.median(reads_list)
    sd_reads = stats.pstdev(reads_list) if n_samples > 1 else 0.0
    cv_reads = sd_reads / mean_reads if mean_reads > 0 else None

    # Decide flag based on CV
    if cv_reads is None:
        flag = 3
        message = "Sequencing depth could not be evaluated due to missing values."
    else:
        if cv_reads < 0.10:
            flag = 1
            message = (
                f"Sequencing depth is well balanced across samples "
                f"(CV = {cv_reads:.3f})."
            )
        elif cv_reads < 0.30:
            flag = 2
            message = (
                f"Sequencing depth shows moderate variation across samples "
                f"(CV = {cv_reads:.3f})."
            )
        else:
            flag = 3
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
        "flag_sequencing_depth": flag,
        "message_sequencing_depth": message,
    }


# ---------- 3) Low-quality reads (fastp-based) ----------

def compute_low_quality(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise low-quality / discarded reads using samples[*].fastp.* fields.

    We aggregate:
      - total reads
      - total discarded reads (low_quality + too_many_N + low_complexity + too_short + too_long)
      - per-sample fraction of discarded reads
      - mean/median/sd of discarded fraction
      - flag + message
    """
    samples = results_json.get("samples", {}) or {}

    frac_removed_list: List[float] = []
    total_reads_all = 0
    total_removed_all = 0
    n_samples_with_fastp = 0

    for name, sample_data in samples.items():
        fastp = sample_data.get("fastp", {}) or {}
        total = fastp.get("total_reads")
        if not isinstance(total, (int, float)) or total <= 0:
            continue

        low_q = fastp.get("low_quality_reads", 0) or 0
        too_n = fastp.get("too_many_N_reads", 0) or 0
        low_complex = fastp.get("low_complexity_reads", 0) or 0
        too_short = fastp.get("too_short_reads", 0) or 0
        too_long = fastp.get("too_long_reads", 0) or 0

        removed = low_q + too_n + low_complex + too_short + too_long
        # Guard against pathological cases
        removed = max(0, min(removed, total))

        frac_removed = removed / total if total > 0 else 0.0

        frac_removed_list.append(frac_removed)
        total_reads_all += total
        total_removed_all += removed
        n_samples_with_fastp += 1

    if n_samples_with_fastp == 0:
        return {
            "n_samples": 0,
            "total_reads": None,
            "total_removed_reads": None,
            "percent_removed_reads_overall": None,
            "mean_fraction_removed": None,
            "median_fraction_removed": None,
            "sd_fraction_removed": None,
            "flag_low_quality": 3,
            "message_low_quality": (
                "No fastp-derived quality metrics were found; low-quality reads cannot be assessed."
            ),
        }

    mean_frac = stats.mean(frac_removed_list)
    median_frac = stats.median(frac_removed_list)
    sd_frac = stats.pstdev(frac_removed_list) if n_samples_with_fastp > 1 else 0.0
    percent_removed_overall = (
        100.0 * total_removed_all / total_reads_all if total_reads_all > 0 else 0.0
    )

    # Flag based on average fraction removed
    # Heuristic: <=10% very good, 10–30% moderate, >30% problematic.
    if mean_frac <= 0.10:
        flag = 1
        message = (
            f"On average {mean_frac*100:.1f}% of reads are removed by quality filtering, "
            "indicating generally high read quality."
        )
    elif mean_frac <= 0.30:
        flag = 2
        message = (
            f"On average {mean_frac*100:.1f}% of reads are removed by quality filtering. "
            "Some libraries may have noticeable quality issues."
        )
    else:
        flag = 3
        message = (
            f"On average {mean_frac*100:.1f}% of reads are removed by quality filtering. "
            "A substantial fraction of sequencing effort is lost to low quality, Ns, or "
            "length/complexity filters; consider revisiting library prep or sequencing depth."
        )

    return {
        "n_samples": n_samples_with_fastp,
        "total_reads": total_reads_all,
        "total_removed_reads": total_removed_all,
        "percent_removed_reads_overall": percent_removed_overall,
        "mean_fraction_removed": mean_frac,
        "median_fraction_removed": median_frac,
        "sd_fraction_removed": sd_frac,
        "flag_low_quality": flag,
        "message_low_quality": message,
    }


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser(
        description=(
            "Distill ScreenM outputs (data.json + results.json) into a summary JSON.\n"
            "Includes: screening threshold coverage, sequencing depth, and low-quality read metrics."
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
    low_quality = compute_low_quality(results_json)

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
            "low_quality_reads": low_quality,
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(distilled, f, indent=2)

    print(f"[✓] Wrote distilled summary → {out_path}")


if __name__ == "__main__":
    main()
