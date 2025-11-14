#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics as stats


# ---------------------------------------------------------
# Normalise sample names
# ---------------------------------------------------------
def clean_sample_name(name: str) -> str:
    """
    Normalise Mash sample names by:
    - Removing directories
    - Removing ALL extensions (.fna, .fa, .fastq.gz, .fq.gz, .msh, etc.)

    Example:
      /path/to/Sample10_1.fastq.gz -> Sample10_1
      Sample2.fna                  -> Sample2
    """
    return Path(name).stem


# ---------------------------------------------------------
# Parse clusters
# ---------------------------------------------------------
def parse_clusters(path: Path) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    sample_to_cluster: Dict[str, str] = {}
    cluster_to_samples: Dict[str, List[str]] = {}

    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                continue

            # Skip header lines
            if parts[0].lower() in ("sample", "genome") or parts[1].lower().startswith("cluster"):
                continue

            raw_sample, cluster = parts[0], parts[1]
            sample = clean_sample_name(raw_sample)

            sample_to_cluster[sample] = cluster
            cluster_to_samples.setdefault(cluster, []).append(sample)

    return sample_to_cluster, cluster_to_samples


# ---------------------------------------------------------
# Parse Mash distances
# ---------------------------------------------------------
def parse_mash_dist(
    path: Path,
    sample_to_cluster: Dict[str, str],
) -> Tuple[
    List[Dict[str, Any]],
    List[float],
    Dict[str, List[float]],
    Dict[Tuple[str, str], List[float]],
]:
    """
    Parse Mash .dist-like file and collect:

      - pairwise entries (list of dicts)
      - all distances (list of float)
      - distances per cluster (cluster_id -> list of float),
        only for pairs whose two samples are in the same cluster
      - distances between clusters ( (c1,c2) -> list of float ),
        for c1 != c2 (using sorted cluster pair keys)

    Expected format per line (tab-separated):
      ref<TAB>query<TAB>distance<TAB>p-value<TAB>shared-hashes
    """

    pairwise: List[Dict[str, Any]] = []
    all_distances: List[float] = []
    within_distances: Dict[str, List[float]] = {}
    between_distances: Dict[Tuple[str, str], List[float]] = {}

    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 3:
                continue

            raw_ref = parts[0]
            raw_query = parts[1]
            dist_str = parts[2]
            p_val_str = parts[3] if len(parts) > 3 else None
            shared_hashes = parts[4] if len(parts) > 4 else None

            # CLEAN sample names
            ref = clean_sample_name(raw_ref)
            query = clean_sample_name(raw_query)

            if ref == query:
                continue

            try:
                dist = float(dist_str)
            except ValueError:
                continue

            entry: Dict[str, Any] = {
                "sample1": ref,
                "sample2": query,
                "distance": dist,
            }

            if p_val_str:
                try:
                    entry["p_value"] = float(p_val_str)
                except ValueError:
                    pass

            if shared_hashes is not None:
                entry["shared_hashes"] = shared_hashes

            pairwise.append(entry)
            all_distances.append(dist)

            c1 = sample_to_cluster.get(ref)
            c2 = sample_to_cluster.get(query)

            # Within-cluster distances
            if c1 is not None and c1 == c2:
                within_distances.setdefault(c1, []).append(dist)

            # Between clusters
            if c1 is not None and c2 is not None and c1 != c2:
                key = tuple(sorted((c1, c2)))
                between_distances.setdefault(key, []).append(dist)

    return pairwise, all_distances, within_distances, between_distances


# ---------------------------------------------------------
# Summary stats helper
# ---------------------------------------------------------
def summarize_distances(distances: List[float]) -> Dict[str, Any]:
    if not distances:
        return {
            "n_pairs": 0,
            "mean_distance": None,
            "median_distance": None,
        }
    return {
        "n_pairs": len(distances),
        "mean_distance": stats.mean(distances),
        "median_distance": stats.median(distances),
    }


