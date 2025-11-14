#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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
                "If you want to include more samples for the estimations consider lowering "
                "the read threshold using the -r flag; but note that this will make the estimations less accurate."
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
    samples[*].count.reads (or total_reads).
    """
    samples = results_json.get("samples", {}) or {}

    reads_list: List[int] = []
    for name, sample_data in samples.items():
        count_block = sample_data.get("count", {}) or {}
        reads = count_block.get("reads", count_block.get("total_reads"))
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
                f"Sequencing depth is well balanced across samples (CV = {cv_reads:.3f}), "
                f"so average estimates should be applicable to most samples."
            )
        elif cv_reads < 0.30:
            flag = 2
            message = (
                f"Sequencing depth shows moderate variation across samples (CV = {cv_reads:.3f}),"
                f"so average estimates may not fully reflect all samples."
            )
        else:
            flag = 3
            message = (
                f"Sequencing depth is uneven across samples (CV = {cv_reads:.3f}), "
                "so average estimates may be misleading for some libraries."
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

    # Heuristic: <=10% very good, 10–30% moderate, >30% problematic.
    if mean_frac <= 0.10:
        flag = 1
        message = (
            f"On average {mean_frac*100:.1f}% of reads are removed by quality filtering, "
            "indicating generally high read quality. Sequencing quality is not likely to "
            "be a limiting factor for downstream analyses."
        )
    elif mean_frac <= 0.30:
        flag = 2
        message = (
            f"On average {mean_frac*100:.1f}% of reads are removed by quality filtering. "
            "Some libraries may have noticeable quality issues, so the effective sequencing "
            "depth could be lower than expected for those samples."
        )
    else:
        flag = 3
        message = (
            f"On average {mean_frac*100:.1f}% of reads are removed by quality filtering. "
            "A substantial fraction of sequencing effort is lost to low quality, Ns, or "
            "length/complexity filters. These results suggest issues during library preparation or "
            "sequencing, leading to compromised data quality. Consider revisiting library preparation"
            "and sequencing protocols. Treat downstream analyses with caution, as results may be affected "
            "by the low-quality data."
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


# ---------- 4) Prokaryotic fraction (SingleM read_fraction) ----------

def compute_prokaryotic_fraction(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise the prokaryotic fraction (read_fraction) from SingleM-based results.

    - Classification for mean prokaryotic fraction (interpreted as %):
        > 90%   → flag = 1
        > 50%   → flag = 2
        <= 50%  → flag = 3
    """
    samples = results_json.get("samples", {}) or {}

    fractions: List[float] = []
    warnings_count = 0

    for name, sample_data in samples.items():
        singlem = sample_data.get("singlem", {}) or {}
        frac = singlem.get("read_fraction")
        warn = singlem.get("warning")

        if isinstance(frac, (int, float)):
            fractions.append(float(frac))

        if warn not in (None, "", "null"):
            warnings_count += 1

    n_samples = len(fractions)

    if n_samples == 0:
        return {
            "n_samples": 0,
            "mean_prokaryotic_fraction": None,
            "median_prokaryotic_fraction": None,
            "sd_prokaryotic_fraction": None,
            "cv_prokaryotic_fraction": None,
            "n_warnings": None,
            "flag_prokaryotic_fraction": 3,
            "message_prokaryotic_fraction": (
                "No usable prokaryotic fraction values were found; "
                "microbial composition cannot be assessed."
            ),
        }

    mean_frac = stats.mean(fractions)
    median_frac = stats.median(fractions)
    sd_frac = stats.pstdev(fractions) if n_samples > 1 else 0.0
    cv_frac = sd_frac / mean_frac if mean_frac > 0 else None

    if mean_frac > 90:
        flag_mean = 1
    elif mean_frac > 50:
        flag_mean = 2
    else:
        flag_mean = 3

    if cv_frac is None:
        var_msg = "Variation in prokaryotic fraction cannot be evaluated."
    else:
        if cv_frac < 0.10:
            var_msg = (
                f"Prokaryotic fraction is consistent across samples (CV = {cv_frac:.3f}), "
                "so average estimates should be representative of the dataset."
            )
        elif cv_frac < 0.30:
            var_msg = (
                f"Prokaryotic fraction shows moderate variation across samples (CV = {cv_frac:.3f}), "
                "so some samples may differ from the average estimate. Consider looking at individual sample values "
                "to assess whether any samples deviate significantly from the average patterns."
            )
        else:
            var_msg = (
                f"Prokaryotic fraction is highly variable across samples (CV = {cv_frac:.3f}), "
                "so average estimates may not reflect individual sample compositions. Have a look at the per-sample "
                "prokaryotic fractions to understand the variation in microbial content across your dataset."
            )

    warning_ratio = warnings_count / n_samples if n_samples > 0 else 0.0
    if warnings_count == 0:
        warn_msg = ""
    elif warning_ratio >= 0.5:
        warn_msg = (
            f"Many samples ({warnings_count}/{n_samples}) contain warnings in prokaryotic fraction estimation, "
            "indicating that the reliability of the estimated prokaryotic fractions is low across the dataset. "
            "If sequencing depth is high enough, consider increasing the number of reads used for estimation "
            "through the -r parameter to improve these estimates."
        )
    else:
        warn_msg = (
            f"Some samples ({warnings_count}/{n_samples}) contain warnings in prokaryotic fraction estimation, "
            "indicating that the reliability of the estimated prokaryotic fractions is low for some samples. "
            "Consider checking those samples individually."
        )

    message = (
        f"Mean prokaryotic fraction across {n_samples} samples is {mean_frac:.1f}%. "
        + var_msg + " "
        + warn_msg
    )

    return {
        "n_samples": n_samples,
        "mean_prokaryotic_fraction": mean_frac,
        "median_prokaryotic_fraction": median_frac,
        "sd_prokaryotic_fraction": sd_frac,
        "cv_prokaryotic_fraction": cv_frac,
        "n_warnings": warnings_count,
        "flag_prokaryotic_fraction": flag_mean,
        "message_prokaryotic_fraction": message,
    }


