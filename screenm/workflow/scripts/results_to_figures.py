#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Input JSON not found: {path}")
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"JSON in {path} is not an object/dict.")
    return data


# ---------- 1) Helpers to extract per-sample basics ----------

def _get_total_reads(sample_data: Dict[str, Any]) -> Optional[float]:
    count_block = sample_data.get("count", {}) or {}
    total_reads = count_block.get("reads", count_block.get("total_reads"))
    if isinstance(total_reads, (int, float)):
        return float(total_reads)
    return None


def _estimate_low_quality_reads(sample_data: Dict[str, Any],
                                total_reads: Optional[float]) -> (Optional[float], Optional[float]):
    """
    Estimate low-quality reads from fastp, scaled to the full library.

    Returns (removed_fraction, low_quality_est).
    """
    fastp = sample_data.get("fastp", {}) or {}
    fastp_total = fastp.get("total_reads")

    if not isinstance(fastp_total, (int, float)) or fastp_total <= 0:
        return None, None

    low_q = fastp.get("low_quality_reads", 0) or 0
    too_n = fastp.get("too_many_N_reads", 0) or 0
    low_complex = fastp.get("low_complexity_reads", 0) or 0
    too_short = fastp.get("too_short_reads", 0) or 0
    too_long = fastp.get("too_long_reads", 0) or 0

    removed = low_q + too_n + low_complex + too_short + too_long
    removed = max(0, min(removed, fastp_total))  # clamp

    removed_fraction = removed / float(fastp_total)
    low_quality_est = (
        removed_fraction * total_reads if total_reads is not None else None
    )
    return removed_fraction, low_quality_est


def _get_singlem_prok_fraction(sample_data: Dict[str, Any]) -> Optional[float]:
    """
    Returns prokaryotic read fraction as a proportion (0–1), if available.
    """
    singlem = sample_data.get("singlem", {}) or {}
    read_fraction = singlem.get("read_fraction")  # interpreted as %
    if isinstance(read_fraction, (int, float)):
        return float(read_fraction) / 100.0
    return None


