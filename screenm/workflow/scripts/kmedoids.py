#!/usr/bin/env python3
"""
cluster_mash_pam.py — Pure-Python K-Medoids (PAM) clustering on a Mash distance matrix,
with silhouette-based selection of the best k. No scikit-learn(-extra), no scipy required.

Input:  square TSV (header row, first column sample ids) with Mash distances.
Outputs (configurable via CLI):
  - silhouettes table (k vs. silhouette)
  - assignments table (Sample, Cluster)
  - medoids table (Cluster, Medoid_Sample)
"""

import argparse
import math
from typing import Tuple, List

import numpy as np
import pandas as pd


def read_distance_matrix(path: str) -> Tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_csv(path, sep="\t", header=0, index_col=0)
    D = df.values.astype(float)
    # enforce symmetry & zero diagonal (Mash is symmetric but just to be safe)
    np.fill_diagonal(D, 0.0)
    D = 0.5 * (D + D.T)
    return df, D


def silhouette_precomputed(D: np.ndarray, labels: np.ndarray) -> float:
    """Compute average silhouette score from a precomputed distance matrix D."""
    n = D.shape[0]
    s = np.zeros(n, dtype=float)
    for i in range(n):
        li = labels[i]
        in_cluster = (labels == li)
        # a(i): mean intra-cluster distance (excluding self)
        if np.sum(in_cluster) > 1:
            a = np.sum(D[i, in_cluster]) / (np.sum(in_cluster) - 1)
        else:
            # singleton cluster: silhouette 0 by convention
            s[i] = 0.0
            continue
        # b(i): lowest mean distance to other clusters
        b = math.inf
        for l in np.unique(labels):
            if l == li:
                continue
            mask = (labels == l)
            if np.any(mask):
                b = min(b, np.mean(D[i, mask]))
        s[i] = 0.0 if (a == 0 and b == 0) else (b - a) / max(a, b)
    # if only 1 cluster or all singletons, silhouette is undefined → 0
    if len(np.unique(labels)) < 2:
        return 0.0
    return float(np.mean(s))