# ---------- 5) Helpers for LR_reads from Nonpareil targets ----------

def _pick_target_lr_reads(npr_block: Dict[str, Any]) -> Optional[Tuple[str, float]]:
    """
    From a nonpareil_* block, pick one LR_reads value from the 'targets' dict:

      "targets": {
        "95": { "LR_bp": ..., "LR_reads": ... },
        "99": { ... }
      }

    Strategy:
      - Find all numeric targets (e.g. "95", "99")
      - Use the one with the lowest target percentage (e.g. 95 before 99)
    Returns (target_str, lr_reads) or None if not found.
    """
    targets = npr_block.get("targets") or {}
    if not isinstance(targets, dict):
        return None

    candidates: List[Tuple[float, str, float]] = []
    for pct_str, info in targets.items():
        try:
            pct = float(pct_str)
        except (TypeError, ValueError):
            continue
        if not isinstance(info, dict):
            continue
        lr_val = info.get("LR_reads")
        if lr_val is None:
            continue

        if isinstance(lr_val, (int, float)):
            lr = float(lr_val)
        elif isinstance(lr_val, str):
            if lr_val.lower() == "inf":
                lr = float("inf")
            else:
                try:
                    lr = float(lr_val)
                except ValueError:
                    continue
        else:
            continue

        candidates.append((pct, pct_str, lr))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])  # smallest target first (e.g. 95)
    _, pct_str, lr = candidates[0]
    return pct_str, lr


# ---------- 6) Redundancy based on reads (Nonpareil on metagenome reads) ----------

