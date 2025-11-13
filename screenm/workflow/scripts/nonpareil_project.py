#!/usr/bin/env python3
from pathlib import Path
import math, json, numpy as np, pandas as pd
from typing import Dict, Any, Tuple, Optional, List

# ---------- Parsing ----------

def parse_nonpareil_headers(npo_path: Path) -> Dict[str, Any]:
    headers = {}
    with npo_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("# @"):
                body = line[3:].strip()
                if ":" in body:
                    key, val = body.split(":", 1)
                    headers[key.strip()] = val.strip()
            if not line.startswith("#"):
                break
    for k in ["L","AL","R","overlap","ksize","divide","logsampling"]:
        if k in headers:
            try:
                headers[k] = float(headers[k])
            except Exception:
                pass
    return headers

def coverage_factor(overlap: float) -> float:
    # same as Nonpareil R: 1 - exp(2.23E-2 * overlap - 3.5698)
    return 1.0 - math.exp(2.23e-2 * overlap - 3.5698)

def read_npo_table(npo_path: Path) -> pd.DataFrame:
    rows = []
    with npo_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                rows.append([float(x) for x in parts[:6]])
    if not rows:
        raise ValueError("No tabular data found in .npo file.")
    df = pd.DataFrame(rows, columns=["x_obs","y_red","y_sd","y_p25","y_p50","y_p75"])
    df = df.sort_values("x_obs").reset_index(drop=True)
    return df

# ---------- Model prep ----------

def prepare_curve(df: pd.DataFrame, headers: Dict[str, Any],
                  correction_factor_on: bool, subset_reads: float):
    # kernel & overlap
    kernel = "alignment"
    if "ksize" in headers and isinstance(headers["ksize"], (int, float)) and 0 < headers["ksize"] < 1001:
        kernel = "kmer"
    overlap = 50.0 if kernel == "kmer" else float(headers.get("overlap", 0.0))
    cor_f = coverage_factor(overlap) if correction_factor_on else 1.0

    # redundancy -> coverage correction (raise to cor_f)
    df_corr = df.copy()
    for col in ["y_red","y_sd","y_p25","y_p50","y_p75"]:
        df_corr[col] = df_corr[col] ** cor_f

    # DROP rows with x_obs <= 0 — and keep both X and Y aligned
    mask_pos = df["x_obs"].values > 0
    if not np.any(mask_pos):
        raise ValueError("All x_obs values are <= 0; cannot fit model.")
    x_obs = df.loc[mask_pos, "x_obs"].to_numpy()
    y_cov = df_corr.loc[mask_pos, "y_red"].to_numpy()

    # Subset metrics (still safe to read from the last row of full table)
    kappa_subset = float(df["y_red"].iloc[-1])
    C_subset     = float(df_corr["y_red"].iloc[-1])

    # x_adj in bp (safe)
    logx = np.log(x_obs)
    maxlogx = np.max(logx)
    x_adj = np.exp(maxlogx + (C_subset ** 0.27) * (logx - maxlogx))

    # scale to AL * subset_reads
    AL = float(headers.get("AL", headers.get("L", 0.0)) or 0.0)
    if AL <= 0:
        raise ValueError("AL/L header is zero or missing; cannot convert reads to bp.")
    x_adj = x_adj * AL * float(subset_reads) / np.max(x_adj)

    return {"AL": AL, "cor_f": cor_f, "x_adj": x_adj,
            "y_cov": y_cov, "kappa_subset": kappa_subset, "C_subset": C_subset}

def pgamma_log1p_x(x_bp, a, b):
    """Gamma CDF with argument log1p(x), shape=a, rate=b (scale=1/b)."""
    try:
        from scipy.stats import gamma as sp_gamma
        return sp_gamma.cdf(np.log1p(x_bp), a=a, scale=1.0/b)
    except Exception:
        # fallback: logistic-like surrogate in log-space
        z = np.log1p(x_bp)
        center = (max(1e-6, a-1.0)) / max(1e-6, b)
        slope  = max(1e-6, b)
        return 1.0 / (1.0 + np.exp(-(z - center) * slope))

