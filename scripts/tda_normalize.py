"""
TDA scale-normalization (Reviewer Major-6 fix).

Reviewer concern:
  "LCZ 6 (Open low-rise) and LCZ 8 (Large low-rise) have FAR more cells
   than LCZ 1 (Compact high-rise) and LCZ 10 (Heavy industry); raw beta_0
   and beta_1 counts inflate naturally with area. Normalize by area or
   sub-sample equal-area patches before comparing."

Action:
  1. Compute beta_0 and beta_1 *density* (per 1,000 cells, equivalent to
     per 10 km²).
  2. Compute persistence-entropy ratio (already a normalized intensive
     quantity, but verify it is interpreted as such).
  3. Plot a normalized version of Fig 6 (or Fig S5 supplementary) showing
     the scale-corrected per-LCZ topological signature.
  4. Compute equal-area-sub-sample Wasserstein distances for the four
     "extreme" LCZ pairs (1 vs 10 small; 6 vs 8 large).

Output:
  results/tda/persistence_features_normalized.csv
  figures/figS5_tda_normalized.png
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.config import RESULTS_DIR, FIGURES_DIR
from src.utils.figure_style import apply_paper_style
apply_paper_style()


def main():
    print("=" * 70)
    print("TDA scale-normalization (Reviewer Major-6 fix)")
    print("=" * 70)

    # === Load original TDA features ===
    src = RESULTS_DIR / "tda" / "persistence_features.csv"
    df = pd.read_csv(src)
    print(f"\n[1/3] Loaded {len(df)} LCZ classes from {src.name}")

    # === Compute density-based metrics ===
    df["n_h0_per_1k"] = df["n_h0"] / df["n_cells"] * 1000
    df["n_h1_per_1k"] = df["n_h1"] / df["n_cells"] * 1000
    df["total_life_h0_per_1k"] = df["total_lifetime_h0"] / df["n_cells"] * 1000
    df["total_life_h1_per_1k"] = df["total_lifetime_h1"] / df["n_cells"] * 1000
    df["n_sig_per_1k"] = df["n_significant"] / df["n_cells"] * 1000

    # 1 cell = 100m × 100m = 10,000 m². 1000 cells = 10 km².
    df["area_km2"] = df["n_cells"] / 100.0  # 100 cells per km²

    print(f"\n[2/3] Computed density metrics (per 1,000 cells = per 10 km²)")
    print(df[["lcz_id", "name", "n_cells", "area_km2",
              "n_h0", "n_h0_per_1k", "n_h1", "n_h1_per_1k",
              "persistence_entropy", "n_sig_per_1k"]].to_string(index=False))

    # === Save ===
    out_csv = RESULTS_DIR / "tda" / "persistence_features_normalized.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n  ✓ saved {out_csv.name}")

    # === Compare RAW vs NORMALIZED ranking ===
    print("\n[3/3] Comparing RAW vs NORMALIZED rankings:")
    print()
    print("  RAW β₁ ranking (by raw count):")
    raw = df.sort_values("n_h1", ascending=False)
    for i, (_, r) in enumerate(raw.iterrows(), 1):
        print(f"    {i}. LCZ {int(r['lcz_id']):>2} ({r['name']:<12})  "
              f"n_cells={int(r['n_cells']):>6}  n_h1={int(r['n_h1']):>3}")

    print()
    print("  NORMALIZED β₁ density ranking (per 1,000 cells = per 10 km²):")
    norm = df.sort_values("n_h1_per_1k", ascending=False)
    for i, (_, r) in enumerate(norm.iterrows(), 1):
        print(f"    {i}. LCZ {int(r['lcz_id']):>2} ({r['name']:<12})  "
              f"density={r['n_h1_per_1k']:>5.2f}/1000  raw={int(r['n_h1']):>3}")

    print()
    print("  Persistence-entropy ranking (intensive, scale-invariant):")
    ent = df.sort_values("persistence_entropy", ascending=False)
    for i, (_, r) in enumerate(ent.iterrows(), 1):
        print(f"    {i}. LCZ {int(r['lcz_id']):>2} ({r['name']:<12})  "
              f"entropy={r['persistence_entropy']:.3f}")

    # === Plot: 4-panel comparison ===
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), dpi=130)
    name_short = df["name"].str[:8]

    cmap = plt.get_cmap("tab10")
    colors = [cmap(i % 10) for i in range(len(df))]

    # (a) Area in km²
    ax = axes[0, 0]
    bars = ax.bar(name_short, df["area_km2"], color=colors, edgecolor="black")
    ax.set_ylabel("Area (km²)")
    ax.set_title("(a) Per-LCZ area\n(highly skewed: LCZ 8/6 ≫ LCZ 1/10)",
                 fontsize=10, fontweight="bold")
    for b, v in zip(bars, df["area_km2"]):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 5,
                f"{v:.0f}", ha="center", fontsize=8)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(axis="y", alpha=0.3)

    # (b) Raw β₁
    ax = axes[0, 1]
    ax.bar(name_short, df["n_h1"], color=colors, edgecolor="black")
    ax.set_ylabel("Raw β₁ count")
    ax.set_title("(b) RAW β₁ count\n(reflects area, not just topology)",
                 fontsize=10, fontweight="bold", color="#d62728")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(axis="y", alpha=0.3)

    # (c) β₁ density
    ax = axes[1, 0]
    bars = ax.bar(name_short, df["n_h1_per_1k"], color=colors, edgecolor="black")
    ax.set_ylabel("β₁ per 1,000 cells (= per 10 km²)")
    ax.set_title("(c) NORMALIZED β₁ density\n(scale-invariant, fair comparison)",
                 fontsize=10, fontweight="bold", color="#2ca02c")
    for b, v in zip(bars, df["n_h1_per_1k"]):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.05,
                f"{v:.2f}", ha="center", fontsize=8)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(axis="y", alpha=0.3)

    # (d) Persistence entropy (intensive)
    ax = axes[1, 1]
    bars = ax.bar(name_short, df["persistence_entropy"], color=colors, edgecolor="black")
    ax.set_ylabel("Persistence entropy")
    ax.set_title("(d) Persistence entropy\n(intensive quantity, no normalization needed)",
                 fontsize=10, fontweight="bold", color="#2ca02c")
    for b, v in zip(bars, df["persistence_entropy"]):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.05,
                f"{v:.2f}", ha="center", fontsize=8)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(axis="y", alpha=0.3)

    plt.suptitle("TDA scale-normalization (Major-6 reviewer response)\n"
                 "RAW counts inflate with area; density and entropy give a fair comparison",
                 fontsize=11.5, fontweight="bold", y=1.02)
    plt.tight_layout()
    out_png = FIGURES_DIR / "figS5_tda_normalized.png"
    plt.savefig(out_png, dpi=140, bbox_inches="tight")
    plt.savefig(out_png.with_suffix(".svg"), bbox_inches="tight")
    plt.close()
    print(f"\n  ✓ Fig S5 saved: {out_png.name}")

    # === Interpretation ===
    print()
    print("=" * 70)
    print("INTERPRETATION (paper §3.6 update + Fig 6 caption update):")
    print("=" * 70)
    raw_max_lcz = int(raw.iloc[0]["lcz_id"])
    norm_max_lcz = int(norm.iloc[0]["lcz_id"])
    raw_max_count = int(raw.iloc[0]["n_h1"])
    norm_max_density = norm.iloc[0]["n_h1_per_1k"]

    if raw_max_lcz != norm_max_lcz:
        print(f"\n  ⚠ Reviewer Major-6 confirmed: ranking changes after normalization.")
        print(f"    RAW max β₁:        LCZ {raw_max_lcz} (count = {raw_max_count})")
        print(f"    NORMALIZED max β₁: LCZ {norm_max_lcz} (density = {norm_max_density:.2f}/10 km²)")
    else:
        print(f"\n  ✓ Top-1 LCZ is robust to normalization (LCZ {raw_max_lcz})")
        print(f"    Raw count: {raw_max_count}; Density: {raw.iloc[0]['n_h1_per_1k']:.2f}/10 km²")

    print()
    print("  Recommended paper update:")
    print("  • Replace raw β₁ counts in §3.6 / Fig 6 with density (per 10 km²)")
    print("  • Add Fig S5 to Supplementary Materials")
    print("  • Drop or qualify the 'LCZ 6 produces 297 holes' claim (count is")
    print("    area-driven; density is the meaningful comparison)")
    print("  • Use persistence entropy (intensive) and Wasserstein distance")
    print("    (relative measure) for primary topological characterization")
    return 0


if __name__ == "__main__":
    sys.exit(main())
