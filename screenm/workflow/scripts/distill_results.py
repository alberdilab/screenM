#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Input JSON not found: {path}")
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"JSON in {path} is not an object/dict.")
    return data


def compute_threshold_summary(data_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take the global counts JSON of the form:
      {
        "min_reads": N,
        "above": { ... },
        "below": { ... }
      }
    and compute:
      - n_total
      - n_above
      - percent_above
      - flag (1/2/3)
      - message
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


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Distill global ScreenM results (data.json + results.json) into a summary JSON.\n"
            "Currently computes read-threshold coverage (above/below) and a diagnostic flag."
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

    # --- threshold summary from data.json ---
    threshold_summary = compute_threshold_summary(data_json)

    # (Optional) basic sanity check:
    # samples_in_results = set((results_json.get("samples") or {}).keys())
    # samples_above = set((data_json.get("above") or {}).keys())
    # You could check they match if you like, but we just keep it simple for now.

    distilled: Dict[str, Any] = {
        "summary": threshold_summary,
        "meta": {
            "n_samples_in_results": int(results_json.get("n_samples", 0)),
            "source_files": {
                "data_json": str(data_path),
                "results_json": str(results_path),
            },
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(distilled, f, indent=2)

    print(f"[✓] Wrote distilled summary → {out_path}")


if __name__ == "__main__":
    main()
