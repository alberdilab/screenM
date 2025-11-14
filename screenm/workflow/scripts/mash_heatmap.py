
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def read_pairwise_or_matrix(tsv_path: Path) -> pd.DataFrame:
    # Try reading with headers
    df_raw = pd.read_csv(tsv_path, sep='\t', header=0)
    # If it looks like a square matrix (first column is index and columns == rows), return that
    if df_raw.shape[1] > 1 and df_raw.shape[0] == df_raw.shape[1]-1:
        # First column likely contains row labels
        df = pd.read_csv(tsv_path, sep='\t', header=0, index_col=0)
        # Coerce to numeric
        df = df.apply(pd.to_numeric, errors='coerce')
        return df

    # Otherwise, assume pairwise "edge list" format
    # Accept headers if present; detect first three columns as A,B,dist
    df = pd.read_csv(tsv_path, sep='\t', header=None, usecols=[0,1,2], names=['A','B','dist'])
    # Coerce distance to float
    df['dist'] = pd.to_numeric(df['dist'], errors='coerce')
    df = df.dropna(subset=['A','B','dist'])
    # Build sorted unique labels
    labels = pd.Index(sorted(set(df['A']).union(set(df['B']))), dtype=object)
    mat = pd.DataFrame(np.nan, index=labels, columns=labels, dtype=float)
    # Fill both directions
    for a,b,d in df[['A','B','dist']].itertuples(index=False):
        mat.at[a,b] = d
        mat.at[b,a] = d
    # Diagonal = 0
    np.fill_diagonal(mat.values, 0.0)
    # If some entries are missing, fill with symmetric value or 0 as fallback
    # Prefer min of [i,j] and [j,i] where available; else leave NaN -> fill with 0
    # (Mash distances are >=0; 0 is a neutral diagonal-like fallback)
    mat = mat.astype(float).fillna(0.0)
    return mat

def plot_heatmap(mat: pd.DataFrame, out_png: Path, dpi: int = 200, title: str = "Mash Pairwise Distance Heatmap"):
    fig_w = max(6, min(16, mat.shape[1] * 0.45))
    fig_h = max(5, min(16, mat.shape[0] * 0.45))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(mat.values, aspect='auto')
    ax.set_xticks(range(len(mat.columns)))
    ax.set_xticklabels(mat.columns, rotation=90)
    ax.set_yticks(range(len(mat.index)))
    ax.set_yticklabels(mat.index)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    fig.savefig(out_png, dpi=dpi, bbox_inches='tight')

def main():
    ap = argparse.ArgumentParser(description="Convert pairwise Mash distances to a symmetric matrix and plot a heatmap")
    ap.add_argument("tsv", help="Mash distances TSV. Either pairwise list (A B dist ...) or a square matrix TSV.")
    ap.add_argument("-o", "--out-png", default="mash_pairwise_heatmap.png", help="Output heatmap PNG (default: mash_pairwise_heatmap.png)")
    ap.add_argument("-m", "--out-matrix", default="mash_pairwise_matrix.tsv", help="Output symmetric matrix TSV (default: mash_pairwise_matrix.tsv)")
    ap.add_argument("--dpi", type=int, default=200, help="PNG DPI (default: 200)")
    args = ap.parse_args()

    tsv_path = Path(args.tsv)
    mat = read_pairwise_or_matrix(tsv_path)

    # Save the matrix
    mat.to_csv(args.out_matrix, sep='\t', header=True, index=True, float_format='%.6g')

    # Plot
    plot_heatmap(mat, Path(args.out_png), dpi=args.dpi)

if __name__ == "__main__":
    main()
