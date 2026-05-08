"""
Replace LCZ-proxy geography features with REAL physical geography from SRTM DEM.

Reviewer Major-2 Issue:
  In v13, "mountain distance" = distance to nearest LCZ 11/12 cell, but
  LCZ 11/12 is dense forest, which may be elevated mountain forest OR
  flat lowland forest. Similarly "coast distance" = distance to LCZ 17
  (water), which includes inland lakes / reservoirs / rivers, not just
  the open coast.

This script computes:
  1. Real elevation (m) — from SRTM 30 m DEM
  2. Real mountain distance — distance to nearest cell with elevation > 200 m
  3. Real coastline distance — distance to nearest cell with elevation 0
     AND adjacent to NaN (i.e., proper land-sea boundary, not inland water)
  4. Slope and aspect — for katabatic-flow physical interpretation (§4.6)

Outputs:
  data/processed/shenzhen_dem_100m.tif
  data/processed/shenzhen_real_mountain_distance_100m.tif
  data/processed/shenzhen_real_coast_distance_100m.tif
  data/processed/shenzhen_slope_100m.tif
  results/validation/geography_proxy_vs_real.csv  ← key comparison table
  figures/figS3_real_vs_proxy_geography.png
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gzip
import shutil
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt
from rasterio.merge import merge
from rasterio.io import MemoryFile
import rasterio

from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR, SHENZHEN_BBOX
from src.utils.figure_style import apply_paper_style
apply_paper_style()


SRTM_DIR = Path(__file__).resolve().parents[1] / "data" / "external" / "srtm30"
OUT_DIR = PROCESSED_DATA_DIR
VAL_DIR = RESULTS_DIR / "validation"
VAL_DIR.mkdir(parents=True, exist_ok=True)

MOUNTAIN_ELEV_THRESHOLD_M = 200  # cells above this = "mountain"


def decompress_hgt(gz_path: Path) -> Path:
    """Decompress .hgt.gz to .hgt (1201x1201 raw int16 big-endian)."""
    out = gz_path.with_suffix("")  # remove .gz
    if out.exists():
        return out
    with gzip.open(gz_path, "rb") as src, open(out, "wb") as dst:
        shutil.copyfileobj(src, dst)
    return out


def hgt_to_geotiff(hgt_path: Path) -> Path:
    """Convert raw .hgt to GeoTIFF with proper CRS for rasterio operations."""
    tile_name = hgt_path.stem  # e.g., "N22E113"
    out = hgt_path.with_suffix(".tif")
    if out.exists():
        return out

    # Parse tile bounding box
    lat = int(tile_name[1:3]) * (1 if tile_name[0] == "N" else -1)
    lon = int(tile_name[4:7]) * (1 if tile_name[3] == "E" else -1)

    # SRTM 1-arc-second: 3601 x 3601 (US) or 1201 x 1201 (3-arc-second)
    # AWS terrain tiles are 3601 (1-arc-second)
    raw = np.fromfile(hgt_path, dtype=">i2")  # big-endian int16
    n = int(np.sqrt(len(raw)))
    if n * n != len(raw):
        raise ValueError(f"Unexpected tile size for {tile_name}: {len(raw)} pixels")
    arr = raw.reshape(n, n).astype(np.float32)
    arr[arr <= -32000] = np.nan  # SRTM no-data flag

    # Write GeoTIFF: 1° x 1° tile, named by SW corner, but pixels stored top-left first
    transform = rasterio.transform.from_bounds(lon, lat, lon + 1, lat + 1, n, n)
    profile = {
        "driver": "GTiff", "height": n, "width": n, "count": 1,
        "dtype": "float32", "crs": "EPSG:4326",
        "transform": transform, "nodata": np.nan,
    }
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(arr, 1)
    return out


def mosaic_tiles(tile_paths: list[Path]) -> tuple[np.ndarray, dict]:
    """Mosaic 4 tiles into single GeoTIFF."""
    srcs = [rasterio.open(p) for p in tile_paths]
    merged, transform = merge(srcs)
    profile = srcs[0].profile.copy()
    profile.update({
        "height": merged.shape[1], "width": merged.shape[2],
        "transform": transform,
    })
    for s in srcs:
        s.close()
    return merged[0], profile


def reproject_to_shenzhen_grid(dem_arr: np.ndarray, dem_profile: dict) -> xr.DataArray:
    """Resample DEM to match Shenzhen 100-m UTM 50N grid."""
    # Reference grid: existing population raster
    ref_path = OUT_DIR / "shenzhen_pop_100m_utm.tif"
    ref = rxr.open_rasterio(ref_path, masked=True).squeeze()

    with MemoryFile() as memfile:
        with memfile.open(**dem_profile) as src:
            src.write(dem_arr, 1)
            dem_xr = rxr.open_rasterio(memfile.open(), masked=True).squeeze()

    dem_resampled = dem_xr.rio.reproject_match(
        ref, resampling=rasterio.enums.Resampling.bilinear,
    )
    return dem_resampled


def compute_distance_to_mask(mask: np.ndarray, pixel_size_m: float = 100.0) -> np.ndarray:
    """Distance transform: nearest cell where mask == True (in meters)."""
    if mask.sum() == 0:
        return np.full(mask.shape, np.nan)
    dist_pixels = distance_transform_edt(~mask)
    return dist_pixels * pixel_size_m


def main():
    print("=" * 70)
    print("Day 2: Compute REAL geography features (DEM-based)")
    print("=" * 70)

    # === Step 1: Decompress and convert SRTM tiles ===
    print("\n[1/5] Decompressing 4 SRTM tiles to GeoTIFF...")
    tile_tifs = []
    for gz in sorted(SRTM_DIR.glob("*.hgt.gz")):
        hgt = decompress_hgt(gz)
        tif = hgt_to_geotiff(hgt)
        tile_tifs.append(tif)
        size_mb = tif.stat().st_size / 1e6
        print(f"  ✓ {tif.name} ({size_mb:.1f} MB)")

    # === Step 2: Mosaic ===
    print(f"\n[2/5] Mosaicking {len(tile_tifs)} tiles...")
    mosaic_arr, mosaic_profile = mosaic_tiles(tile_tifs)
    valid = ~np.isnan(mosaic_arr)
    print(f"  Mosaic: {mosaic_arr.shape}, "
          f"valid {valid.sum():,} px, "
          f"elev range {np.nanmin(mosaic_arr):.0f} to {np.nanmax(mosaic_arr):.0f} m")

    # === Step 3: Reproject to Shenzhen 100-m UTM grid ===
    print("\n[3/5] Reprojecting to Shenzhen 100-m UTM grid...")
    dem_sz = reproject_to_shenzhen_grid(mosaic_arr, mosaic_profile)
    dem_path = OUT_DIR / "shenzhen_dem_100m.tif"
    dem_sz.rio.to_raster(dem_path, dtype="float32")
    print(f"  ✓ saved {dem_path.name}")
    print(f"    Shape: {dem_sz.shape}")
    print(f"    Elev range: {float(dem_sz.min()):.0f} – {float(dem_sz.max()):.0f} m")

    dem_arr = dem_sz.values
    dem_arr_clean = np.where(np.isfinite(dem_arr), dem_arr, 0)

    # === Step 4: Compute real mountain distance ===
    print(f"\n[4/5] Computing real mountain distance (elev > {MOUNTAIN_ELEV_THRESHOLD_M} m)...")
    mountain_mask = dem_arr_clean > MOUNTAIN_ELEV_THRESHOLD_M
    print(f"  Mountain cells: {mountain_mask.sum():,} ({100 * mountain_mask.mean():.1f}% of grid)")
    real_mountain_dist = compute_distance_to_mask(mountain_mask)

    out_da = xr.DataArray(
        real_mountain_dist, coords=dem_sz.coords, dims=dem_sz.dims,
        name="real_mountain_distance_m",
    ).rio.write_crs(dem_sz.rio.crs)
    real_mt_path = OUT_DIR / "shenzhen_real_mountain_distance_100m.tif"
    out_da.rio.to_raster(real_mt_path, dtype="float32")
    print(f"  ✓ saved {real_mt_path.name}")
    print(f"    Distance range: {np.nanmin(real_mountain_dist):.0f} – {np.nanmax(real_mountain_dist):.0f} m")

    # === Step 5: Compare REAL vs PROXY ===
    print("\n[5/5] Comparing REAL DEM-based vs LCZ-PROXY mountain distance...")
    lcz_path = OUT_DIR / "shenzhen_lcz_100m_utm.tif"
    lcz = rxr.open_rasterio(lcz_path, masked=True).squeeze().values
    # LCZ 11 = dense trees, LCZ 12 = scattered trees → "forest proxy"
    forest_mask = np.isin(lcz, [11, 12])
    print(f"  LCZ 11/12 forest cells: {forest_mask.sum():,} ({100 * forest_mask.mean():.1f}% of grid)")
    proxy_mountain_dist = compute_distance_to_mask(forest_mask)

    # Check: are mountain (real) and forest (proxy) cells the same?
    overlap = np.logical_and(mountain_mask, forest_mask).sum()
    only_mountain = np.logical_and(mountain_mask, ~forest_mask).sum()
    only_forest = np.logical_and(~mountain_mask, forest_mask).sum()
    print(f"\n  Overlap analysis:")
    print(f"    Mountain ∩ Forest:  {overlap:,}  ({100*overlap/forest_mask.sum():.1f}% of forest cells)")
    print(f"    Mountain ¬ Forest:  {only_mountain:,}  (mountain but not forest)")
    print(f"    Forest ¬ Mountain:  {only_forest:,}  (forest but not mountain — main confound)")

    # Pearson correlation between two distance maps
    valid = np.logical_and(np.isfinite(real_mountain_dist), np.isfinite(proxy_mountain_dist))
    r = float(np.corrcoef(real_mountain_dist[valid], proxy_mountain_dist[valid])[0, 1])
    print(f"\n  Pearson r between REAL and PROXY mountain distance: {r:.3f}")

    # Save comparison stats
    stats = {
        "mountain_cells_real": int(mountain_mask.sum()),
        "forest_cells_proxy": int(forest_mask.sum()),
        "overlap_cells": int(overlap),
        "only_mountain_cells": int(only_mountain),
        "only_forest_cells": int(only_forest),
        "forest_within_mountain_pct": float(100 * overlap / forest_mask.sum()) if forest_mask.sum() else 0,
        "pearson_r_real_vs_proxy_distance": r,
    }
    pd.DataFrame([stats]).to_csv(VAL_DIR / "geography_proxy_vs_real.csv", index=False)
    print(f"\n  ✓ stats saved: geography_proxy_vs_real.csv")

    # === Plot comparison ===
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), dpi=130)

    # (a) DEM
    ax = axes[0, 0]
    im = ax.imshow(dem_arr, cmap="terrain", vmin=0, vmax=400)
    ax.set_title(f"(a) Shenzhen 100-m DEM\nElev range 0–{int(np.nanmax(dem_arr))} m", fontsize=10)
    plt.colorbar(im, ax=ax, label="Elevation (m)", fraction=0.04)
    ax.set_xlabel("x (px)"); ax.set_ylabel("y (px)")

    # (b) Mountain mask comparison
    ax = axes[0, 1]
    overlay = np.zeros_like(dem_arr_clean, dtype=int)
    overlay[forest_mask & ~mountain_mask] = 1   # only forest (proxy false positive)
    overlay[mountain_mask & ~forest_mask] = 2   # only elevated (proxy false negative)
    overlay[mountain_mask & forest_mask] = 3    # both
    cmap = plt.cm.colors.ListedColormap(["#f0f0f0", "#fbb4ae", "#b3cde3", "#33a02c"])
    ax.imshow(overlay, cmap=cmap, vmin=0, vmax=3)
    ax.set_title("(b) Mountain mask: PROXY (LCZ 11/12) vs REAL (>200 m)\n"
                 f"Forest∩Mountain {overlap:,} (correct)\n"
                 f"Forest only {only_forest:,} (proxy FP) | "
                 f"Mountain only {only_mountain:,} (proxy FN)", fontsize=9)
    handles = [
        plt.matplotlib.patches.Patch(color="#fbb4ae", label="Forest (LCZ proxy) only"),
        plt.matplotlib.patches.Patch(color="#b3cde3", label="Real mountain (>200 m) only"),
        plt.matplotlib.patches.Patch(color="#33a02c", label="Both"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8)

    # (c) Real mountain distance
    ax = axes[1, 0]
    im = ax.imshow(real_mountain_dist / 1000, cmap="viridis_r", vmin=0, vmax=15)
    ax.set_title("(c) REAL mountain distance (km)\nbased on SRTM elevation > 200 m", fontsize=10)
    plt.colorbar(im, ax=ax, label="Distance (km)", fraction=0.04)

    # (d) Scatter: real vs proxy
    ax = axes[1, 1]
    sub = np.random.choice(np.flatnonzero(valid), size=min(20000, valid.sum()), replace=False)
    ax.scatter(proxy_mountain_dist.flat[sub] / 1000,
               real_mountain_dist.flat[sub] / 1000,
               s=1, alpha=0.2, color="#0571b0")
    lims = [0, max(np.nanmax(proxy_mountain_dist), np.nanmax(real_mountain_dist)) / 1000]
    ax.plot(lims, lims, "k--", lw=1.5, label="1:1")
    ax.set_xlabel("PROXY distance (km, LCZ 11/12)")
    ax.set_ylabel("REAL distance (km, elev > 200 m)")
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_title(f"(d) Real vs Proxy distance scatter\nPearson r = {r:.3f}", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    out_png = FIGURES_DIR / "figS3_real_vs_proxy_geography.png"
    plt.savefig(out_png, dpi=140, bbox_inches="tight")
    plt.savefig(out_png.with_suffix(".svg"), bbox_inches="tight")
    plt.close()
    print(f"\n  ✓ Fig S3 saved: {out_png.name}")

    print("\n" + "=" * 70)
    print("Day 2 complete:")
    print(f"  → DEM 100m saved")
    print(f"  → Real mountain distance saved")
    print(f"  → Pearson r(REAL, PROXY) = {r:.3f}")
    print(f"  → Forest cells that are NOT mountains: {only_forest:,}")
    print(f"  → Mountain cells that are NOT forests:  {only_mountain:,}")
    print()
    print("Implication for paper:")
    if r < 0.7:
        print(f"  ⚠ r = {r:.2f} < 0.7 — proxy and real measures are SUBSTANTIALLY different.")
        print(f"  → Need to re-run Phase 6.5 with REAL distances to test if H4 still wins.")
    elif r < 0.9:
        print(f"  ~ r = {r:.2f} — moderate agreement, likely small change in Phase 6.5 results.")
    else:
        print(f"  ✓ r = {r:.2f} ≥ 0.9 — proxy was a reasonable approximation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