def compute_redundancy_reads(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise redundancy using Nonpareil kappa_total and LR_reads from
    samples[*].nonpareil_reads.targets, compared to total sample reads.
    """
    samples = results_json.get("samples", {}) or {}

    kappas: List[float] = []
    lr_exceeds = 0
    n_with_lr = 0
    lr_target_used: Optional[str] = None

    for name, sample_data in samples.items():
        npr = sample_data.get("nonpareil_reads", {}) or {}
        if not npr:
            continue

        # kappa_total
        kappa = npr.get("kappa_total")
        if isinstance(kappa, str):
            try:
                kappa = float(kappa)
            except ValueError:
                kappa = None
        if isinstance(kappa, (int, float)):
            kappas.append(float(kappa))

        # LR_reads from targets
        lr_info = _pick_target_lr_reads(npr)
        if lr_info is not None:
            target_str, lr_reads = lr_info
            lr_target_used = lr_target_used or target_str

            count_block = sample_data.get("count", {}) or {}
            total_reads = count_block.get("reads", count_block.get("total_reads"))

            if isinstance(total_reads, str):
                try:
                    total_reads = float(total_reads)
                except ValueError:
                    total_reads = None

            if isinstance(total_reads, (int, float)) and total_reads > 0:
                n_with_lr += 1
                if (lr_reads != float("inf")) and (lr_reads > total_reads):
                    lr_exceeds += 1

    n_kappa = len(kappas)

    if n_kappa == 0:
        msg = (
            "No Nonpareil-based redundancy estimates (kappa_total) were found for reads; "
            "redundancy and LR-based effort cannot be assessed."
        )
        return {
            "n_samples_kappa": 0,
            "mean_kappa_total": None,
            "median_kappa_total": None,
            "sd_kappa_total": None,
            "cv_kappa_total": None,
            "flag_redundancy": 3,
            "n_samples_with_lr": n_with_lr,
            "n_samples_lr_exceeds_depth": lr_exceeds,
            "flag_LR_vs_depth": 3 if n_with_lr > 0 else None,
            "lr_target_used": lr_target_used,
            "message_redundancy": msg,
        }

    mean_k = stats.mean(kappas)
    median_k = stats.median(kappas)
    sd_k = stats.pstdev(kappas) if n_kappa > 1 else 0.0
    cv_k = sd_k / mean_k if mean_k > 0 else None

    if mean_k > 0.9:
        flag_redundancy = 1
    elif mean_k > 0.5:
        flag_redundancy = 2
    else:
        flag_redundancy = 3

    if mean_k is None:
        mean_k_msg = "Variation in redundancy cannot be evaluated."
    else:
        if mean_k > 0.9:
            mean_k_msg = c(
                f"Average estimated read redundancy is high ({mean_k:.3f}), "
                "indicating that the sequencing data captures most of the "
                "metagenomic diversity estimated in the samples."
            )
        elif mean_k > 0.5:
            mean_k_msg = (
                f"Average estimated read redundancy is moderate ({mean_k:.3f}), "
                "indicating that a significant portion of the metagenomic diversity is "
                "likely not to be captured by the sequencing data."
                ""
            )
        else:
            mean_k_msg = (
                f"Average estimated read redundancy is low ({mean_k:.3f}), "
                "indicating that a significant portion of the metagenomic diversity "
                "remains unsampled. Consider increasing sequencing depth to better "
                "capture the diversity. "
            )


    if cv_k is None:
        var_msg = "Variation in redundancy cannot be evaluated."
    else:
        if cv_k < 0.10:
            var_msg = (
                f"Read redundancy is consistent across samples (CV = {cv_k:.3f}), "
                "indicating that average estimates should be applicable to most samples."
            )
        elif cv_k < 0.30:
            var_msg = (
                f"Marker redundancy shows moderate variation across samples (CV = {cv_k:.3f}), "
                "indicating that average estimates may not fully reflect all samples. "
                "Consider looking at individual sample redundancy estimates to assess the variation."
            )
        else:
            var_msg = (
                f"Marker redundancy is highly variable across samples (CV = {cv_k:.3f}), "
                "indicating that average estimates may be misleading for some libraries. "
                "Look at individual sample redundancy estimates to assess the variation."
            )

    if n_with_lr == 0:
        flag_lr = None
        lr_msg = (
            "No LR_reads targets were available from Nonpareil (reads); "
            "cannot compare required sequencing effort to observed depth."
        )
    else:
        frac_exceeds = lr_exceeds / n_with_lr
        if lr_exceeds == 0:
            flag_lr = 1
            lr_msg = (
                f"For all {n_with_lr} samples, the sequencing depth estimated to be needed to capture {lr_target_used}% "
                "of the metagenomic diversity is below the conducted sequencing depth, "
                "indicating sufficient sequencing effort."
            )
        elif frac_exceeds < 0.5:
            flag_lr = 2
            lr_msg = (
                f"In {lr_exceeds}/{n_with_lr} samples, the sequencing depth estimated to be needed to capture {lr_target_used}% "
                "of the metagenomic diversity is above the conducted sequencing depth, indicating that these samples "
                "may not be able to represent the complexity of the samples adequately."
            )
        else:
            flag_lr = 3
            lr_msg = (
                f"In most ({lr_exceeds}/{n_with_lr}) samples, the sequencing depth estimated to be needed to capture {lr_target_used}% "
                "of the metagenomic diversity is above the conducted sequencing depth, indicating that a substantial fraction of "
                "the dataset will likely be unable to represent the complexity of the samples adequately. "
            )

    message = (
        mean_k_msg + " "
        + var_msg + " "
        + lr_msg
    )

    return {
        "n_samples_kappa": n_kappa,
        "mean_kappa_total": mean_k,
        "median_kappa_total": median_k,
        "sd_kappa_total": sd_k,
        "cv_kappa_total": cv_k,
        "flag_redundancy": flag_redundancy,
        "n_samples_with_lr": n_with_lr,
        "n_samples_lr_exceeds_depth": lr_exceeds,
        "flag_LR_vs_depth": flag_lr,
        "lr_target_used": lr_target_used,
        "message_redundancy": message,
    }


# ---------- 7) Redundancy based on marker genes (Nonpareil on markers) ----------

def compute_redundancy_markers(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise redundancy using Nonpareil kappa_total and LR_reads from
    samples[*].nonpareil_markers.targets, compared to marker read depth
    recorded in the same block (total_reads or subset_reads).
    """
    samples = results_json.get("samples", {}) or {}

    kappas: List[float] = []
    lr_exceeds = 0
    n_with_lr = 0
    lr_target_used: Optional[str] = None

    for name, sample_data in samples.items():
        npr = sample_data.get("nonpareil_markers", {}) or {}
        if not npr:
            continue

        # kappa_total for markers
        kappa = npr.get("kappa_total")
        if isinstance(kappa, str):
            try:
                kappa = float(kappa)
            except ValueError:
                kappa = None
        if isinstance(kappa, (int, float)):
            kappas.append(float(kappa))

        # LR_reads from targets
        lr_info = _pick_target_lr_reads(npr)
        if lr_info is not None:
            target_str, lr_reads = lr_info
            lr_target_used = lr_target_used or target_str

            # Marker read depth: prefer total_reads, then subset_reads
            depth = npr.get("total_reads", npr.get("subset_reads"))

            if isinstance(depth, str):
                try:
                    depth = float(depth)
                except ValueError:
                    depth = None

            if isinstance(depth, (int, float)) and depth > 0:
                n_with_lr += 1
                if (lr_reads != float("inf")) and (lr_reads > depth):
                    lr_exceeds += 1

    n_kappa = len(kappas)

    if n_kappa == 0:
        msg = (
            "No Nonpareil-based redundancy estimates (kappa_total) were found for marker genes; "
            "marker redundancy and LR-based effort cannot be assessed."
        )
        return {
            "n_samples_kappa": 0,
            "mean_kappa_total": None,
            "median_kappa_total": None,
            "sd_kappa_total": None,
            "cv_kappa_total": None,
            "flag_redundancy_markers": 3,
            "n_samples_with_lr": n_with_lr,
            "n_samples_lr_exceeds_depth": lr_exceeds,
            "flag_LR_vs_depth_markers": 3 if n_with_lr > 0 else None,
            "lr_target_used": lr_target_used,
            "message_redundancy_markers": msg,
        }

    mean_k = stats.mean(kappas)
    median_k = stats.median(kappas)
    sd_k = stats.pstdev(kappas) if n_kappa > 1 else 0.0
    cv_k = sd_k / mean_k if mean_k > 0 else None

    if mean_k > 0.9:
        flag_redundancy = 1
    elif mean_k > 0.5:
        flag_redundancy = 2
    else:
        flag_redundancy = 3

    if mean_k is None:
        mean_k_msg = "Variation in redundancy cannot be evaluated."
    else:
        if mean_k > 0.9:
            mean_k_msg = c(
                f"Average estimated marker redundancy is high ({mean_k:.3f}), "
                "indicating that the sequencing data captures most of the "
                "microbial diversity estimated in the samples."
            )
        elif mean_k > 0.5:
            mean_k_msg = (
                f"Average estimated marker redundancy is moderate ({mean_k:.3f}), "
                "indicating that a significant portion of the microbial diversity is "
                "likely not to be captured by the sequencing data."
                ""
            )
        else:
            mean_k_msg = (
                f"Average estimated marker redundancy is low ({mean_k:.3f}), "
                "indicating that a significant portion of the microbial diversity "
                "remains unsampled. Consider increasing sequencing depth to better "
                "capture the microbial community. "
            )

    if cv_k is None:
        var_msg = "Variation in marker redundancy cannot be evaluated."
    else:
        if cv_k < 0.10:
            var_msg = (
                f"Marker redundancy is consistent across samples (CV = {cv_k:.3f}), "
                "indicating that average estimates should be applicable to most samples."
            )
        elif cv_k < 0.30:
            var_msg = (
                f"Marker redundancy shows moderate variation across samples (CV = {cv_k:.3f}), "
                "indicating that average estimates may not fully reflect all samples. "
                "Consider looking at individual sample redundancy estimates to assess the variation."
            )
        else:
            var_msg = (
                f"Marker redundancy is highly variable across samples (CV = {cv_k:.3f}), "
                "indicating that average estimates may be misleading for some libraries. "
                "Look at individual sample redundancy estimates to assess the variation."
            )

    if n_with_lr == 0:
        flag_lr = None
        lr_msg = (
            "No LR_reads targets were available from Nonpareil (markers); "
            "cannot compare required marker sequencing effort to observed marker depth."
        )
    else:
        frac_exceeds = lr_exceeds / n_with_lr
        if lr_exceeds == 0:
            flag_lr = 1
            lr_msg = (
                f"For all {n_with_lr} samples, the sequencing depth estimated to be needed to capture {lr_target_used}% "
                "of the microbial diversity is below the conducted sequencing depth, "
                "indicating sufficient sequencing effort."
            )
        elif frac_exceeds < 0.5:
            flag_lr = 2
            lr_msg = (
                f"In {lr_exceeds}/{n_with_lr} samples, the sequencing depth estimated to be needed to capture {lr_target_used}% "
                "of the microbial diversity is above the conducted sequencing depth, indicating that these samples "
                "may not be able to represent the complexity of the communities adequately."
            )
        else:
            flag_lr = 3
            lr_msg = (
                f"In most ({lr_exceeds}/{n_with_lr}) samples, the sequencing depth estimated to be needed to capture {lr_target_used}% "
                "of the microbial diversity is above the conducted sequencing depth, indicating that a substantial fraction of "
                "the dataset will likely be unable to represent the complexity of the communities adequately. "
            )

    message = (
        mean_k_msg + " "
        + var_msg + " "
        + lr_msg
    )

    return {
        "n_samples_kappa": n_kappa,
        "mean_kappa_total": mean_k,
        "median_kappa_total": median_k,
        "sd_kappa_total": sd_k,
        "cv_kappa_total": cv_k,
        "flag_redundancy_markers": flag_redundancy,
        "n_samples_with_lr": n_with_lr,
        "n_samples_lr_exceeds_depth": lr_exceeds,
        "flag_LR_vs_depth_markers": flag_lr,
        "lr_target_used": lr_target_used,
        "message_redundancy_markers": message,
    }


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser(
        description=(
            "Distill ScreenM outputs (data.json + results.json) into a summary JSON.\n"
            "Includes: screening threshold coverage, sequencing depth, low-quality reads, "
            "prokaryotic fraction, and redundancy based on reads and marker genes."
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
    prok_fraction = compute_prokaryotic_fraction(results_json)
    redundancy_reads = compute_redundancy_reads(results_json)
    redundancy_markers = compute_redundancy_markers(results_json)

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
            "prokaryotic_fraction": prok_fraction,
            "redundancy_reads": redundancy_reads,
            "redundancy_markers": redundancy_markers,
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(distilled, f, indent=2)

    print(f"[✓] Wrote distilled summary → {out_path}")


if __name__ == "__main__":
    main()