def _get_nonpareil_targets_95(sample_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extract LR_reads for the 95% Nonpareil target for reads and markers.

    Returns a dict:
      {
        "target_reads_95_LR_reads": float or None,
        "target_markers_95_LR_reads": float or None
      }
    """
    # Reads-based Nonpareil
    npr_reads = sample_data.get("nonpareil_reads", {}) or {}
    t_reads: Optional[float] = None
    targets_r = npr_reads.get("targets") or {}
    if isinstance(targets_r, dict):
        t95 = targets_r.get("95") or {}
        if isinstance(t95, dict):
            lr = t95.get("LR_reads")
            if isinstance(lr, (int, float)):
                t_reads = float(lr)

    # Marker-based Nonpareil
    npr_markers = sample_data.get("nonpareil_markers", {}) or {}
    t_markers: Optional[float] = None
    targets_m = npr_markers.get("targets") or {}
    if isinstance(targets_m, dict):
        t95m = targets_m.get("95") or {}
        if isinstance(t95m, dict):
            lr = t95m.get("LR_reads")
            if isinstance(lr, (int, float)):
                t_markers = float(lr)

    return {
        "target_reads_95_LR_reads": t_reads,
        "target_markers_95_LR_reads": t_markers,
    }


def _get_nonpareil_redundancy(sample_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extract redundancy and coverage (kappa_total, C_total) for reads and markers.
    """
    npr_reads = sample_data.get("nonpareil_reads", {}) or {}
    npr_markers = sample_data.get("nonpareil_markers", {}) or {}

    kappa_reads = npr_reads.get("kappa_total")
    C_reads = npr_reads.get("C_total")
    kappa_markers = npr_markers.get("kappa_total")
    C_markers = npr_markers.get("C_total")

    def _to_float(x):
        return float(x) if isinstance(x, (int, float)) else None

    return {
        "kappa_reads": _to_float(kappa_reads),
        "coverage_reads": _to_float(C_reads),
        "kappa_markers": _to_float(kappa_markers),
        "coverage_markers": _to_float(C_markers),
    }


# ---------- 2) Figure data: DNA depth fractions (stacked bar) ----------

def compute_depth_components_per_sample(results_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare per-sample components for a stacked bar plot of sequencing depth.

    For each sample, we estimate:
      - total_reads: from count.reads or count.total_reads (full library)
      - low_quality_reads_est: scaled from fastp subset (removed fraction * total_reads)
      - qc_pass_reads_est: total_reads - low_quality_reads_est
      - prokaryotic_reads_est: qc_pass_reads_est * (SingleM read_fraction / 100)
      - non_prokaryotic_reads_est: qc_pass_reads_est - prokaryotic_reads_est

    We also include the corresponding fractions w.r.t. total_reads, and for each
    sample the Nonpareil LR_reads target at 95% (reads and markers) that can
    be plotted as dashed lines in the figure.
    """
    samples = results_json.get("samples", {}) or {}
    per_sample: List[Dict[str, Any]] = []

    for sample_name, sample_data in samples.items():
        total_reads = _get_total_reads(sample_data)

        removed_fraction, low_quality_est = _estimate_low_quality_reads(
            sample_data, total_reads
        )

        # QC-passing reads
        if total_reads is None:
            qc_pass_est = None
        else:
            qc_pass_est = total_reads - (low_quality_est or 0.0)

        # Prokaryotic vs non-prokaryotic (from SingleM)
        prok_frac = _get_singlem_prok_fraction(sample_data)
        if qc_pass_est is None or prok_frac is None:
            prok_reads_est = None
        else:
            prok_reads_est = qc_pass_est * prok_frac

        if qc_pass_est is None or prok_reads_est is None:
            non_prok_reads_est = None
        else:
            non_prok_reads_est = qc_pass_est - prok_reads_est

        # Fractions relative to total
        if total_reads and total_reads > 0:
            frac_lowq = (low_quality_est or 0.0) / total_reads
            frac_prok = (prok_reads_est or 0.0) / total_reads
            frac_non_prok = (non_prok_reads_est or 0.0) / total_reads
        else:
            frac_lowq = None
            frac_prok = None
            frac_non_prok = None

        targets_95 = _get_nonpareil_targets_95(sample_data)

        per_sample.append(
            {
                "sample": sample_name,
                "total_reads": total_reads,
                "low_quality_reads_est": low_quality_est,
                "qc_pass_reads_est": qc_pass_est,
                "prokaryotic_reads_est": prok_reads_est,
                "non_prokaryotic_reads_est": non_prok_reads_est,
                "removed_fraction_fastp": removed_fraction,
                "singlem_read_fraction": (
                    sample_data.get("singlem", {})
                    .get("read_fraction", None)
                ),
                "fraction_low_quality_of_total": frac_lowq,
                "fraction_prokaryotic_of_total": frac_prok,
                "fraction_non_prokaryotic_of_total": frac_non_prok,
                # 95% Nonpareil targets (reads and markers)
                "target_reads_95_LR_reads": targets_95["target_reads_95_LR_reads"],
                "target_markers_95_LR_reads": targets_95["target_markers_95_LR_reads"],
            }
        )

    # Stable sort by sample for nicer plotting
    per_sample.sort(key=lambda x: x["sample"])
    return per_sample


# ---------- 3) Figure data: redundancy biplot ----------

def compute_redundancy_biplot_per_sample(results_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare per-sample values for a biplot of Nonpareil-based redundancy:

      - x-axis: read-based redundancy (kappa_total from nonpareil_reads)
      - y-axis: marker-based redundancy (kappa_total from nonpareil_markers)

    Also includes coverage (C_total) and the 95% LR_reads targets so the
    plotting layer can optionally encode them (colour/size/lines, etc.).
    """
    samples = results_json.get("samples", {}) or {}
    per_sample: List[Dict[str, Any]] = []

    for sample_name, sample_data in samples.items():
        red = _get_nonpareil_redundancy(sample_data)
        targets_95 = _get_nonpareil_targets_95(sample_data)

        entry = {
            "sample": sample_name,
            "kappa_reads": red["kappa_reads"],
            "coverage_reads": red["coverage_reads"],
            "kappa_markers": red["kappa_markers"],
            "coverage_markers": red["coverage_markers"],
            "target_reads_95_LR_reads": targets_95["target_reads_95_LR_reads"],
            "target_markers_95_LR_reads": targets_95["target_markers_95_LR_reads"],
        }
        per_sample.append(entry)

    per_sample.sort(key=lambda x: x["sample"])
    return per_sample


# ---------- 4) Build figures.json structure ----------

def build_figures_json(
    data_json: Dict[str, Any],
    results_json: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the final figures.json structure from data.json and results.json.

    Includes:
      - figures.dna_depth_fractions: stacked bar-friendly decomposition
        of read depth by low-quality, prokaryotic, and other, plus 95%
        Nonpareil target depths.

      - figures.redundancy_biplot: per-sample read vs marker redundancy
        (kappa_total) and coverage, suitable for a 2D scatter/biplot.
    """
    depth_components = compute_depth_components_per_sample(results_json)
    redundancy_biplot = compute_redundancy_biplot_per_sample(results_json)

    samples_from_results = results_json.get("samples", {}) or {}
    n_samples_results = int(results_json.get("n_samples", len(samples_from_results)))

    above = data_json.get("above", {}) or {}
    below = data_json.get("below", {}) or {}

    meta = {
        "min_reads": data_json.get("min_reads"),
        "n_samples_results": n_samples_results,
        "n_samples_in_data_above_threshold": len(above),
        "n_samples_in_data_below_threshold": len(below),
    }

    figures = {
        "meta": meta,
        "figures": {
            "dna_depth_fractions": {
                "description": (
                    "Per-sample sequencing depth decomposed into estimated low-quality reads, "
                    "prokaryotic reads (based on SingleM read_fraction applied to QC-passing reads), "
                    "and other reads. Also includes Nonpareil 95% LR_reads targets for reads and "
                    "marker genes, which can be plotted as dashed lines."
                ),
                "unit": "reads",
                "per_sample": depth_components,
            },
            "redundancy_biplot": {
                "description": (
                    "Per-sample Nonpareil-based redundancy for reads and marker genes. "
                    "Each point represents a sample, with read-based kappa_total on one axis and "
                    "marker-based kappa_total on the other. Coverage (C_total) and 95% LR_reads "
                    "targets are provided for additional visual encodings."
                ),
                "per_sample": redundancy_biplot,
            },
        },
    }

    return figures


# ---------- 5) Main CLI ----------

def main():
    ap = argparse.ArgumentParser(
        description=(
            "Create figures.json from ScreenM outputs (data.json + results.json) "
            "for downstream MultiQC-like HTML reports."
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
        help="Output figures JSON (e.g. figures.json).",
    )
    args = ap.parse_args()

    data_path = Path(args.data_json)
    results_path = Path(args.results_json)

    data_json = load_json(data_path)
    results_json = load_json(results_path)

    figures_json = build_figures_json(data_json, results_json)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(figures_json, f, indent=2)


if __name__ == "__main__":
    main()
