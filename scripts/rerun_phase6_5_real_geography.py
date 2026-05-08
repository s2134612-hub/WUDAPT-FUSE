"""
Critical re-test: rerun Phase 6.5 (single-feature Gini decomposition) with
REAL elevation-based mountain distance, replacing the LCZ-11/12-proxy.

Reviewer Major-2 Issue: the "mountain" proxy in v13 was actually a "forest
proxy" (28.3% of grid). Day 2 analysis showed only 29.5% of LCZ 11/12 cells
are real elevated terrain (>200 m). The 10.81 pp Gini reduction attributed
to "geography" may therefore have been driven by green-space proximity, not
mountain-specific physics.

This script tests the H4 hypothesis under the REAL elevation distance and
reports whether the geographic dominance still holds.

Outputs:
  results/validation/phase6_5_real_vs_proxy.csv
  figures/figS4_phase6_5_real_vs_proxy.png
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.ndimage import distance_transform_edt

from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR
from src.utils.figure_style import apply_paper_style
apply_paper_style()


VAL_DIR = RESULTS_DIR / "validation"
VAL_DIR.mkdir(parents=True, exist_ok=True)


def population_weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    """Population-weighted Gini, robust to NaN."""
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    v, w = values[valid], weights[valid]
    if len(v) < 2:
        return np.nan
    order = np.argsort(v)
    v, w = v[order], w[order]
    cumw = np.cumsum(w)
    cum_vw = np.cumsum(v * w)
    total_w = cumw[-1]
    total_vw = cum_vw[-1]
    if total_vw == 0:
        return 0.0
    # Lorenz-area-based Gini for weighted samples
    cum_pop_share = cumw / total_w
    cum_val_share = cum_vw / total_vw
    return float(1 - 2 * np.trapz(cum_val_share, cum_pop_share))


def gini_within_lcz(values, weights, lcz):
    """Population-weighted within-LCZ Gini share."""
    g_total = population_weighted_gini(values, weights)
    if g_total == 0 or np.isnan(g_total):
        return np.nan, np.nan
    classes = np.unique(lcz[np.isfinite(lcz)])
    g_within_sum = 0
    total_w = np.nansum(weights[np.isfinite(values) & np.isfinite(lcz)])
    total_vw = np.nansum(values * weights * np.isfinite(lcz))
    for c in classes:
        mask = (lcz == c) & np.isfinite(values) & np.isfinite(weights)
        if mask.sum() < 2:
            continue
        g_c = population_weighted_gini(values[mask], weights[mask])
        w_c = weights[mask].sum()
        v_c = (values[mask] * weights[mask]).sum() / w_c
        g_within_sum += (w_c / total_w) * (v_c * w_c / total_vw) * g_c
    return g_total, g_within_sum / g_total * 100  # within-share %


def main():
    print("=" * 70)
    print("Phase 6.5 RE-RUN with REAL geography (Major-2 fix)")
    print("=" * 70)

    # === Load data ===
    print("\n[1/4] Loading...")
    utci_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc")
    pop = rxr.open_rasterio(PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif", masked=True).squeeze()
    lcz = rxr.open_rasterio(PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif", masked=True).squeeze()
    dem = rxr.open_rasterio(PROCESSED_DATA_DIR / "shenzhen_dem_100m.tif", masked=True).squeeze()
    real_mt_dist = rxr.open_rasterio(PROCESSED_DATA_DIR / "shenzhen_real_mountain_distance_100m.tif",
                                       masked=True).squeeze()

    # Use HDH as exposure metric
    hdh = utci_ds["hdh"].values
    pop_arr = pop.values if pop.shape == hdh.shape else None

    # Reproject pop and lcz to UTCI grid if shapes differ
    if pop.shape != hdh.shape:
        # The UTCI summary uses (560, 1067), pop uses (575, 1040)
        # Need to resample pop and lcz to match UTCI grid
        ref_da = xr.DataArray(hdh, coords={"y": utci_ds.y.values,
                                             "x": utci_ds.x.values},
                                dims=["y", "x"]).rio.write_crs("EPSG:32650")
        pop_arr = pop.rio.reproject_match(ref_da).values
        lcz_arr = lcz.rio.reproject_match(ref_da).values
        dem_arr = dem.rio.reproject_match(ref_da).values
        real_mt_arr = real_mt_dist.rio.reproject_match(ref_da).values
    else:
        pop_arr = pop.values
        lcz_arr = lcz.values
        dem_arr = dem.values
        real_mt_arr = real_mt_dist.values

    # Restrict to built-up cells with population
    builtup_mask = np.isin(lcz_arr.astype(int), [1, 2, 3, 4, 5, 6, 8, 9, 10])
    valid_mask = builtup_mask & np.isfinite(hdh) & np.isfinite(pop_arr) & (pop_arr > 0)
    print(f"  Valid built-up cells: {valid_mask.sum():,}")

    # === Compute PROXY mountain/coast distances (LCZ-based) ===
    print("\n[2/4] Computing PROXY mountain/coast distances (LCZ 11/12 / LCZ 17)...")
    forest_mask = np.isin(lcz_arr.astype(int), [11, 12])
    water_mask = lcz_arr.astype(int) == 17
    proxy_mt_dist = distance_transform_edt(~forest_mask) * 100  # 100m per pixel
    proxy_coast_dist = distance_transform_edt(~water_mask) * 100

    # === Compute REAL coast distance from DEM (cells with elev <= 0) ===
    print("\n[3/4] Computing REAL coast distance from DEM (elev <= 0)...")
    coast_mask_real = (dem_arr <= 0) & np.isfinite(dem_arr)
    if coast_mask_real.sum() == 0:
        # Fall back: use LCZ 17 as coast proxy (DEM may not capture water)
        coast_mask_real = water_mask
        print("  (DEM has no <=0 cells; falling back to LCZ 17 water mask)")
    real_coast_dist = distance_transform_edt(~coast_mask_real) * 100

    # === Single-feature k-means clustering for each scheme ===
    print("\n[4/4] Running single-feature k-means and computing Gini reduction...")

    schemes = {
        "Coast PROXY (LCZ 17)": proxy_coast_dist,
        "Coast REAL (DEM<=0)": real_coast_dist,
        "Mountain PROXY (LCZ 11/12)": proxy_mt_dist,
        "Mountain REAL (DEM>200m)": real_mt_arr,
        "Elevation (m)": dem_arr,
        "Coast+Mountain PROXY": None,  # joint
        "Coast+Mountain REAL": None,
    }

    # Baseline: LCZ-class within share
    g_total_baseline, within_baseline = gini_within_lcz(hdh, pop_arr, lcz_arr)
    print(f"\n  Baseline: G_total={g_total_baseline:.4f}, "
          f"LCZ-within share = {within_baseline:.2f}%")

    results = []
    K = 35  # n subcategories (matching v13)

    for name, feat in schemes.items():
        if feat is None:  # joint Coast+Mountain
            if name == "Coast+Mountain PROXY":
                feat_arr = np.stack([proxy_coast_dist[valid_mask], proxy_mt_dist[valid_mask]], axis=1)
            else:
                feat_arr = np.stack([real_coast_dist[valid_mask], real_mt_arr[valid_mask]], axis=1)
            n_subcat_cluster = 45  # match v13 Phase 6.5
        else:
            feat_arr = feat[valid_mask].reshape(-1, 1)
            n_subcat_cluster = 45

        if not np.isfinite(feat_arr).all(axis=0).all():
            print(f"  ⚠ {name}: feature has NaN, skipping")
            continue

        scaler = StandardScaler()
        feat_scaled = scaler.fit_transform(feat_arr)

        km = KMeans(n_clusters=n_subcat_cluster, random_state=42, n_init=10)
        labels_within = km.fit_predict(feat_scaled)

        # Combine with LCZ to make subcategory IDs
        lcz_within = lcz_arr[valid_mask]
        subcat = lcz_within * 100 + labels_within  # unique combo
        hdh_v = hdh[valid_mask]
        pop_v = pop_arr[valid_mask]

        g_total, within_sub = gini_within_lcz(hdh_v, pop_v, subcat)
        reduction_pp = within_baseline - within_sub
        results.append({
            "scheme": name,
            "n_features": feat_arr.shape[1],
            "n_subcategories": len(np.unique(subcat)),
            "G_within_lcz": within_baseline,
            "G_within_sub": within_sub,
            "reduction_pp": reduction_pp,
        })
        flag = "✓" if reduction_pp >= 5 else "✗"
        print(f"  {flag}  {name:<32}  reduction = {reduction_pp:+.2f} pp")

    df = pd.DataFrame(results)
    df.to_csv(VAL_DIR / "phase6_5_real_vs_proxy.csv", index=False)
    print(f"\n  ✓ saved: phase6_5_real_vs_proxy.csv")

    # === Compare PROXY vs REAL ===
    print("\n" + "=" * 70)
    print("PROXY vs REAL comparison summary:")
    print("=" * 70)

    pairs = [
        ("Coast PROXY (LCZ 17)", "Coast REAL (DEM<=0)"),
        ("Mountain PROXY (LCZ 11/12)", "Mountain REAL (DEM>200m)"),
        ("Coast+Mountain PROXY", "Coast+Mountain REAL"),
    ]
    for proxy_name, real_name in pairs:
        proxy_row = df[df["scheme"] == proxy_name]
        real_row = df[df["scheme"] == real_name]
        if len(proxy_row) and len(real_row):
            p = proxy_row.iloc[0]["reduction_pp"]
            r = real_row.iloc[0]["reduction_pp"]
            delta = r - p
            print(f"\n  {proxy_name:<32}  {p:+.2f} pp")
            print(f"  {real_name:<32}  {r:+.2f} pp")
            print(f"  Delta (REAL − PROXY)              {delta:+.2f} pp")
            if abs(delta) < 1:
                print(f"  → robust: results similar")
            elif delta > 0:
                print(f"  → REAL > PROXY: real geography MORE explanatory than proxy")
            else:
                print(f"  → REAL < PROXY: proxy was overstating geography effect ⚠")

    # === Plot ===
    fig, ax = plt.subplots(figsize=(12, 6), dpi=130)
    bar_pos = np.arange(len(df))
    colors = ["#fbb4ae" if "PROXY" in s else "#33a02c" if "REAL" in s else "#888" for s in df["scheme"]]
    bars = ax.bar(bar_pos, df["reduction_pp"], color=colors, edgecolor="black", linewidth=1)
    ax.axhline(5, color="red", linestyle="--", lw=1.5, label="5-pp threshold")
    ax.axhline(0, color="black", lw=0.5)
    for i, (b, v) in enumerate(zip(bars, df["reduction_pp"])):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.2,
                f"{v:+.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(bar_pos)
    ax.set_xticklabels(df["scheme"], rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Within-class Gini reduction (pp)")
    ax.set_title("Phase 6.5 RE-RUN: Real DEM-based vs LCZ-proxy geography\n"
                 f"H4 robustness check after Major-2 reviewer concern",
                 fontweight="bold", fontsize=11)
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out_png = FIGURES_DIR / "figS4_phase6_5_real_vs_proxy.png"
    plt.savefig(out_png, dpi=140, bbox_inches="tight")
    plt.savefig(out_png.with_suffix(".svg"), bbox_inches="tight")
    plt.close()
    print(f"\n  ✓ Fig S4 saved: {out_png.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