# ---------------------------------------------------------
# Between / within cluster structure summary
# ---------------------------------------------------------
def compute_structure_summary(
    clusters_summary: Dict[str, Any],
    between_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Given:
      clusters_summary: {
        "C0": {"mean_distance": ...},
        "C1": {"mean_distance": ...},
        ...
      }

      between_summary: {
        "C0__vs__C1": {"clusters": ["C0","C1"], "mean_distance": ...},
        ...
      }

    Compute:
      - mean & sd of within-cluster mean distances
      - mean & sd of between-cluster mean distances
      - global ratio: mean_between / mean_within
      - per-pair ratios: between_mean / ((within_c1 + within_c2)/2), with mean & sd
    """
    within_means: List[float] = []
    within_by_cluster: Dict[str, float] = {}

    for cid, info in clusters_summary.items():
        m = info.get("mean_distance")
        if isinstance(m, (int, float)):
            val = float(m)
            within_means.append(val)
            within_by_cluster[str(cid)] = val

    between_means: List[float] = []
    pair_ratios: List[float] = []

    for _, info in between_summary.items():
        m = info.get("mean_distance")
        if not isinstance(m, (int, float)):
            continue
        m_val = float(m)
        between_means.append(m_val)

        cl = info.get("clusters") or []
        if isinstance(cl, list) and len(cl) == 2:
            c1, c2 = str(cl[0]), str(cl[1])
            w1 = within_by_cluster.get(c1)
            w2 = within_by_cluster.get(c2)
            if isinstance(w1, (int, float)) and isinstance(w2, (int, float)) and w1 > 0 and w2 > 0:
                denom = 0.5 * (float(w1) + float(w2))
                if denom > 0:
                    pair_ratios.append(m_val / denom)

    if within_means:
        mean_within = stats.mean(within_means)
        sd_within = stats.pstdev(within_means) if len(within_means) > 1 else 0.0
    else:
        mean_within = None
        sd_within = None

    if between_means:
        mean_between = stats.mean(between_means)
        sd_between = stats.pstdev(between_means) if len(between_means) > 1 else 0.0
    else:
        mean_between = None
        sd_between = None

    if mean_within and mean_within > 0 and mean_between is not None:
        ratio_global = mean_between / mean_within
    else:
        ratio_global = None

    if pair_ratios:
        ratio_pairs_mean = stats.mean(pair_ratios)
        ratio_pairs_sd = stats.pstdev(pair_ratios) if len(pair_ratios) > 1 else 0.0
    else:
        ratio_pairs_mean = None
        ratio_pairs_sd = None

    return {
        "n_clusters": len(within_means),
        "n_between_pairs": len(between_means),
        "mean_within_distance": mean_within,
        "sd_within_distance": sd_within,
        "mean_between_distance": mean_between,
        "sd_between_distance": sd_between,
        "ratio_between_over_within": ratio_global,
        "pair_ratio_mean": ratio_pairs_mean,
        "pair_ratio_sd": ratio_pairs_sd,
    }


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description=(
            "Create a JSON summary from Mash pairwise distances and clusters.\n"
            "Sample names are cleaned (paths + extensions removed), and a between/within\n"
            "cluster separation metric is calculated."
        )
    )

    ap.add_argument(
        "--dist",
        required=True,
        help="Mash pairwise distance file.",
    )
    ap.add_argument(
        "--clusters",
        required=True,
        help="Cluster TSV: sample<TAB>cluster",
    )
    ap.add_argument(
        "--kind",
        choices=["markers", "reads"],
        default="markers",
        help="Use 'markers' or 'reads' as top-level key (mash_markers or mash_reads).",
    )
    ap.add_argument(
        "-o", "--output",
        required=True,
        help="Output JSON file.",
    )
    args = ap.parse_args()

    dist_path = Path(args.dist)
    clusters_path = Path(args.clusters)
    out_path = Path(args.output)

    sample_to_cluster, cluster_to_samples = parse_clusters(clusters_path)

    pairwise, all_distances, within_distances, between_distances = parse_mash_dist(
        dist_path, sample_to_cluster
    )

    overall_summary = summarize_distances(all_distances)

    # Within-cluster summaries
    clusters_summary: Dict[str, Any] = {}
    for cid, members in cluster_to_samples.items():
        d = within_distances.get(cid, [])
        clusters_summary[cid] = {
            "members": sorted(members),
            "n_members": len(members),
            **summarize_distances(d),
        }

    # Between-cluster summaries
    between_summary: Dict[str, Any] = {}
    for (c1, c2), dists in between_distances.items():
        key = f"{c1}__vs__{c2}"
        between_summary[key] = {
            "clusters": [c1, c2],
            **summarize_distances(dists),
        }

    # Between/within cluster structure metric
    structure_summary = compute_structure_summary(clusters_summary, between_summary)

    top_key = f"mash_{args.kind}"

    mash_json: Dict[str, Any] = {
        top_key: {
            "pairwise": pairwise,
            "summary": {
                "overall": overall_summary,
                "clusters": clusters_summary,
                "between_clusters": between_summary,
                "structure": structure_summary,
            },
        }
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(mash_json, f, indent=2)

    print(f"[✓] Wrote Mash {args.kind} summary → {out_path}")


if __name__ == "__main__":
    main()