def fit_gamma_model(x_bp: np.ndarray, y_cov: np.ndarray) -> Tuple[float,float]:
    # lengths must match
    if x_bp.shape[0] != y_cov.shape[0]:
        n = min(x_bp.shape[0], y_cov.shape[0])
        x_bp = x_bp[:n]
        y_cov = y_cov[:n]

    sel = (y_cov > 0) & (y_cov < 0.9)
    x = x_bp[sel]
    y = y_cov[sel]
    if x.size < 5:
        # fall back to defaults if not enough points in (0,0.9)
        return 1.0, 0.1

    try:
        from scipy.optimize import curve_fit
        def f(xx, a, b): return pgamma_log1p_x(xx, a, b)
        popt, _ = curve_fit(f, x, y, p0=[1.0,0.1],
                            bounds=([1e-6,1e-6],[100,100]), maxfev=20000)
        return float(popt[0]), float(popt[1])
    except Exception:
        a_grid = np.geomspace(0.5, 10, 20)
        b_grid = np.geomspace(0.01, 2, 20)
        best = (1, 0.1, 1e9)
        for a in a_grid:
            for b in b_grid:
                err = np.mean((pgamma_log1p_x(x,a,b)-y)**2)
                if err < best[2]:
                    best = (a,b,err)
        return best[0], best[1]


# ---------- Effort (LR*) for target coverage ----------

def effort_for_coverage(target_cov: float, a: float, b: float,
                        hi_start: float = 1e6, hi_cap: float = 1e15) -> float:
    """
    Find x_bp such that pgamma_log1p_x(x_bp, a, b) ~= target_cov using monotonic bisection.
    Expands the upper bound until f(hi) >= target or hits hi_cap.
    """
    target = float(np.clip(target_cov, 1e-9, 0.999999))  # avoid exact 0 or 1
    lo, hi = 0.0, hi_start
    # expand hi until we bracket the target
    f_hi = pgamma_log1p_x(np.array([hi]), a, b)[0]
    while f_hi < target and hi < hi_cap:
        hi *= 2.0
        f_hi = pgamma_log1p_x(np.array([hi]), a, b)[0]
    if hi >= hi_cap and f_hi < target:
        return float("inf")  # effectively unreachable under current model

    # bisection
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = pgamma_log1p_x(np.array([mid]), a, b)[0]
        if f_mid < target:
            lo = mid
        else:
            hi = mid
    return hi

# ---------- CLI ----------

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Estimate Nonpareil κ and C for subset and projected total; optionally compute LR* for target coverages."
    )
    ap.add_argument("npo_file", help=".npo file from Nonpareil subset run (e.g. 1M reads)")
    ap.add_argument("--subset-reads", type=float, required=True,
                    help="Number of reads used for Nonpareil run (subset)")
    ap.add_argument("--total-reads", type=float, required=True,
                    help="Total reads in dataset to project to")
    ap.add_argument("--targets", type=str, default="95",
                    help="Comma-separated target coverages in percent (e.g., '95,99,100'). Default: 95")
    ap.add_argument("--no-correction", action="store_true",
                    help="Disable overlap-based correction factor")
    ap.add_argument("-o", "--out", default="nonpareil_projection.tsv",
                    help="Output TSV filename")
    args = ap.parse_args()

    headers = parse_nonpareil_headers(Path(args.npo_file))
    df = read_npo_table(Path(args.npo_file))
    prep = prepare_curve(df, headers, not args.no_correction, args.subset_reads)

    # Fit coverage model on subset
    a, b = fit_gamma_model(prep["x_adj"], prep["y_cov"])

    # Project total
    AL = prep["AL"]
    LR_total = AL * args.total_reads
    C_total = float(np.clip(pgamma_log1p_x(np.array([LR_total]), a, b)[0], 0, 1))
    cor_f = prep["cor_f"]
    kappa_total = float(np.clip(C_total ** (1.0 / cor_f), 0, 1))

    # Build header and row
    cols = ["subset_reads","total_reads","kappa_subset","C_subset","kappa_total","C_total"]
    row  = [args.subset_reads, args.total_reads,
            f"{prep['kappa_subset']:.6f}", f"{prep['C_subset']:.6f}",
            f"{kappa_total:.6f}", f"{C_total:.6f}"]

    # LR* for targets
    targets_pct = [t.strip() for t in args.targets.split(",") if t.strip()]
    for t in targets_pct:
        try:
            pct = float(t)
        except ValueError:
            continue
        y = min(max(pct/100.0, 1e-9), 0.999999)  # safe [0,1)
        lr_bp = effort_for_coverage(y, a, b)
        if lr_bp == float("inf"):
            lr_reads = float("inf")
        else:
            lr_reads = lr_bp / AL if AL > 0 else float("nan")
        cols += [f"LR_{int(round(pct))}_bp", f"LR_{int(round(pct))}_reads"]
        if math.isfinite(lr_bp):
            row  += [f"{lr_bp:.0f}", f"{lr_reads:.0f}"]
        else:
            row  += ["inf", "inf"]

    # Write TSV
    with open(args.out, "w") as out:
        out.write("\t".join(cols) + "\n")
        out.write("\t".join(map(str, row)) + "\n")

    print(f"[✓] Results written to {args.out}")

if __name__ == "__main__":
    main()
