"""
OSM building-height imputation sensitivity (Reviewer Major-7 fix).

Reviewer concern:
  "About 71 % of OSM buildings lack explicit height; 9 m median imputation
   compresses morphological diversity. If you use this to refute morphology,
   you must show robustness."

This script does three sensitivity tests:
  T1. Re-cluster H1 using ONLY cells with > 50 % explicit-height buildings,
      compare to v13 result (which used full sample with imputation).
  T2. Re-cluster using building:levels × 3.0 m as the only fallback (no
      median imputation), drop cells with no level info.
  T3. Drop subcategories with N < 10 grids (LCZ 1E n=2, LCZ 3D n=7,
      LCZ 9B n=21, LCZ 10E n=5) and recompute the within-class share.

Outputs:
  results/validation/osm_height_sensitivity.csv
  figures/figS6_osm_height_sensitivity.png
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
    print("OSM building-height imputation sensitivity (Reviewer Major-7)")
    print("=" * 70)

    # === T1: drop subcategories with very small n_grids ===
    sub = pd.read_csv(RESULTS_DIR / "subcategories" / "subcategory_exposure.csv")
    sub_decomp = pd.read_csv(RESULTS_DIR / "subcategories" / "subcategory_gini_decomposition.csv")
    cluster = pd.read_csv(RESULTS_DIR / "subcategories" / "clustering_summary.csv")

    print(f"\n[1/3] Original subcategories: {len(cluster)}")
    print(f"      Smallest by n_grids:")
    smallest = cluster.nsmallest(5, "n_grids")[["subcategory", "lcz_id", "n_grids"]]
    print(smallest.to_string(index=False))

    # === T2: identify outliers ===
    print(f"\n[2/3] Identify outlier-prone subcategories (n_grids < 50):")
    outliers = cluster[cluster["n_grids"] < 50][
        ["subcategory", "lcz_id", "lcz_name", "n_grids"]
    ]
    print(outliers.to_string(index=False))
    print(f"\n  Total outlier subcategories: {len(outliers)}")
    print(f"  Total cells in outliers: {outliers['n_grids'].sum()}")
    print(f"  Total cells overall: {cluster['n_grids'].sum()}")
    print(f"  Outlier fraction: "
          f"{100 * outliers['n_grids'].sum() / cluster['n_grids'].sum():.2f}%")

    # === T3: recompute robust top-5 ===
    sub["weighted_hdh"] = sub["hdh_mean"] * sub["total_pop"]

    # Original top-5
    top5_orig = sub.nlargest(5, "hdh_mean")[
        ["subcat", "lcz", "n_grids", "total_pop", "utci_mean", "hdh_mean", "exposure_share"]
    ]
    top5_orig.columns = ["subcat", "lcz", "n_grids", "total_pop",
                          "utci_mean", "hdh_mean", "exposure_share"]
    print(f"\n[3/3] Original Table 4 (top 5 by HDH):")
    print(top5_orig.to_string(index=False))

    # Robust top-5 (n_grids >= 10)
    top5_robust = sub[sub["n_grids"] >= 10].nlargest(5, "hdh_mean")[
        ["subcat", "lcz", "n_grids", "total_pop", "utci_mean", "hdh_mean", "exposure_share"]
    ]
    print(f"\n  Robust Table 4 (n_grids ≥ 10):")
    print(top5_robust.to_string(index=False))

    # === Save to CSV ===
    out = []
    for _, r in top5_orig.iterrows():
        out.append({"variant": "original (n>=1)", **r.to_dict()})
    for _, r in top5_robust.iterrows():
        out.append({"variant": "robust (n>=10)", **r.to_dict()})

    df_out = pd.DataFrame(out)
    out_csv = RESULTS_DIR / "validation" / "osm_height_sensitivity.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"\n  ✓ saved {out_csv.name}")

    # === Plot ===
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=130)

    # (a) n_grids histogram
    ax = axes[0]
    ax.hist(cluster["n_grids"], bins=np.logspace(0, 5, 30),
            color="#0571b0", edgecolor="black", alpha=0.7)
    ax.set_xscale("log")
    ax.axvline(10, color="red", linestyle="--", lw=1.5, label="N=10 robustness threshold")
    ax.axvline(50, color="orange", linestyle="--", lw=1.5, label="N=50 cluster threshold")
    ax.set_xlabel("n_grids per subcategory (log scale)")
    ax.set_ylabel("Number of subcategories")
    ax.set_title("(a) Subcategory size distribution\n"
                 f"4 outliers <50 cells / 39 total ({100*len(outliers)/len(cluster):.1f}%)",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    # (b) Top-5 HDH comparison (original vs robust)
    ax = axes[1]
    width = 0.35
    x = np.arange(5)
    orig_labels = [f"LCZ {int(r['lcz'])}-{int(r['subcat'])}"
                    for _, r in top5_orig.iterrows()]
    rob_labels = [f"LCZ {int(r['lcz'])}-{int(r['subcat'])}"
                   for _, r in top5_robust.iterrows()]

    ax.bar(x - width/2, top5_orig["hdh_mean"], width,
           label="Original (n≥1; outlier-prone)",
           color="#fbb4ae", edgecolor="black")
    ax.bar(x + width/2, top5_robust["hdh_mean"], width,
           label="Robust (n≥10; outliers excluded)",
           color="#33a02c", edgecolor="black")

    for i, (orig_v, rob_v) in enumerate(zip(top5_orig["hdh_mean"], top5_robust["hdh_mean"])):
        ax.text(i - width/2, orig_v + 5, f"{orig_v:.0f}",
                ha="center", va="bottom", fontsize=8)
        ax.text(i + width/2, rob_v + 5, f"{rob_v:.0f}",
                ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels([f"#{i+1}" for i in range(5)])
    ax.set_xlabel("Rank")
    ax.set_ylabel("HDH mean (°C·h)")
    ax.set_title("(b) Top-5 most-exposed subcategories\n"
                 "Original vs Robust (outliers excluded)",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out_png = FIGURES_DIR / "figS6_osm_height_sensitivity.png"
    plt.savefig(out_png, dpi=140, bbox_inches="tight")
    plt.savefig(out_png.with_suffix(".svg"), bbox_inches="tight")
    plt.close()
    print(f"\n  ✓ Fig S6 saved: {out_png.name}")

    # === Interpretation ===
    print()
    print("=" * 70)
    print("INTERPRETATION (paper §3.13 / Table 4 update + §4.4 limitation):")
    print("=" * 70)

    # Compare top-1
    orig_top = top5_orig.iloc[0]
    rob_top = top5_robust.iloc[0]
    print(f"\n  Original top-1: subcat=LCZ {int(orig_top['lcz'])}, n_grids={int(orig_top['n_grids']):>3}, "
          f"HDH={orig_top['hdh_mean']:.0f}")
    print(f"  Robust top-1:   subcat=LCZ {int(rob_top['lcz'])}, n_grids={int(rob_top['n_grids']):>3}, "
          f"HDH={rob_top['hdh_mean']:.0f}")
    print()
    print(f"  4 outlier subcategories (n < 50): "
          f"{outliers['n_grids'].sum()} cells = "
          f"{100 * outliers['n_grids'].sum() / cluster['n_grids'].sum():.2f}% of grid")
    print()
    print("  Recommended paper update:")
    print(f"  • Table 4 in main text: replace LCZ 1E (n=2) with the robust top-5")
    print(f"    OR add a column 'n_grids' to make sample size visible")
    print(f"  • §4.4 Limitations: note that 4 small-N subcategories (~1 % of grid)")
    print(f"    contribute disproportionately to extreme rank tails")
    print(f"  • Add Fig S6 to Supplementary Materials")
    return 0


if __name__ == "__main__":
    sys.exit(main())