def init_medoids_kpp(D: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """k-medoids++ style initialization on distances."""
    n = D.shape[0]
    medoids = np.empty(k, dtype=int)
    medoids[0] = rng.integers(0, n)
    # distance to nearest selected medoid
    d2 = np.min(D[:, [medoids[0]]], axis=1)
    for t in range(1, k):
        # probabilities proportional to distance (not squared) to nearest medoid
        prob = d2 / (d2.sum() + 1e-12)
        medoids[t] = rng.choice(n, p=prob)
        d2 = np.minimum(d2, D[:, medoids[t]])
    return np.unique(medoids) if len(np.unique(medoids)) == k else init_medoids_kpp(D, k, rng)


def assign_to_medoids(D: np.ndarray, medoids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return (labels, dist_to_nearest) given current medoids."""
    # compute distances to each medoid and take argmin
    dist_to_medoids = D[:, medoids]
    labels = medoids[np.argmin(dist_to_medoids, axis=1)]
    dmin = np.min(dist_to_medoids, axis=1)
    return labels, dmin


def pam_once(
    D: np.ndarray,
    k: int,
    rng: np.random.Generator,
    max_iter: int = 100
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Run one PAM (Partitioning Around Medoids) optimization:
    - init medoids (k-medoids++ style),
    - alternate assignment and best swap until no improvement.
    Returns: (labels, medoids, total_cost)
    """
    n = D.shape[0]
    medoids = init_medoids_kpp(D, k, rng)
    labels, dmin = assign_to_medoids(D, medoids)
    cost = float(dmin.sum())

    for _ in range(max_iter):
        improved = False
        # Precompute for speed
        in_medoids = np.zeros(n, dtype=bool)
        in_medoids[medoids] = True
        # For each medoid m and non-medoid h, compute cost change if swap
        best_delta = 0.0
        best_swap = None
        for mi, m in enumerate(medoids):
            # distances to this medoid
            dm = D[:, m]
            # For all candidate h not a medoid
            for h in np.where(~in_medoids)[0]:
                dh = D[:, h]
                # Compute second-best efficiently:
                # For points i where current nearest medoid is m, we need
                # the best distance to other medoids.
                # Precompute distances to all other medoids (excluding m).
                others = np.delete(medoids, mi)
                if others.size > 0:
                    d_to_others = np.min(D[:, others], axis=1)
                else:
                    d_to_others = np.full(n, np.inf)

                # For each point:
                # case1: labels[i] == m → newd = min(dh[i], d_to_others[i])
                # case2: labels[i] != m → newd = min(dmin[i], dh[i])
                same = (labels == m)
                newd = np.where(same, np.minimum(dh, d_to_others), np.minimum(dmin, dh))
                delta = float(newd.sum() - cost)
                if delta < best_delta:
                    best_delta = delta
                    best_swap = (mi, h, d_to_others)  # cache second-best for reuse
        if best_swap is None:
            break  # no improving swap
        # Apply best swap
        mi, h, d_to_others = best_swap
        m_old = medoids[mi]
        medoids[mi] = h
        in_medoids[m_old] = False
        in_medoids[h] = True
        # Reassign with updated medoids
        labels, dmin = assign_to_medoids(D, medoids)
        cost = float(dmin.sum())
        improved = True
        if not improved:
            break

    # Convert labels from medoid ids to 0..k-1 cluster ids
    # Map medoid index -> cluster id
    medoid_to_cluster = {m: ci for ci, m in enumerate(medoids)}
    cluster_labels = np.array([medoid_to_cluster[l] for l in labels], dtype=int)
    return cluster_labels, medoids, cost


def pam_best_of_n(
    D: np.ndarray,
    k: int,
    n_init: int,
    seed: int,
    max_iter: int = 100
) -> Tuple[np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(seed)
    best: Tuple[np.ndarray, np.ndarray, float] | None = None
    for t in range(n_init):
        labels, medoids, cost = pam_once(D, k, rng, max_iter=max_iter)
        if best is None or cost < best[2]:
            best = (labels, medoids, cost)
    return best  # type: ignore[return-value]


def main():
    ap = argparse.ArgumentParser(
        description="Pure-Python K-Medoids (PAM) on Mash distances with silhouette-based k selection."
    )
    ap.add_argument(
        "-i", "--infile", required=True,
        help="Mash distance matrix (TSV; square, header+index)."
    )
    ap.add_argument(
        "-o", "--out", default="mash_pam",
        help="Output prefix [default: mash_pam]."
    )

    # Explicit, predictable outputs (no k in the filename unless you specify it)
    ap.add_argument(
        "--silhouettes-out", default=None,
        help="Output TSV for k vs silhouette "
             "(default: <out>_silhouettes.tsv)."
    )
    ap.add_argument(
        "--assignments-out", default=None,
        help="Output TSV for sample-to-cluster assignments "
             "(default: <out>_assignments.tsv)."
    )
    ap.add_argument(
        "--medoids-out", default=None,
        help="Output TSV for medoids "
             "(default: <out>_medoids.tsv)."
    )

    ap.add_argument(
        "--kmin", type=int, default=2,
        help="Minimum k to test [default: 2]."
    )
    ap.add_argument(
        "--kmax", type=int, default=15,
        help="Maximum k to test [default: 15]."
    )
    ap.add_argument(
        "--n-init", type=int, default=5,
        help="Number of random initializations per k [default: 5]."
    )
    ap.add_argument(
        "--max-iter", type=int, default=100,
        help="Max PAM iterations per init [default: 100]."
    )
    ap.add_argument(
        "--seed", type=int, default=1,
        help="Random seed [default: 1]."
    )
    args = ap.parse_args()

    df, D = read_distance_matrix(args.infile)
    n = D.shape[0]
    kmax = max(args.kmin, min(args.kmax, n - 1))

    results: List[Tuple[int, float]] = []
    best_k: int | None = None
    best_sil = -1.0
    best_labels: np.ndarray | None = None
    best_medoids: np.ndarray | None = None

    print(f"[INFO] Testing k={args.kmin}..{kmax} on n={n} samples (pure Python PAM) ...")
    for k in range(args.kmin, kmax + 1):
        labels, medoids, cost = pam_best_of_n(
            D,
            k,
            n_init=args.n_init,
            seed=args.seed,
            max_iter=args.max_iter,
        )
        sil = silhouette_precomputed(D, labels)
        results.append((k, sil))
        print(f"  k={k:<2d} | silhouette={sil:.4f} | cost={cost:.3f}")
        if sil > best_sil:
            best_sil = sil
            best_k = k
            best_labels = labels
            best_medoids = medoids

    # Decide final output paths; all fully predictable and do NOT depend on k
    sil_path = args.silhouettes_out or f"{args.out}_silhouettes.tsv"
    assign_path = args.assignments_out or f"{args.out}_assignments.tsv"
    medoid_path = args.medoids_out or f"{args.out}_medoids.tsv"

    # Save silhouettes
    sil_df = pd.DataFrame(results, columns=["k", "silhouette"])
    sil_df.to_csv(sil_path, sep="\t", index=False)

    # Save best assignments
    if best_labels is None or best_medoids is None or best_k is None:
        raise RuntimeError("No valid clustering found; check k range and input matrix.")

    assign_df = pd.DataFrame({
        "Sample": df.index,
        "Cluster": best_labels,
    })
    assign_df.to_csv(assign_path, sep="\t", index=False)

    # Save medoids
    medoid_names = [df.index[i] for i in best_medoids]
    medoid_df = pd.DataFrame({
        "Cluster": range(best_k),
        "Medoid_Sample": medoid_names,
    })
    medoid_df.to_csv(medoid_path, sep="\t", index=False)

    print("\n[✓] Done.")
    print(f"    Best k: {best_k} (silhouette={best_sil:.4f})")
    print(f"    Wrote: {sil_path}, {assign_path}, {medoid_path}")


if __name__ == "__main__":
    main()
