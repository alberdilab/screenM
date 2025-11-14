#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics as stats


def parse_clusters(path: Path) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """
    Parse cluster file (TSV) with at least two columns:
      sample_id<TAB>cluster_id

    Returns:
      sample_to_cluster: {sample -> cluster}
      cluster_to_samples: {cluster -> [samples]}
    """
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

            # Skip header-like lines
            if parts[0].lower() in ("sample", "genome") or parts[1].lower().startswith("cluster"):
                continue

            sample, cluster = parts[0], parts[1]
            sample_to_cluster[sample] = cluster
            cluster_to_samples.setdefault(cluster, []).append(sample)

    return sample_to_cluster, cluster_to_samples


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
    Parse Mash .dist file and collect:

      - pairwise entries (list of dicts)
      - all distances (list of float)
      - distances per cluster (cluster_id -> list of float),
        only for pairs whose two samples are in the same cluster
      - distances between clusters ( (c1,c2) -> list of float ),
        for c1 != c2 (using sorted cluster pair keys)

    Assumes Mash format:
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

            ref = parts[0]
            query = parts[1]
            dist_str = parts[2]
            p_val_str = parts[3] if len(parts) > 3 else None
            shared_hashes = parts[4] if len(parts) > 4 else None

            # skip self distances if present
            if ref == query:
                continue

            try:
                dist = float(dist_str)
            except ValueError:
                continue

            p_val = None
            if p_val_str is not None:
                try:
                    p_val = float(p_val_str)
                except ValueError:
                    p_val = None

            entry: Dict[str, Any] = {
                "sample1": ref,
                "sample2": query,
                "distance": dist,
            }
            if p_val is not None:
                entry["p_value"] = p_val
            if shared_hashes is not None:
                entry["shared_hashes"] = shared_hashes

            pairwise.append(entry)
            all_distances.append(dist)

            c1 = sample_to_cluster.get(ref)
            c2 = sample_to_cluster.get(query)

            # Within-cluster distances
            if c1 is not None and c1 == c2:
                within_distances.setdefault(c1, []).append(dist)

            # Between-cluster distances
            if c1 is not None and c2 is not None and c1 != c2:
                pair_key = tuple(sorted((c1, c2)))
                between_distances.setdefault(pair_key, []).append(dist)

    return pairwise, all_distances, within_distances, between_distances


def summarize_distances(distances: List[float]) -> Dict[str, Any]:
    """
    Compute basic summary statistics for a list of distances.
    Returns: n_pairs, mean_distance, median_distance.
    """
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


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Create a JSON summary from Mash pairwise distances and cluster assignments.\n"
            "Keeps all pairwise distances and computes average distance overall, within clusters, "
            "and between clusters."
        )
    )
    ap.add_argument(
        "--dist",
        required=True,
        help="Mash pairwise distance file (e.g. mash_markers.dist or mash_reads.dist).",
    )
    ap.add_argument(
        "--clusters",
        required=True,
        help="Cluster file (TSV) with columns: sample_id<TAB>cluster_id (e.g. mash_markers.tsv).",
    )
    ap.add_argument(
        "--kind",
        choices=["markers", "reads"],
        default="markers",
        help="Type of Mash data: 'markers' (default) or 'reads'. Used to name the top-level key.",
    )
    ap.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output JSON file to write Mash summary.",
    )
    args = ap.parse_args()

    dist_path = Path(args.dist)
    clusters_path = Path(args.clusters)
    out_path = Path(args.output)

    # Parse cluster info
    sample_to_cluster, cluster_to_samples = parse_clusters(clusters_path)

    # Parse Mash distances and collect within- and between-cluster distances
    pairwise, all_distances, within_distances, between_distances = parse_mash_dist(
        dist_path, sample_to_cluster
    )

    # Overall summary
    overall_summary = summarize_distances(all_distances)

    # Within-cluster summaries
    clusters_summary: Dict[str, Any] = {}
    for cluster_id, members in cluster_to_samples.items():
        dists = within_distances.get(cluster_id, [])
        clusters_summary[cluster_id] = {
            "members": sorted(members),
            "n_members": len(members),
            **summarize_distances(dists),
        }

    # Between-cluster summaries
    between_summary: Dict[str, Any] = {}
    for (c1, c2), dists in between_distances.items():
        key = f"{c1}__vs__{c2}"
        between_summary[key] = {
            "clusters": [c1, c2],
            **summarize_distances(dists),
        }

    top_key = f"mash_{args.kind}"

    mash_json: Dict[str, Any] = {
        top_key: {
            "pairwise": pairwise,
            "summary": {
                "overall": overall_summary,
                "clusters": clusters_summary,          # within-cluster
                "between_clusters": between_summary,   # between-cluster
            },
        }
    }

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        json.dump(mash_json, fh, indent=2)

if __name__ == "__main__":
    main()
