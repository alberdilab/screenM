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

    kernel = "alignment"
    if "ksize" in headers and isinstance(headers["ksize"], (int, float)) and 0 < headers["ksize"] < 1001:
        kernel = "kmer"
    overlap = 50.0 if kernel == "kmer" else float(headers.get("overlap", 0.0))
    cor_f = coverage_factor(overlap) if correction_factor_on else 1.0

    df_corr = df.copy()
    for col in ["y_red","y_sd","y_p25","y_p50","y_p75"]:
        df_corr[col] = df_corr[col] ** cor_f

    mask_pos = df["x_obs"].values > 0
    if not np.any(mask_pos):
        raise ValueError("All x_obs values ≤ 0.")
    x_obs = df.loc[mask_pos, "x_obs"].to_numpy()
    y_cov = df_corr.loc[mask_pos, "y_red"].to_numpy()

    kappa_subset = float(df["y_red"].iloc[-1])
    C_subset     = float(df_corr["y_red"].iloc[-1])

    logx = np.log(x_obs)
    maxlogx = np.max(logx)
    x_adj = np.exp(maxlogx + (C_subset ** 0.27) * (logx - maxlogx))

    AL = float(headers.get("AL", headers.get("L", 0.0)) or 0.0)
    if AL <= 0:
        raise ValueError("Missing AL/L header.")
    x_adj = x_adj * AL * float(subset_reads) / np.max(x_adj)

    return {"AL": AL, "cor_f": cor_f, "x_adj": x_adj,
            "y_cov": y_cov, "kappa_subset": kappa_subset, "C_subset": C_subset}

def pgamma_log1p_x(x_bp, a, b):
    try:
        from scipy.stats import gamma as sp_gamma
        return sp_gamma.cdf(np.log1p(x_bp), a=a, scale=1.0/b)
    except Exception:
        z = np.log1p(x_bp)
        center = (max(1e-6, a-1.0)) / max(1e-6, b)
        slope  = max(1e-6, b)
        return 1.0 / (1.0 + np.exp(-(z - center) * slope))

def fit_gamma_model(x_bp: np.ndarray, y_cov: np.ndarray) -> Tuple[float,float]:
    if x_bp.shape[0] != y_cov.shape[0]:
        n = min(x_bp.shape[0], y_cov.shape[0])
        x_bp = x_bp[:n]
        y_cov = y_cov[:n]

    sel = (y_cov > 0) & (y_cov < 0.9)
    x = x_bp[sel]
    y = y_cov[sel]
    if x.size < 5:
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
                if err < best[2]: best = (a,b,err)
        return best[0], best[1]

# ---------- LR* computation ----------

def effort_for_coverage(target_cov, a, b, hi_start=1e6, hi_cap=1e15):
    target = float(np.clip(target_cov, 1e-9, 0.999999))
    lo, hi = 0.0, hi_start
    f_hi = pgamma_log1p_x(np.array([hi]), a, b)[0]

    while f_hi < target and hi < hi_cap:
        hi *= 2.0
        f_hi = pgamma_log1p_x(np.array([hi]), a, b)[0]

    if hi >= hi_cap and f_hi < target:
        return float("inf")

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = pgamma_log1p_x(np.array([mid]), a, b)[0]
        if f_mid < target: lo = mid
        else: hi = mid
    return hi

# ---------- CLI ----------

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Estimate Nonpareil κ, C, and LR* using gamma model."
    )

    ap.add_argument("npo_file")
    ap.add_argument("--subset-reads", type=float, required=True)
    ap.add_argument("--total-reads", type=float, required=True)
    ap.add_argument("--targets", type=str, default="95")
    ap.add_argument("--no-correction", action="store_true")

    # NEW: explicit required outputs
    ap.add_argument("--tsv-out", required=True,
                    help="Path to output TSV file (required)")
    ap.add_argument("--json-out", required=True,
                    help="Path to output JSON summary (required)")

    args = ap.parse_args()

    headers = parse_nonpareil_headers(Path(args.npo_file))
    df = read_npo_table(Path(args.npo_file))
    prep = prepare_curve(df, headers, not args.no_correction, args.subset_reads)

    # Fit gamma model
    a, b = fit_gamma_model(prep["x_adj"], prep["y_cov"])

    AL = prep["AL"]
    LR_total = AL * args.total_reads

    C_total = float(np.clip(pgamma_log1p_x(np.array([LR_total]), a, b)[0], 0, 1))
    kappa_total = float(np.clip(C_total ** (1.0 / prep["cor_f"]), 0, 1))

    # --------- Build TSV row ----------
    cols = ["subset_reads","total_reads","kappa_subset","C_subset","kappa_total","C_total"]
    row  = [args.subset_reads, args.total_reads,
            f"{prep['kappa_subset']:.6f}", f"{prep['C_subset']:.6f}",
            f"{kappa_total:.6f}", f"{C_total:.6f}"]

    targets_struct = {}
    targets_pct = [t.strip() for t in args.targets.split(",") if t.strip()]

    for t in targets_pct:
        pct = float(t)
        y  = min(max(pct/100.0, 1e-9), 0.999999)
        lr_bp = effort_for_coverage(y, a, b)

        if lr_bp == float("inf"):
            lr_reads = float("inf")
        else:
            lr_reads = lr_bp / AL if AL > 0 else float("nan")

        # TSV columns
        cols += [f"LR_{int(pct)}_bp", f"LR_{int(pct)}_reads"]
        row  += [
            "inf" if lr_bp==float("inf") else f"{lr_bp:.0f}",
            "inf" if lr_reads==float("inf") else f"{lr_reads:.0f}"
        ]

        # JSON structure
        targets_struct[str(int(pct))] = {
            "LR_bp": None if lr_bp==float("inf") else float(lr_bp),
            "LR_reads": None if lr_reads==float("inf") else float(lr_reads)
        }

    # ---------- WRITE TSV ----------
    with open(args.tsv_out, "w") as out:
        out.write("\t".join(cols) + "\n")
        out.write("\t".join(map(str, row)) + "\n")

    # ---------- WRITE JSON ----------
    summary = {
        "sample": Path(args.npo_file).stem,
        "npo_file": str(args.npo_file),
        "subset_reads": float(args.subset_reads),
        "total_reads": float(args.total_reads),
        "kappa_subset": float(prep["kappa_subset"]),
        "C_subset": float(prep["C_subset"]),
        "kappa_total": float(kappa_total),
        "C_total": float(C_total),
        "targets": targets_struct,
        "outputs": {
            "tsv": str(args.tsv_out),
            "json": str(args.json_out)
        }
    }

    with open(args.json_out, "w") as jf:
        json.dump(summary, jf, indent=2)

    print(f"[✓] TSV written → {args.tsv_out}")
    print(f"[✓] JSON written → {args.json_out}")

if __name__ == "__main__":
    main()
