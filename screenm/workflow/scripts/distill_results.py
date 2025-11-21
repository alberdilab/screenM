#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import statistics as stats
import numpy as np

# ---------- Global thresholds (tune here) ----------

### Screening overview

# Screening threshold: fraction of samples above read cutoff
THRESH_PCT_ABOVE_ALL = 100.0  # "all samples above"
THRESH_PCT_ABOVE_GOOD = 80.0  # "most samples above"

# Coefficient of variation (CV) thresholds for "balanced / moderate / uneven"
THRESH_CV_BALANCED = 0.10
THRESH_CV_MODERATE = 0.30

### Sequencing quality

# Low-quality read fraction thresholds (fastp)
THRESH_LOWQ_GOOD = 0.05   # <= 5% removed → very good
THRESH_LOWQ_MODERATE = 0.20  # 5–20% → moderate, >20% → problematic
THRESH_FASTP_LOWQUAL_GOOD = 0.02  # <=2% low-quality reads → clean
THRESH_FASTP_LOWQUAL_MODERATE = 0.05
THRESH_FASTP_COMPLEXITY_GOOD = 0.02
THRESH_FASTP_COMPLEXITY_MODERATE = 0.05
THRESH_FASTP_ADAPTER_GOOD = 0.10  # <=10% adapter trimming → minimal
THRESH_FASTP_ADAPTER_MODERATE = 0.20
THRESH_FASTP_TOOSHORT_GOOD = 0.02
THRESH_FASTP_TOOSHORT_MODERATE = 0.05
THRESH_FASTP_DUPLICATION_GOOD = 0.05  # <=5% duplicates → low redundancy
THRESH_FASTP_DUPLICATION_MODERATE = 0.15

### Prokaryotic fraction

# Prokaryotic fraction (%)
THRESH_PROK_HIGH = 90.0
THRESH_PROK_MODERATE = 50.0

### Metagenomic coverage of samples

# Fractions used for "many" warnings or LR_exceeds
THRESH_WARNINGS_HIGH_FRACTION = 0.5
THRESH_LR_EXCEEDS_FRACTION = 0.5

# Coverage ratio thresholds (relative to target) for medians and sample fractions
THRESH_COV_MEDIAN_GOOD = 1.0   # >=100% of target
THRESH_COV_MEDIAN_MODERATE = 0.8
THRESH_COV_SAMPLES_GOOD = 1.0  # 100% of samples meet target
THRESH_COV_SAMPLES_MODERATE = 0.8  # >=80% of samples meet target

# Mash clustering – separation ratio (between / within)
THRESH_CLUSTER_RATIO_GOOD = 1.20
THRESH_CLUSTER_RATIO_MODERATE = 1.05

# Mash clustering – absolute within-cluster Mash distances
# reference value = worst (max) mean distance across clusters, or global mean_within_distance
THRESH_CLUSTER_WITHIN_MILD = 0.05   # >0.05 → mild warning
THRESH_CLUSTER_WITHIN_STRONG = 0.15  # >0.15 → strong warning

# Mash clustering – imbalance in cluster sizes
THRESH_CLUSTER_SIZE_UNBALANCED_FACTOR = 2.0  # largest >= 2× mean size → unbalanced


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
        if percent_above == THRESH_PCT_ABOVE_ALL:
            flag = 1
            message = (
                f"All samples ({n_above}/{n_total}, {percent_above:.1f}%) are above the "
                f"read threshold ({min_reads} reads). If you want higher accuracy of the estimations, "
                f"you might consider increasing the read threshold using the -r flag, although this "
                f"will require longer computation times."
            )
        elif percent_above >= THRESH_PCT_ABOVE_GOOD:
            flag = 2
            message = (
                f"Most samples ({n_above}/{n_total}, {percent_above:.1f}%) are above the "
                f"read threshold ({min_reads} reads), but some are below. "
                "If you want to include more samples for the estimations consider lowering "
                "the read threshold using the -r flag; but note that this will make the estimations less accurate."
            )
        else:
            flag = 3
            message = (
                f"Only {n_above}/{n_total} samples ({percent_above:.1f}%) are above the "
                f"read threshold ({min_reads} reads). "
                f"As less than {THRESH_PCT_ABOVE_GOOD:.0f}% of the samples are above the number of reads used for "
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
        if cv_reads < THRESH_CV_BALANCED:
            flag = 1
            message = (
                f"Sequencing depth is well balanced across samples (CV = {cv_reads:.3f}), "
                f"so average estimates should be applicable to most samples."
            )
        elif cv_reads < THRESH_CV_MODERATE:
            flag = 2
            message = (
                f"Sequencing depth shows moderate variation across samples (CV = {cv_reads:.3f}), "
                f"so average estimates may not fully reflect all samples. Consider looking at individual sample values "
                f"to assess whether any samples deviate significantly from the average patterns."
            )
        else:
            flag = 3
            message = (
                f"Sequencing depth is uneven across samples (CV = {cv_reads:.3f}), "
                f"so average estimates may be misleading for some libraries. Look at individual sample values "
                f"to identify the samples that deviate significantly from the average patterns."
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


# ---------- 2b) Combined screening overview ----------

def compute_screening_overview(
    data_json: Dict[str, Any],
    results_json: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Combined view of:
      - fraction of samples above the screening read threshold, and
      - sequencing depth balance across samples.

    The returned section is called 'screening_overview' and contains
    the key metrics from both aspects plus a combined flag/message.

    Combined flag:
      - based on the "worst" (max) of flag_reads_threshold and flag_sequencing_variation
        whenever both are available,
      - falls back gracefully when one of them cannot be evaluated.
    """
    st = compute_screening_threshold(data_json)
    sd = compute_sequencing_depth(results_json)

    reads_flag = st.get("flag_reads_threshold", 3)
    depth_flag = sd.get("flag_sequencing_depth", 3)

    # Combined flag logic
    if sd.get("n_samples", 0) == 0 and st.get("n_samples_total", 0) == 0:
        combined_flag = 3
    elif sd.get("n_samples", 0) == 0:
        combined_flag = reads_flag
    elif st.get("n_samples_total", 0) == 0:
        combined_flag = depth_flag
    else:
        combined_flag = max(reads_flag, depth_flag)
        if {reads_flag, depth_flag} == {1, 3}:
            # Excellent screening fraction but uneven depth → treat as moderate overall.
            combined_flag = 2

    # Combined message
    def _variation_transition(depth_flag: Optional[int], variation_flag: Optional[int]) -> str:
        """Pick a linker word to keep the tone natural."""
        if depth_flag is None or variation_flag is None:
            return ""
        if depth_flag == 1:
            return "Additionally" if variation_flag == 1 else "However"
        if depth_flag == 2:
            if variation_flag == 1:
                return "On the bright side"
            return "Additionally" if variation_flag == 2 else "However"
        if depth_flag == 3:
            if variation_flag == 1:
                return "Still"
            return "Still" if variation_flag == 2 else "Additionally"
        return ""

    def _apply_transition(transition: str, text: str) -> str:
        if not transition:
            return text.strip()
        stripped = text.strip()
        if not stripped:
            return stripped
        if stripped.lower().startswith(transition.lower()):
            return stripped
        lowered = stripped[0].lower() + stripped[1:] if len(stripped) > 1 else stripped.lower()
        return f"{transition}, {lowered}"

    msg_parts: List[str] = []
    reads_msg = st.get("message_reads_threshold")
    if reads_msg:
        msg_parts.append(reads_msg.strip())
    variation_msg = sd.get("message_sequencing_depth")
    if variation_msg:
        transition = _variation_transition(reads_flag, depth_flag)
        msg_parts.append(_apply_transition(transition, variation_msg))

    if sd.get("n_samples", 0) == 0:
        msg_parts.append(
            "Sequencing depth statistics could not be computed because per-sample read counts are missing."
        )
    if st.get("n_samples_total", 0) == 0:
        msg_parts.append(
            "Read screening could not be evaluated because the number of samples in data.json is zero."
        )

    combined_message = " ".join(m for m in msg_parts if m)

    return {
        # Screening threshold side
        "reads_threshold": st.get("reads_threshold"),
        "n_samples_total": st.get("n_samples_total"),
        "n_samples_above_threshold": st.get("n_samples_above_threshold"),
        "percent_above_threshold": st.get("percent_above_threshold"),
        "flag_reads_threshold": reads_flag,

        # Sequencing depth side
        "n_samples_depth": sd.get("n_samples"),
        "mean_reads": sd.get("mean_reads"),
        "median_reads": sd.get("median_reads"),
        "sd_reads": sd.get("sd_reads"),
        "cv_reads": sd.get("cv_reads"),
        "flag_sequencing_depth": reads_flag,
        "flag_sequencing_variation": depth_flag,

        # Combined
        "flag_screening_overview": combined_flag,
        "message_screening_overview": combined_message,
    }


def compute_total_reads_all(results_json: Dict[str, Any]) -> Optional[float]:
    """
    Sum total reads across all samples using count.reads (or count.total_reads).
    Returns None if no numeric counts are found.
    """
    samples = results_json.get("samples", {}) or {}
    total_reads_all = 0.0
    found = False

    for sample_data in samples.values():
        count_block = sample_data.get("count", {}) or {}
        reads = count_block.get("reads", count_block.get("total_reads"))
        if isinstance(reads, str):
            try:
                reads = float(reads)
            except ValueError:
                reads = None
        if isinstance(reads, (int, float)) and reads >= 0:
            total_reads_all += float(reads)
            found = True

    return total_reads_all if found else None


# ---------- 3) Low-quality reads (fastp-based) ----------

def compute_low_quality(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise low-quality / discarded reads using samples[*].fastp.* fields.
    """
    samples = results_json.get("samples", {}) or {}

    frac_removed_list: List[float] = []
    low_quality_frac_list: List[float] = []
    low_complex_frac_list: List[float] = []
    too_short_frac_list: List[float] = []
    adapter_frac_list: List[float] = []
    duplication_rates: List[float] = []
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
        adapter_trimmed = fastp.get("adapter_trimmed_reads", 0) or 0
        duplication = fastp.get("duplication")
        if isinstance(duplication, str):
            try:
                duplication = float(duplication)
            except ValueError:
                duplication = None

        removed = low_q + too_n + low_complex + too_short
        removed = max(0, min(removed, total))

        frac_removed = removed / total if total > 0 else 0.0
        low_quality_frac = low_q / total if total > 0 else 0.0
        low_complex_frac = low_complex / total if total > 0 else 0.0
        too_short_frac = too_short / total if total > 0 else 0.0
        adapter_frac = adapter_trimmed / total if total > 0 else 0.0

        frac_removed_list.append(frac_removed)
        low_quality_frac_list.append(low_quality_frac)
        low_complex_frac_list.append(low_complex_frac)
        too_short_frac_list.append(too_short_frac)
        adapter_frac_list.append(adapter_frac)
        if isinstance(duplication, (int, float)) and duplication >= 0:
            duplication_rates.append(float(duplication))
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
            "sd_fraction_removed": None,
            "mean_fraction_low_quality": None,
            "mean_fraction_low_complexity": None,
            "mean_fraction_too_short": None,
            "mean_fraction_adapter_trimmed": None,
            "mean_duplication_rate": None,
            "flag_sequencing_quality": 3,
            "flag_phred_score": 3,
            "flag_complexity": 3,
            "flag_too_short": 3,
            "flag_adapter_trimming": 3,
            "flag_duplication": 3,
            "message_low_quality": (
                "No fastp-derived quality metrics were found; low-quality reads cannot be assessed."
            ),
        }

    mean_frac = stats.mean(frac_removed_list)
    sd_frac = stats.pstdev(frac_removed_list) if n_samples_with_fastp > 1 else 0.0
    mean_low_q = stats.mean(low_quality_frac_list)
    mean_low_complex = stats.mean(low_complex_frac_list)
    mean_too_short = stats.mean(too_short_frac_list)
    mean_adapter = stats.mean(adapter_frac_list)
    mean_dup = stats.mean(duplication_rates) if duplication_rates else None
    percent_removed_overall = (
        100.0 * total_removed_all / total_reads_all if total_reads_all > 0 else 0.0
    )

    # Heuristic: <= THRESH_LOWQ_GOOD very good,
    # THRESH_LOWQ_GOOD–THRESH_LOWQ_MODERATE moderate, >THRESH_LOWQ_MODERATE problematic.
    if mean_frac <= THRESH_LOWQ_GOOD:
        flag = 1
        message = (
            f"On average {mean_frac*100:.1f}% of reads are flagged as low-quality, "
            "indicating generally high sequencing performance. Sequencing quality is therefore not likely to "
            "be a limiting factor for downstream analyses."
        )
    elif mean_frac <= THRESH_LOWQ_MODERATE:
        flag = 2
        message = (
            f"On average {mean_frac*100:.1f}% of reads are flagged as low-quality. "
            "Some libraries may have noticeable quality issues, so the effective sequencing "
            "depth could be lower than expected for those samples."
        )
    else:
        flag = 3
        message = (
            f"On average {mean_frac*100:.1f}% of reads are flagged as low-quality. "
            "A substantial fraction of sequencing effort is lost to low quality, Ns, or "
            "length/complexity filters. These results suggest issues during library preparation or "
            "sequencing, leading to compromised data quality. Consider revisiting library preparation"
            "and sequencing protocols. Treat downstream analyses with caution, as results may be affected "
            "by the low-quality data."
        )

    def _flag_from_thresholds(value: Optional[float], good: float, moderate: float) -> int:
        if value is None:
            return 3
        if value <= good:
            return 1
        if value <= moderate:
            return 2
        return 3

    flag_phred = _flag_from_thresholds(
        mean_low_q, THRESH_FASTP_LOWQUAL_GOOD, THRESH_FASTP_LOWQUAL_MODERATE
    )
    flag_complexity = _flag_from_thresholds(
        mean_low_complex, THRESH_FASTP_COMPLEXITY_GOOD, THRESH_FASTP_COMPLEXITY_MODERATE
    )
    flag_too_short = _flag_from_thresholds(
        mean_too_short, THRESH_FASTP_TOOSHORT_GOOD, THRESH_FASTP_TOOSHORT_MODERATE
    )
    flag_adapter = _flag_from_thresholds(
        mean_adapter, THRESH_FASTP_ADAPTER_GOOD, THRESH_FASTP_ADAPTER_MODERATE
    )
    flag_dup = _flag_from_thresholds(
        mean_dup, THRESH_FASTP_DUPLICATION_GOOD, THRESH_FASTP_DUPLICATION_MODERATE
    )

    def _describe_metric(value: Optional[float], flag_value: int, templates: Dict[Any, str]) -> str:
        if value is None:
            return templates.get("missing", "")
        pct = value * 100
        entry = templates.get(flag_value) or templates.get("default", "")
        return entry.format(pct=pct)

    template_low_phred = {
        1: "Reads failing phred-score checks are scarce ({pct:.1f}%), so trimming losses are negligible.",
        2: "About {pct:.1f}% of reads are flagged for low phred quality, slightly reducing usable depth in those libraries.",
        3: "Roughly {pct:.1f}% of reads fail phred-score checks, signalling systemic quality issues that erode effective depth.",
        "missing": "Low phred-score reads could not be quantified.",
    }
    template_complexity = {
        1: "Low-complexity reads are uncommon ({pct:.1f}%), so repetitive fragments are not inflating filtering.",
        2: "{pct:.1f}% of reads are flagged as low complexity, which can point to repetitive artifacts in a subset of libraries.",
        3: "Approximately {pct:.1f}% of reads are filtered for low complexity, suggesting sequencing/library artifacts dominate.",
        "missing": "Low-complexity filtering could not be quantified.",
    }
    template_too_short = {
        1: "Reads flagged as too short are rare ({pct:.1f}%), indicating insert-size selection is consistent.",
        2: "Roughly {pct:.1f}% of reads are flagged as too short, hinting at mild fragmentation or tagmentation issues.",
        3: "Around {pct:.1f}% of reads are removed as too short, pointing to excessive DNA shearing or degradation, or excessive residual adapters.",
        "missing": "Length-based filtering could not be evaluated.",
    }
    template_adapter = {
        1: "Adapter trimming remains minor ({pct:.1f}%), suggesting library fragment-sizes were appropriate.",
        2: "Adapter trimming affects {pct:.1f}% of reads, indicating that a significant proportion of inserts are shorter than the employed read length.",
        3: "Adapter trimming was applied to about {pct:.1f}% of reads, reducing the effective length of the reads.",
        "missing": "Adapter trimming events could not be quantified.",
    }
    template_dup = {
        1: "Duplicate reads remain modest ({pct:.1f}%), so technical replicates should not hurt effective depth.",
        2: "Duplicates account for {pct:.1f}% of reads; expect effective depth to be slightly lower than raw counts suggest. This might impact assembly quality and introduce biases in contig and MAG quantification.",
        3: "Duplicates comprise about {pct:.1f}% of reads, meaning many molecules are PCR replicates and true coverage is markedly lower. This will likely impact assembly quality and introduce biases in contig and MAG quantification.",
        "missing": "Duplicate rates could not be quantified.",
    }

    parts = [message]
    parts.append(_describe_metric(mean_low_q, flag_phred, template_low_phred))
    parts.append(_describe_metric(mean_low_complex, flag_complexity, template_complexity))
    parts.append(_describe_metric(mean_too_short, flag_too_short, template_too_short))
    parts.append(_describe_metric(mean_adapter, flag_adapter, template_adapter))
    parts.append(_describe_metric(mean_dup, flag_dup, template_dup))
    enriched_message = " ".join(p for p in parts if p)

    subset_flags = [flag_phred, flag_complexity, flag_too_short, flag_adapter, flag_dup]
    valid_flags = [f for f in subset_flags if f is not None]
    if not valid_flags:
        flag_overall = 3
    elif any(f == 3 for f in valid_flags):
        flag_overall = 3
    elif any(f == 2 for f in valid_flags):
        flag_overall = 2
    else:
        flag_overall = 1

    return {
        "n_samples": n_samples_with_fastp,
        "total_reads": total_reads_all,
        "total_removed_reads": total_removed_all,
        "percent_removed_reads_overall": percent_removed_overall,
        "mean_fraction_removed": mean_frac,
        "sd_fraction_removed": sd_frac,
        "mean_fraction_low_quality": mean_low_q,
        "mean_fraction_low_complexity": mean_low_complex,
        "mean_fraction_too_short": mean_too_short,
        "mean_fraction_adapter_trimmed": mean_adapter,
        "mean_duplication_rate": mean_dup,
        "flag_sequencing_quality": flag_overall,
        "flag_phred_score": flag_phred,
        "flag_complexity": flag_complexity,
        "flag_too_short": flag_too_short,
        "flag_adapter_trimming": flag_adapter,
        "flag_duplication": flag_dup,
        "message_low_quality": enriched_message,
    }


# ---------- 4) Prokaryotic fraction (SingleM read_fraction) ----------

def compute_prokaryotic_fraction(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise the prokaryotic fraction (read_fraction) from SingleM-based results.

    - Classification for mean prokaryotic fraction (interpreted as %):
        > THRESH_PROK_HIGH   → flag = 1
        > THRESH_PROK_MODERATE → flag = 2
        <= THRESH_PROK_MODERATE  → flag = 3
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

    if mean_frac > THRESH_PROK_HIGH:
        flag_mean = 1
    elif mean_frac > THRESH_PROK_MODERATE:
        flag_mean = 2
    else:
        flag_mean = 3

    if mean_frac is None:
        mean_frac_msg = "Prokaryotic fraction cannot be evaluated."
    else:
        if mean_frac > THRESH_PROK_HIGH:
            mean_frac_msg = (
                f"Average prokaryotic fraction of the dataset is high ({mean_frac:.2f}%), "
                "indicating that marginal amounts of host and other non-prokaryotic DNA are unlikely to affect the analyses. "
            )
        elif mean_frac > THRESH_PROK_MODERATE:
            mean_frac_msg = (
                f"Average prokaryotic fraction of the dataset is moderate ({mean_frac:.2f}%), "
                "indicating that samples may contain significant amounts of host or other non-prokaryotic DNA "
                "that could affect the analyses (e.g., slow down or disrupt assembly, reduce binning efficacy etc.). "
                "If the host genome is available, consider removing host reads prior to assembly, but bear in mind that the resulting "
                "effective sequencing depth for prokaryotes will be lower. "
            )
        else:
            mean_frac_msg = (
                f"Average prokaryotic fraction of the dataset is low ({mean_frac:.2f}%), "
                "indicating that samples likely contain high amounts of host or other non-prokaryotic (e.g., dietary remains) DNA. "
                "This could severely affect downstream analyses, by affecting assembly quality and binning success. "
                "If the host genome is available, remove host reads prior to assembly, but bear in mind that the resulting "
                "effective sequencing depth for prokaryotes will be very low. "
            )

    if cv_frac is None:
        var_msg = "Variation in prokaryotic fraction cannot be evaluated."
    else:
        if cv_frac < THRESH_CV_BALANCED:
            var_msg = (
                f"Prokaryotic fraction is consistent across samples (CV = {cv_frac:.2f}), "
                "so this factor is not expected to affect downstream analyses."
            )
        elif cv_frac < THRESH_CV_MODERATE:
            var_msg = (
                f"Prokaryotic fraction shows moderate variation across samples (CV = {cv_frac:.2f}), "
                "suggesting that the relative contribution of samples to the metagenomic assemblies and "
                "the representativeness of reconstructed microbial profiles among samples may vary ."
                "It is recommended to take prokaryotic fraction into account when comparing microbial profiles between samples."
            )
        else:
            var_msg = (
                f"Prokaryotic fraction is highly variable across samples (CV = {cv_frac:.2f}), "
                "indicating that the relative contribution of samples to the metagenomic assemblies and the "
                "representativeness of reconstructed microbial profiles among samples will likely vary significantly. "
                "It is strongly recommended to take prokaryotic fraction into account when comparing microbial profiles between samples. "
            )

    warning_ratio = warnings_count / n_samples if n_samples > 0 else 0.0
    if warnings_count == 0:
        warn_msg = ""
    elif warning_ratio >= THRESH_WARNINGS_HIGH_FRACTION:
        warn_msg = (
            f"Note that many samples ({warnings_count}/{n_samples}) contain warnings in prokaryotic fraction estimation, "
            "indicating that the reliability of the estimated prokaryotic fractions is low across the dataset. "
            "If sequencing depth is high enough, consider increasing the number of reads used for estimation "
            "through the -r parameter to improve these estimates. "
        )
    else:
        warn_msg = (
            f"Note that some samples ({warnings_count}/{n_samples}) contain warnings in prokaryotic fraction estimation, "
            "indicating that the reliability of the estimated prokaryotic fractions is low for some samples. "
            "Consider checking those samples individually. "
        )

    message = (
        mean_frac_msg + " "
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
    Summarise coverage/completeness on metagenome reads using Nonpareil LR targets.

    We still report C_total statistics for reference, but colour/flags and
    messaging are based on how many samples meet the LR target (coverage ratio)
    rather than on redundancy alone.
    """
    samples = results_json.get("samples", {}) or {}

    c_totals: List[float] = []
    lr_exceeds = 0
    n_with_lr = 0
    coverage_ratios: List[float] = []
    coverage_estimates: List[float] = []
    lr_target_used: Optional[str] = None

    for name, sample_data in samples.items():
        npr = sample_data.get("nonpareil_reads", {}) or {}
        if not npr:
            continue

        cov = npr.get("C_total")
        if isinstance(cov, str):
            try:
                cov = float(cov)
            except ValueError:
                cov = None
        if isinstance(cov, (int, float)) and cov >= 0:
            coverage_estimates.append(float(cov))

        # C_total
        kappa = npr.get("C_total")
        if isinstance(kappa, str):
            try:
                kappa = float(kappa)
            except ValueError:
                kappa = None
        if isinstance(kappa, (int, float)):
            c_totals.append(float(kappa))

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
                if lr_reads and lr_reads not in (0, float("inf")):
                    coverage_ratios.append(total_reads / lr_reads)

    n_kappa = len(c_totals)

    if n_kappa == 0:
        msg = (
            "No Nonpareil-based redundancy estimates (C_total) were found for reads; "
            "redundancy and LR-based effort cannot be assessed."
        )
        return {
            "n_samples_kappa": 0,
            "mean_C_total": None,
            "median_C_total": None,
            "sd_C_total": None,
            "cv_C_total": None,
            "flag_redundancy": 3,
            "n_samples_with_lr": n_with_lr,
            "n_samples_lr_exceeds_depth": lr_exceeds,
            "flag_LR_vs_depth": 3 if n_with_lr > 0 else None,
            "lr_target_used": lr_target_used,
            "message_redundancy": msg,
        }

    mean_k = stats.mean(c_totals)
    median_k = stats.median(c_totals)
    sd_k = stats.pstdev(c_totals) if n_kappa > 1 else 0.0
    cv_k = sd_k / mean_k if mean_k > 0 else None
    cov_median = stats.median(coverage_estimates) if coverage_estimates else None
    cov_cv = None
    if coverage_estimates:
        mean_cov = stats.mean(coverage_estimates)
        if mean_cov > 0:
            sd_cov = stats.pstdev(coverage_estimates) if len(coverage_estimates) > 1 else 0.0
            cov_cv = sd_cov / mean_cov

    # Coverage-based flags (primary, separate components)
    n_cov = len(coverage_ratios)
    n_meet = sum(1 for r in coverage_ratios if r >= 1.0)
    frac_meet = (n_meet / n_cov) if n_cov else 0.0
    median_ratio = stats.median(coverage_ratios) if coverage_ratios else None
    mean_ratio = stats.mean(coverage_ratios) if coverage_ratios else None

    if median_ratio is None:
        flag_cov_median = 3
    else:
        if median_ratio >= THRESH_COV_MEDIAN_GOOD:
            flag_cov_median = 1
        elif median_ratio >= THRESH_COV_MEDIAN_MODERATE:
            flag_cov_median = 2
        else:
            flag_cov_median = 3

    if n_cov == 0:
        flag_cov_samples = 3
    else:
        if frac_meet >= THRESH_COV_SAMPLES_GOOD:
            flag_cov_samples = 1
        elif frac_meet >= THRESH_COV_SAMPLES_MODERATE:
            flag_cov_samples = 2
        else:
            flag_cov_samples = 3

    if n_cov == 0:
        coverage_msg = (
            "No LR_reads targets with valid coverage ratios were found; cannot assess completeness for metagenomic reads."
        )
    else:
        coverage_msg = (
            f"{n_meet}/{n_cov} samples meet or exceed the coverage target ({lr_target_used}%). "
            f"Median coverage ratio is {median_ratio:.2f}× "
            f"(mean {mean_ratio:.2f}×)."
        )

    flag_redundancy = max(flag_cov_median, flag_cov_samples)

    # LR vs depth flag (1/2/3, plus 4 when none meet target depth)
    if n_with_lr == 0:
        flag_lr = 3
        lr_msg = (
            "No LR_reads targets were available from Nonpareil (reads); "
            "cannot compare required sequencing effort to observed depth."
        )
    else:
        frac_exceeds = lr_exceeds / n_with_lr
        if lr_exceeds == 0:
            flag_lr = 1
            lr_msg = (
                f"All {n_with_lr} samples are at or above the sequencing depth needed for {lr_target_used}% completeness."
            )
        elif lr_exceeds == n_with_lr:
            flag_lr = 4
            lr_msg = (
                f"All {n_with_lr} samples fall below the depth needed for {lr_target_used}% completeness."
            )
        elif frac_exceeds < THRESH_LR_EXCEEDS_FRACTION:
            flag_lr = 2
            lr_msg = (
                f"{lr_exceeds}/{n_with_lr} samples fall below the depth needed for {lr_target_used}% completeness."
            )
        else:
            flag_lr = 3
            lr_msg = (
                f"Most samples ({lr_exceeds}/{n_with_lr}) fall below the depth needed for {lr_target_used}% completeness."
            )

    message = coverage_msg
    if lr_msg and flag_lr != 4:
        message += " " + lr_msg

    return {
        "n_samples_kappa": n_kappa,
        "mean_C_total": mean_k,
        "median_C_total": median_k,
        "sd_C_total": sd_k,
        "cv_C_total": cv_k,
        "coverage_median": cov_median,
        "coverage_ratio_median": median_ratio,
        "coverage_ratio_mean": mean_ratio,
        "coverage_cv": cov_cv,
        "flag_redundancy": flag_redundancy,
        "flag_coverage_median": flag_cov_median,
        "flag_coverage_samples": flag_cov_samples,
        "percent_samples_meet_target": frac_meet * 100 if n_cov else None,
        "n_samples_with_lr": n_with_lr,
        "n_samples_lr_exceeds_depth": lr_exceeds,
        "flag_LR_vs_depth": flag_lr,
        "lr_target_used": lr_target_used,
        "coverage_ratios": coverage_ratios if coverage_ratios else None,
        "message_redundancy": message,
    }


# ---------- 7) Redundancy based on marker genes (Nonpareil on markers) ----------

def compute_redundancy_markers(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise marker-based coverage/completeness using Nonpareil LR targets.

    Flags and explanations are based on target coverage; C_total is kept for reference.
    """
    samples = results_json.get("samples", {}) or {}

    c_totals: List[float] = []
    lr_exceeds = 0
    n_with_lr = 0
    coverage_ratios: List[float] = []
    coverage_estimates: List[float] = []
    lr_target_used: Optional[str] = None

    for name, sample_data in samples.items():
        npr = sample_data.get("nonpareil_markers", {}) or {}
        if not npr:
            continue

        cov = npr.get("C_total")
        if isinstance(cov, str):
            try:
                cov = float(cov)
            except ValueError:
                cov = None
        if isinstance(cov, (int, float)) and cov >= 0:
            coverage_estimates.append(float(cov))

        # C_total for markers
        kappa = npr.get("C_total")
        if isinstance(kappa, str):
            try:
                kappa = float(kappa)
            except ValueError:
                kappa = None
        if isinstance(kappa, (int, float)):
            c_totals.append(float(kappa))

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
                if lr_reads and lr_reads not in (0, float("inf")):
                    coverage_ratios.append(depth / lr_reads)

    n_kappa = len(c_totals)

    if n_kappa == 0:
        msg = (
            "No Nonpareil-based redundancy estimates (C_total) were found for marker genes; "
            "marker redundancy and LR-based effort cannot be assessed."
        )
        return {
            "n_samples_kappa": 0,
            "mean_C_total": None,
            "median_C_total": None,
            "sd_C_total": None,
            "cv_C_total": None,
            "flag_redundancy_markers": 3,
            "n_samples_with_lr": n_with_lr,
            "n_samples_lr_exceeds_depth": lr_exceeds,
            "flag_LR_vs_depth_markers": 3 if n_with_lr > 0 else None,
            "lr_target_used": lr_target_used,
            "message_redundancy_markers": msg,
        }

    mean_k = stats.mean(c_totals)
    median_k = stats.median(c_totals)
    sd_k = stats.pstdev(c_totals) if n_kappa > 1 else 0.0
    cv_k = sd_k / mean_k if mean_k > 0 else None
    cov_median = stats.median(coverage_estimates) if coverage_estimates else None
    cov_cv = None
    if coverage_estimates:
        mean_cov = stats.mean(coverage_estimates)
        if mean_cov > 0:
            sd_cov = stats.pstdev(coverage_estimates) if len(coverage_estimates) > 1 else 0.0
            cov_cv = sd_cov / mean_cov

    # Coverage-based flags (primary, separate components)
    n_cov = len(coverage_ratios)
    n_meet = sum(1 for r in coverage_ratios if r >= 1.0)
    frac_meet = (n_meet / n_cov) if n_cov else 0.0
    median_ratio = stats.median(coverage_ratios) if coverage_ratios else None
    mean_ratio = stats.mean(coverage_ratios) if coverage_ratios else None

    if median_ratio is None:
        flag_cov_median = 3
    else:
        if median_ratio >= THRESH_COV_MEDIAN_GOOD:
            flag_cov_median = 1
        elif median_ratio >= THRESH_COV_MEDIAN_MODERATE:
            flag_cov_median = 2
        else:
            flag_cov_median = 3

    if n_cov == 0:
        flag_cov_samples = 3
    else:
        if frac_meet >= THRESH_COV_SAMPLES_GOOD:
            flag_cov_samples = 1
        elif frac_meet >= THRESH_COV_SAMPLES_MODERATE:
            flag_cov_samples = 2
        else:
            flag_cov_samples = 3

    if n_cov == 0:
        coverage_msg = (
            "No LR_reads targets with valid coverage ratios were found; cannot assess completeness for marker genes."
        )
    else:
        coverage_msg = (
            f"{n_meet}/{n_cov} samples meet or exceed the LR target ({lr_target_used}%). "
            f"Median coverage ratio is {median_ratio:.2f}× "
            f"(mean {mean_ratio:.2f}×)."
        )

    flag_redundancy = max(flag_cov_median, flag_cov_samples)

    # LR vs depth flag (1/2/3, plus 4 when none meet target depth)
    if n_with_lr == 0:
        flag_lr = 3
        lr_msg = (
            "No LR_reads targets were available from Nonpareil (markers); "
            "cannot compare required marker sequencing effort to observed marker depth."
        )
    else:
        frac_exceeds = lr_exceeds / n_with_lr
        if lr_exceeds == 0:
            flag_lr = 1
            lr_msg = (
                f"All {n_with_lr} samples are at or above the marker depth needed for {lr_target_used}% completeness."
            )
        elif lr_exceeds == n_with_lr:
            flag_lr = 4
            lr_msg = (
                f"All {n_with_lr} samples fall below the marker depth needed for {lr_target_used}% completeness."
            )
        elif frac_exceeds < THRESH_LR_EXCEEDS_FRACTION:
            flag_lr = 2
            lr_msg = (
                f"{lr_exceeds}/{n_with_lr} samples fall below the marker depth needed for {lr_target_used}% completeness."
            )
        else:
            flag_lr = 3
            lr_msg = (
                f"Most samples ({lr_exceeds}/{n_with_lr}) fall below the marker depth needed for {lr_target_used}% completeness."
            )

    message = coverage_msg
    if lr_msg and flag_lr != 4:
        message += " " + lr_msg

    return {
        "n_samples_kappa": n_kappa,
        "mean_C_total": mean_k,
        "median_C_total": median_k,
        "sd_C_total": sd_k,
        "cv_C_total": cv_k,
        "coverage_median": cov_median,
        "coverage_ratio_median": median_ratio,
        "coverage_ratio_mean": mean_ratio,
        "coverage_cv": cov_cv,
        "flag_redundancy_markers": flag_redundancy,
        "flag_coverage_median_markers": flag_cov_median,
        "flag_coverage_samples_markers": flag_cov_samples,
        "percent_samples_meet_target_markers": frac_meet * 100 if n_cov else None,
        "n_samples_with_lr": n_with_lr,
        "n_samples_lr_exceeds_depth": lr_exceeds,
        "flag_LR_vs_depth_markers": flag_lr,
        "lr_target_used": lr_target_used,
        "coverage_ratios": coverage_ratios if coverage_ratios else None,
        "message_redundancy_markers": message,
    }


# ---------- 8) Mash-based clusters (potential coassemblies) ----------

def _summarise_mash_cluster_block(
    mash_block: Optional[Dict[str, Any]],
    label: str,
) -> Dict[str, Any]:
    """
    Summarise clustering structure from a Mash block (markers or reads).

    Uses the precomputed summary.structure fields:
      - n_clusters
      - mean_within_distance / mean_between_distance
      - ratio_between_over_within
      - pair_ratio_mean / pair_ratio_sd

    and provides a flag + message describing how well-separated the clusters are
    as candidates for coassemblies.

    Flags:
      1 = well separated clusters (good candidates for coassembly)
      2 = moderate separation
      3 = weak/no separation or missing information

    Additionally, considers absolute within-cluster Mash distances:
      - if the worst mean within-cluster distance > THRESH_CLUSTER_WITHIN_STRONG → strong warning
      - if THRESH_CLUSTER_WITHIN_MILD < distance ≤ THRESH_CLUSTER_WITHIN_STRONG → mild warning
    """
    if not mash_block:
        return {
            "n_clusters": None,
            "n_between_pairs": None,
            "mean_within_distance": None,
            "sd_within_distance": None,
            "mean_between_distance": None,
            "sd_between_distance": None,
            "ratio_between_over_within": None,
            "pair_ratio_mean": None,
            "pair_ratio_sd": None,
            "clusters": [],
            "between_clusters": {},
            "flag_cluster_structure": 3,
            "message_cluster_structure": (
                f"No Mash-based {label} distances were found; coassembly clusters "
                "cannot be evaluated."
            ),
        }

    summary = mash_block.get("summary") or {}
    structure = summary.get("structure") or {}
    clusters_block = summary.get("clusters") or {}
    between_block = summary.get("between_clusters") or {}

    n_clusters = structure.get("n_clusters")
    n_between_pairs = structure.get("n_between_pairs")
    mean_within = structure.get("mean_within_distance")
    sd_within = structure.get("sd_within_distance")
    mean_between = structure.get("mean_between_distance")
    sd_between = structure.get("sd_between_distance")
    ratio = structure.get("ratio_between_over_within")
    pair_ratio_mean = structure.get("pair_ratio_mean")
    pair_ratio_sd = structure.get("pair_ratio_sd")

    # Per-cluster info (compact summary)
    cluster_list: List[Dict[str, Any]] = []
    for cid, c in clusters_block.items():
        members = c.get("members") or []
        n_members = c.get("n_members", len(members))
        mean_d = c.get("mean_distance")
        median_d = c.get("median_distance")
        cluster_list.append(
            {
                "cluster_id": cid,
                "n_members": n_members,
                "members": members,
                "mean_distance": mean_d,
                "median_distance": median_d,
            }
        )

    # Sort clusters by within-cluster mean distance (more compact first)
    cluster_list.sort(
        key=lambda x: (
            x["mean_distance"]
            if isinstance(x.get("mean_distance"), (int, float))
            else float("inf")
        )
    )

    # Flag and message based on separation ratio
    if not n_clusters or n_clusters <= 1 or ratio is None:
        if not n_clusters or n_clusters <= 1:
            msg = (
                f"Mash-based clustering of {label} distances identifies a single group "
                "of samples or no clusters, indicating no clear subdivision into "
                "candidate coassemblies."
            )
        else:
            msg = (
                f"Mash-based clustering of {label} distances could not be fully evaluated "
                "because required summary statistics are missing."
            )
        flag = 3
    else:
        # Interpret ratio = between / within as separation; "magnified" so that
        # higher ratios correspond to flag = 1, lower to 2 or 3.
        if ratio >= THRESH_CLUSTER_RATIO_GOOD:
            flag = 1
            msg = (
                f"Clusters based on Mash {label} distances are well separated "
                f"(between-cluster distances are on average {ratio:.2f}× higher than "
                "within-cluster distances). These clusters are strong candidates for "
                "defining coassemblies."
            )
        elif ratio >= THRESH_CLUSTER_RATIO_MODERATE:
            flag = 2
            msg = (
                f"Clusters based on Mash {label} distances show modest separation "
                f"(between-cluster distances are on average {ratio:.2f}× higher than "
                "within-cluster distances). Coassemblies based on these clusters are "
                "possible, but some mixing of moderately distinct communities is likely."
            )
        else:
            flag = 3
            msg = (
                f"Clusters based on Mash {label} distances are weakly separated "
                f"(between-cluster distances are only {ratio:.2f}× higher than "
                "within-cluster distances). Using these clusters for coassemblies may "
                "mix samples with quite different community compositions."
            )

        # Optional note on cluster size balance
        sizes = [c["n_members"] for c in cluster_list if c.get("n_members") is not None]
        if sizes:
            total = sum(sizes)
            max_size = max(sizes)
            mean_size = stats.mean(sizes)
            if (
                total > 0
                and max_size >= THRESH_CLUSTER_SIZE_UNBALANCED_FACTOR * mean_size
            ):
                msg += (
                    f" Cluster sizes are unbalanced (largest cluster has {max_size} out "
                    f"of {total} samples), so coassemblies may be dominated by a single "
                    "large group."
                )

    # Additional warning based on absolute within-cluster Mash distances
    # We look at the worst (maximum) mean distance across clusters, and
    # fall back to the global mean_within_distance if needed.
    worst_mean_within = None
    for c in cluster_list:
        d = c.get("mean_distance")
        if isinstance(d, (int, float)):
            if worst_mean_within is None or d > worst_mean_within:
                worst_mean_within = d

    global_mean_within = (
        mean_within if isinstance(mean_within, (int, float)) else None
    )

    # Prefer the worst per-cluster value; if not available, use global mean
    ref_within = worst_mean_within if worst_mean_within is not None else global_mean_within

    if ref_within is not None:
        if ref_within > THRESH_CLUSTER_WITHIN_STRONG:
            # Strong warning: within-cluster distances high in absolute terms
            if flag == 1:
                flag = 2  # demote slightly: not as ideal as ratio alone suggests
            msg += (
                f" However, within-cluster Mash distances are high in absolute terms "
                f"(mean up to {ref_within:.3f}), so even samples grouped together can "
                "be quite dissimilar. Consider splitting large clusters or using "
                "single-sample assemblies for the most divergent samples."
            )
        elif ref_within > THRESH_CLUSTER_WITHIN_MILD:
            # Mild warning
            if flag < 2:
                flag = 2
            msg += (
                f" Note that within-cluster Mash distances are moderate in absolute "
                f"terms (mean up to {ref_within:.3f}), so coassemblies may mix "
                "communities that are not extremely similar."
            )

    return {
        "n_clusters": n_clusters,
        "n_between_pairs": n_between_pairs,
        "mean_within_distance": mean_within,
        "sd_within_distance": sd_within,
        "mean_between_distance": mean_between,
        "sd_between_distance": sd_between,
        "ratio_between_over_within": ratio,
        "pair_ratio_mean": pair_ratio_mean,
        "pair_ratio_sd": pair_ratio_sd,
        "clusters": cluster_list,
        "between_clusters": between_block,
        "flag_cluster_structure": flag,
        "message_cluster_structure": msg,
    }


def compute_clusters(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarise Mash-based clustering (markers and reads) as potential
    coassembly groups.

    Returns a nested structure with per-distance-type summaries and an
    overall flag/message (preferring markers if available).

    Additionally passes through *filtered* raw pairwise Mash distances
    (markers and reads), keeping only sample1, sample2, and distance.
    """
    mash_markers_block = results_json.get("mash_markers") or {}
    mash_reads_block = results_json.get("mash_reads") or {}

    markers_summary = _summarise_mash_cluster_block(mash_markers_block, "marker")
    reads_summary = _summarise_mash_cluster_block(mash_reads_block, "read")

    # pick dominant summary for overall flag/message
    overall_source = markers_summary
    if (
        markers_summary.get("n_clusters") is None
        or markers_summary.get("n_clusters", 0) <= 1
    ) and reads_summary.get("n_clusters", 0) > 1:
        overall_source = reads_summary

    overall_flag = overall_source.get("flag_cluster_structure")
    overall_message = overall_source.get("message_cluster_structure")

    # ---- FILTER PAIRWISE DISTANCES ----
    def extract_pairwise(block):
        pw = block.get("pairwise")
        if not isinstance(pw, list):
            return None
        filtered = []
        for rec in pw:
            if not isinstance(rec, dict):
                continue
            s1 = rec.get("sample1")
            s2 = rec.get("sample2")
            dist = rec.get("distance")
            if s1 is None or s2 is None or dist is None:
                continue
            filtered.append({
                "sample1": s1,
                "sample2": s2,
                "distance": dist
            })
        return filtered if filtered else None

    pairwise_markers = extract_pairwise(mash_markers_block)
    pairwise_reads = extract_pairwise(mash_reads_block)

    return {
        "markers": markers_summary,
        "reads": reads_summary,
        "flag_clusters": overall_flag,
        "message_clusters": overall_message,
        # new filtered pairwise distance lists
        "pairwise_markers": pairwise_markers,
        "pairwise_reads": pairwise_reads,
    }


def _build_distance_matrix(pairwise: Optional[List[Dict[str, Any]]]) -> Tuple[List[str], Optional[np.ndarray]]:
    """
    Convert a list of pairwise records (sample1, sample2, distance) into a square
    distance matrix. Returns (sample_names, matrix) where matrix is None if
    distances are missing or invalid.
    """
    if not pairwise:
        return [], None

    samples: List[str] = []
    for rec in pairwise:
        s1 = rec.get("sample1")
        s2 = rec.get("sample2")
        if s1 is not None:
            samples.append(s1)
        if s2 is not None:
            samples.append(s2)
    sample_names = sorted(set(samples))
    n = len(sample_names)
    if n < 2:
        return sample_names, None

    index = {s: i for i, s in enumerate(sample_names)}
    mat = np.full((n, n), np.nan, dtype=float)
    np.fill_diagonal(mat, 0.0)

    for rec in pairwise:
        s1 = rec.get("sample1")
        s2 = rec.get("sample2")
        dist = rec.get("distance")
        if s1 not in index or s2 not in index:
            continue
        try:
            dval = float(dist)
        except (TypeError, ValueError):
            continue
        i, j = index[s1], index[s2]
        mat[i, j] = dval
        mat[j, i] = dval

    if np.isnan(mat).any():
        return sample_names, None
    return sample_names, mat


def _pcoa(distance_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform classical multidimensional scaling (PCoA) on a full distance matrix.
    Returns eigenvalues, variance explained, and coordinates (n x 2).
    """
    n = distance_matrix.shape[0]
    if n < 2:
        return np.array([]), np.array([]), np.zeros((n, 2))

    d2 = distance_matrix ** 2
    H = np.eye(n) - np.full((n, n), 1.0 / n)
    B = -0.5 * H @ d2 @ H

    eigvals, eigvecs = np.linalg.eigh(B)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    positive = np.clip(eigvals, a_min=0.0, a_max=None)
    total = positive.sum()
    var_expl = positive / total if total > 0 else np.array([])

    keep = min(2, eigvecs.shape[1])
    coords = eigvecs[:, :keep] * np.sqrt(np.clip(eigvals[:keep], a_min=0.0, a_max=None))
    if coords.shape[1] < 2:
        coords = np.pad(coords, ((0, 0), (0, 2 - coords.shape[1])), "constant")
    return eigvals, var_expl, coords


def _cluster_map(clusters_block: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a mapping sample -> cluster_id from a cluster summary block.
    """
    mapping: Dict[str, Any] = {}
    for entry in clusters_block.get("clusters", []):
        cid = entry.get("cluster_id")
        if cid is None:
            continue
        for sample in entry.get("members") or []:
            mapping[sample] = cid
    return mapping


def compute_ordination_from_pairwise(
    pairwise: Optional[List[Dict[str, Any]]],
    markers_map: Dict[str, Any],
    reads_map: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Build a 2D ordination (PCoA) from pairwise distances and annotate each point
    with marker/read cluster assignments.
    """
    sample_names, dist_matrix = _build_distance_matrix(pairwise)
    if dist_matrix is None or not len(sample_names):
        return None

    eigvals, var_expl, coords = _pcoa(dist_matrix)
    sample_coords: List[Dict[str, Any]] = []
    for i, sample in enumerate(sample_names):
        sample_coords.append(
            {
                "sample": sample,
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
                "cluster_markers": markers_map.get(sample),
                "cluster_reads": reads_map.get(sample),
            }
        )

    return {
        "method": "PCoA",
        "n_samples": len(sample_names),
        "variance_explained": [float(v) for v in var_expl[:2]],
        "variance_explained_cumulative": float(var_expl[:2].sum()) if var_expl.size else None,
        "eigenvalues": [float(ev) for ev in eigvals[:2]],
        "samples": sample_coords,
    }


def compute_ordinations(clusters: Dict[str, Any], seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Create ordination coordinates for marker- and read-based Mash distances.
    If both are available, uses a seed-driven Procrustes alignment to orient
    the read ordination closer to the marker ordination (helps comparability).
    """
    markers_block = clusters.get("markers", {}) or {}
    reads_block = clusters.get("reads", {}) or {}
    markers_map = _cluster_map(markers_block)
    reads_map = _cluster_map(reads_block)

    ord_markers = compute_ordination_from_pairwise(
        clusters.get("pairwise_markers"),
        markers_map,
        reads_map,
    )
    ord_reads = compute_ordination_from_pairwise(
        clusters.get("pairwise_reads"),
        markers_map,
        reads_map,
    )

    def _align_reads_to_markers(ord_reads_local, ord_markers_local, seed_local):
        if not ord_reads_local or not ord_markers_local:
            return ord_reads_local
        samples_reads = ord_reads_local.get("samples") or []
        samples_mark = ord_markers_local.get("samples") or []
        if not samples_reads or not samples_mark:
            return ord_reads_local
        marker_map = {s["sample"]: s for s in samples_mark if "sample" in s}
        common_idx = [i for i, s in enumerate(samples_reads) if s.get("sample") in marker_map]
        if len(common_idx) < 2:
            return ord_reads_local

        rng = np.random.default_rng(seed_local if seed_local is not None else 0)

        coords_reads = np.array([[float(s.get("x", 0) or 0), float(s.get("y", 0) or 0)] for s in samples_reads])
        coords_marks = np.array([
            [
                float(marker_map[samples_reads[i]["sample"]].get("x", 0) or 0),
                float(marker_map[samples_reads[i]["sample"]].get("y", 0) or 0),
            ]
            for i in common_idx
        ])
        coords_common = coords_reads[common_idx]

        # Center
        src_mean = coords_common.mean(axis=0)
        tgt_mean = coords_marks.mean(axis=0)
        src_centered = coords_common - src_mean
        tgt_centered = coords_marks - tgt_mean

        # Covariance and rotation
        cov = src_centered.T @ tgt_centered
        try:
            U, _, Vt = np.linalg.svd(cov)
            R = U @ Vt
            if np.linalg.det(R) < 0:
                flip = np.eye(R.shape[0])
                flip[-1, -1] = -1
                R = U @ flip @ Vt
                # optional seeded jitter for tie-breaking reflection
                if rng.random() < 0.5:
                    R = -R
        except np.linalg.LinAlgError:
            return ord_reads_local

        src_var = np.sum(src_centered ** 2)
        if src_var == 0:
            return ord_reads_local
        scale = np.trace(R.T @ cov) / src_var

        # Apply transform to all read points
        transformed = ((coords_reads - src_mean) @ R) * scale + tgt_mean
        for i, s in enumerate(samples_reads):
            s["x"] = float(transformed[i, 0])
            s["y"] = float(transformed[i, 1])
        ord_reads_local["aligned_to_markers"] = True
        return ord_reads_local

    ord_reads = _align_reads_to_markers(ord_reads, ord_markers, seed)

    return {
        "markers": ord_markers,
        "reads": ord_reads,
    }


def compute_recommendations(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a simple recommendation block based on existing section flags/metrics.
    The HTML report will later render these as itemised suggestions.
    """
    items: List[Dict[str, Any]] = []

    screen = summary.get("screening_overview", {}) or {}
    lowq = summary.get("sequencing_quality", {}) or {}
    prok = summary.get("prokaryotic_fraction", {}) or {}
    red_reads = summary.get("redundancy_reads", {}) or {}
    red_mark = summary.get("redundancy_markers", {}) or {}
    clusters = summary.get("clusters", {}) or {}

    # Coverage signals
    cov_flags = [
        red_reads.get("flag_redundancy"),
        red_mark.get("flag_redundancy_markers"),
    ]
    cov_flags = [f for f in cov_flags if f is not None]
    worst_cov_flag = max(cov_flags) if cov_flags else 3

    # Depth balance / quality / prok signals
    depth_cv = screen.get("cv_reads")
    lowq_flag = lowq.get("flag_sequencing_quality", 3)
    prok_flag = prok.get("flag_prokaryotic_fraction", 3)

    markers_block = clusters.get("markers", {}) or {}
    reads_block = clusters.get("reads", {}) or {}
    n_clusters = markers_block.get("n_clusters") or reads_block.get("n_clusters")
    clusters_flag = clusters.get("flag_clusters", 3)
    cluster_ratio_ok = (
        (markers_block.get("ratio_between_over_within") or 0) >= THRESH_CLUSTER_RATIO_GOOD
        or (reads_block.get("ratio_between_over_within") or 0) >= THRESH_CLUSTER_RATIO_GOOD
    )

    # All sections green → straightforward genome-resolved path
    all_flags = [
        screen.get("flag_screening_overview"),
        lowq_flag,
        prok_flag,
        red_reads.get("flag_redundancy"),
        red_mark.get("flag_redundancy_markers"),
        clusters_flag,
    ]
    all_green = all(f == 1 for f in all_flags if f is not None)

    if all_green:
        overall = "Data quality and coverage are excellent; individual assemblies for genome-resolved MAG recovery are recommended."
        items.append({
            "priority": "high",
            "text": "Proceed with genome-resolved metagenomics using individual assemblies; coassemblies not required."
        })
    elif worst_cov_flag == 1 and prok_flag == 1:
        overall = "Coverage supports genome-resolved work; most samples look strong."
        items.append({
            "priority": "high",
            "text": "Individual assemblies are recommended; cluster-based coassemblies are optional for nuanced comparisons."
        })
    elif worst_cov_flag <= 2 and prok_flag == 1:
        overall = "Coverage is mixed; genome-resolved performance will vary."
        if clusters_flag == 1 and n_clusters and n_clusters > 1 and cluster_ratio_ok:
            items.append({
                "priority": "high",
                "text": "Use coassemblies per cluster to mitigate uneven coverage; retain individual assemblies for well-covered samples."
            })
        else:
            items.append({
                "priority": "high",
                "text": "Genome-resolved MAG recovery is feasible for better-covered samples; filter or down-weight low-depth libraries."
            })
    elif prok_flag in (1, 2):
        overall = "Prokaryotic signal is present but coverage is limited."
        if clusters_flag == 1 and n_clusters and n_clusters > 1 and cluster_ratio_ok:
            items.append({
                "priority": "high",
                "text": "Cluster-driven coassemblies are recommended to pool reads and boost prokaryotic coverage."
            })
        else:
            items.append({
                "priority": "high",
                "text": "Whole-dataset coassembly may be needed to increase effective coverage; expect fragmented MAG recovery."
            })
    else:
        overall = "Low prokaryotic signal and/or poor coverage; assemblies will struggle."
        items.append({
            "priority": "high",
            "text": "Prioritise read-based profiling; use community-level assemblies only for broad functional overviews."
        })

    # Assembly strategy
    if worst_cov_flag <= 2 and not all_green:
        if depth_cv is not None and depth_cv < 0.2:
            items.append({
                "priority": "info",
                "text": "Depth is balanced; individual assemblies remain a solid default."
            })
        elif clusters_flag == 1 and isinstance(n_clusters, int) and n_clusters > 1 and cluster_ratio_ok:
            items.append({
                "priority": "info",
                "text": "Coassemblies per well-separated cluster can improve recovery while respecting sample structure."
            })
        else:
            items.append({
                "priority": "info",
                "text": "Hybrid approach: assemble high-depth samples individually and coassemble weaker groups."
            })

    # Quality / prokaryotic content
    if lowq_flag == 3:
        items.append({
            "priority": "warn",
            "text": "Low sequencing quality in several samples suggests aggressive QC or dropping worst libraries before assembly."
        })
    if prok_flag == 3:
        items.append({
            "priority": "warn",
            "text": "Low prokaryotic fraction indicates contamination/human/host signal; enrichment or read-based profiling may be safer."
        })

    # Read-based fallback
    if worst_cov_flag == 3 or lowq_flag == 3 or prok_flag == 3:
        items.append({
            "priority": "info",
            "text": "Read-based taxonomic/functional profiling will provide robust community overviews even if assemblies underperform."
        })

    return {
        "overall": overall,
        "items": items,
    }



# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser(
        description=(
            "Distill ScreenM outputs (data.json + results.json) into a summary JSON.\n"
            "Includes: screening overview (threshold coverage + depth balance), "
            "sequencing quality, prokaryotic fraction, redundancy based on reads and "
            "marker genes, and Mash-based clustering as potential coassemblies."
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

    # Capture metadata (and allow reuse downstream, including seed/parameters)
    merged_metadata = {
        "data_json": str(data_path),
        "results_json": str(results_path),
    }
    results_metadata = results_json.get("metadata")
    if isinstance(results_metadata, dict):
        merged_metadata.update(results_metadata)

    screening_overview = compute_screening_overview(data_json, results_json)
    low_quality = compute_low_quality(results_json)
    prok_fraction = compute_prokaryotic_fraction(results_json)
    redundancy_reads = compute_redundancy_reads(results_json)
    redundancy_markers = compute_redundancy_markers(results_json)
    clusters = compute_clusters(results_json)
    # Try to stabilise ordinations (PCoA) using a seed, if provided
    params_block = results_json.get("parameters") or {}
    meta_params = results_metadata.get("parameters") if isinstance(results_metadata, dict) else {}
    seed_val = (
        results_json.get("seed")
        or results_json.get("random_seed")
        or params_block.get("seed")
        or meta_params.get("seed")
        or merged_metadata.get("seed")
        or merged_metadata.get("random_seed")
        or merged_metadata.get("parameters", {}).get("seed")
    )
    try:
        seed_val = int(seed_val)
    except Exception:
        seed_val = None

    ordinations = compute_ordinations(clusters, seed=seed_val)
    total_reads_all = compute_total_reads_all(results_json)

    recommendations = compute_recommendations({
        "screening_overview": screening_overview,
            "sequencing_quality": low_quality,
        "prokaryotic_fraction": prok_fraction,
        "redundancy_reads": redundancy_reads,
        "redundancy_markers": redundancy_markers,
        "clusters": clusters,
    })

    meta: Dict[str, Any] = {
        "n_samples_in_results": int(results_json.get("n_samples", 0)),
        "metadata": merged_metadata,
        "all_samples": results_json.get("all_samples"),
    }

    all_samples_markers = results_json.get("all_samples_markers")
    all_samples_reads = results_json.get("all_samples_reads")
    overall_prok_coverage = None
    if isinstance(all_samples_markers, dict):
        comp_target = merged_metadata.get("parameters", {}).get("completeness")
        try:
            comp_target = float(comp_target)
        except Exception:
            comp_target = 95.0

        coverage_total = all_samples_markers.get("C_total")
        if isinstance(coverage_total, str):
            try:
                coverage_total = float(coverage_total)
            except ValueError:
                coverage_total = None

        coverage_pct = coverage_total * 100 if coverage_total is not None else None

        if coverage_pct is None:
            flag_overall = 3
            msg_overall = "Overall marker coverage could not be assessed from all_samples Nonpareil output."
        else:
            if coverage_pct >= comp_target:
                flag_overall = 1
                msg_overall = (
                    f"Overall marker coverage meets the {comp_target:.0f}% completeness target "
                    f"({coverage_pct:.1f}%)."
                )
            elif coverage_pct >= 0.8 * comp_target:
                flag_overall = 2
                msg_overall = (
                    f"Overall marker coverage is within 20% of the {comp_target:.0f}% completeness target "
                    f"({coverage_pct:.1f}%)."
                )
            else:
                flag_overall = 3
                msg_overall = (
                    f"Overall marker coverage is below 80% of the {comp_target:.0f}% completeness target "
                    f"({coverage_pct:.1f}%)."
                )

        overall_prok_coverage = {
            "sample": all_samples_markers.get("sample"),
            "C_total": all_samples_markers.get("C_total"),
            "coverage_total": all_samples_markers.get("C_total"),
            "coverage_percent": coverage_pct,
            "subset_reads": all_samples_markers.get("subset_reads"),
            "total_reads": all_samples_markers.get("total_reads"),
            "lr_95_reads": (
                all_samples_markers.get("targets", {}).get("95", {}).get("LR_reads")
                if isinstance(all_samples_markers.get("targets"), dict)
                else None
            ),
            "flag_overall_prok_coverage": flag_overall,
            "message_overall_prok_coverage": msg_overall,
        }

    overall_read_coverage = None
    if isinstance(all_samples_reads, dict):
        comp_target = merged_metadata.get("parameters", {}).get("completeness")
        try:
            comp_target = float(comp_target)
        except Exception:
            comp_target = 95.0

        coverage_total = all_samples_reads.get("C_total")
        if isinstance(coverage_total, str):
            try:
                coverage_total = float(coverage_total)
            except ValueError:
                coverage_total = None

        coverage_pct = coverage_total * 100 if coverage_total is not None else None

        if coverage_pct is None:
            flag_overall_reads = 3
            msg_reads = "Overall metagenomic coverage could not be assessed from pooled read Nonpareil output."
        else:
            if coverage_pct >= comp_target:
                flag_overall_reads = 1
                msg_reads = (
                    f"Pooled metagenomic coverage meets the {comp_target:.0f}% completeness target "
                    f"({coverage_pct:.1f}%)."
                )
            elif coverage_pct >= 0.8 * comp_target:
                flag_overall_reads = 2
                msg_reads = (
                    f"Pooled metagenomic coverage is within 20% of the {comp_target:.0f}% completeness target "
                    f"({coverage_pct:.1f}%)."
                )
            else:
                flag_overall_reads = 3
                msg_reads = (
                    f"Pooled metagenomic coverage is below 80% of the {comp_target:.0f}% completeness target "
                    f"({coverage_pct:.1f}%)."
                )

        overall_read_coverage = {
            "sample": all_samples_reads.get("sample"),
            "C_total": all_samples_reads.get("C_total"),
            "coverage_total": all_samples_reads.get("C_total"),
            "coverage_percent": coverage_pct,
            "subset_reads": all_samples_reads.get("subset_reads"),
            "total_reads": all_samples_reads.get("total_reads"),
            "lr_95_reads": (
                all_samples_reads.get("targets", {}).get("95", {}).get("LR_reads")
                if isinstance(all_samples_reads.get("targets"), dict)
                else None
            ),
            "flag_overall_read_coverage": flag_overall_reads,
            "message_overall_read_coverage": msg_reads,
        }

    overall_combined_coverage = None
    if overall_read_coverage or overall_prok_coverage:
        message_parts: List[str] = []
        combined_flags: List[int] = []
        if overall_read_coverage:
            msg = overall_read_coverage.get("message_overall_read_coverage")
            if msg:
                message_parts.append(msg)
            fr = overall_read_coverage.get("flag_overall_read_coverage")
            if isinstance(fr, int):
                combined_flags.append(fr)
        if overall_prok_coverage:
            msg = overall_prok_coverage.get("message_overall_prok_coverage")
            if msg:
                message_parts.append(msg)
            fm = overall_prok_coverage.get("flag_overall_prok_coverage")
            if isinstance(fm, int):
                combined_flags.append(fm)

        if not combined_flags:
            combined_flag = 3
        elif any(f == 3 for f in combined_flags):
            combined_flag = 3
        elif any(f == 2 for f in combined_flags):
            combined_flag = 2
        else:
            combined_flag = 1

        overall_combined_coverage = {
            "metagenomic": overall_read_coverage,
            "prokaryotic": overall_prok_coverage,
            "flag_overall_coverage": combined_flag,
            "message_overall_coverage": " ".join(message_parts).strip(),
        }

    distilled: Dict[str, Any] = {
        "meta": meta,
        "summary": {
            "screening_overview": screening_overview,
            "sequencing_quality": low_quality,
            "prokaryotic_fraction": prok_fraction,
            "redundancy_reads": redundancy_reads,
            "redundancy_markers": redundancy_markers,
            "clusters": clusters,
            "ordinations": ordinations,
            # aggregate total reads across all samples
            "total_reads_all_samples": total_reads_all,
            "recommendations": recommendations,
            "overall_prokaryotic_coverage": overall_prok_coverage,
            "overall_metagenomic_coverage": overall_read_coverage,
            "overall_coverage_summary": overall_combined_coverage,
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(distilled, f, indent=2)


if __name__ == "__main__":
    main()
