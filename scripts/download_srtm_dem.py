"""
Download SRTM 30-m DEM tiles for the 3 GBA cities (Shenzhen, Guangzhou, Dongguan).

Sources:
  Primary: USGS EarthExplorer (requires NASA Earthdata account)
  Alternative: OpenTopography (https://opentopography.org) — programmatic API
  Alternative: AWS Open Data (s3://elevation-tiles-prod/) — public bucket

For Issue 2 (Major Revision): replace LCZ-11/12-distance proxy with real
elevation-based mountain distance and slope; replace LCZ-17-distance with
real OSM coastline distance.

Usage:
    python scripts/download_srtm_dem.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import urllib.request
import zipfile

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "external" / "srtm30"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# SRTM 1-arc-second (~30 m) tile coverage for 3 GBA cities
# Tile naming: NXXEYYY where N/S = lat sign, E/W = lon sign, XX/YYY = absolute degrees
# A single SRTM tile covers 1° × 1° starting at the named SW corner
TILES = [
    "N22E113",  # Covers 22-23°N, 113-114°E — Macao, west Guangzhou, west Shenzhen
    "N22E114",  # Covers 22-23°N, 114-115°E — east Shenzhen, Hong Kong
    "N23E113",  # Covers 23-24°N, 113-114°E — Guangzhou, Foshan
    "N23E114",  # Covers 23-24°N, 114-115°E — Dongguan, Huizhou edges
]


def try_aws_terrain(tile: str) -> Path | None:
    """Try to download SRTM tile from AWS Open Data (no auth)."""
    # AWS Open Data SRTM mirror pattern
    url = f"https://s3.amazonaws.com/elevation-tiles-prod/skadi/{tile[:3]}/{tile}.hgt.gz"
    out = OUT_DIR / f"{tile}.hgt.gz"
    if out.exists():
        print(f"  ✓ already have {tile}")
        return out
    try:
        print(f"  downloading {tile} from AWS Open Data...")
        req = urllib.request.Request(url, headers={"User-Agent": "WUDAPT-FUSE/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(out, "wb") as f:
            f.write(r.read())
        size = out.stat().st_size / 1e6
        print(f"    ✓ saved {tile}.hgt.gz ({size:.1f} MB)")
        return out
    except Exception as e:
        print(f"    ✗ AWS failed: {type(e).__name__}: {e}")
        out.unlink(missing_ok=True)
        return None


def try_opentopography(tile: str) -> Path | None:
    """Try OpenTopography API (free, no key needed for SRTM)."""
    # Parse tile name to bbox
    lat0 = int(tile[1:3]) * (1 if tile[0] == "N" else -1)
    lon0 = int(tile[4:7]) * (1 if tile[3] == "E" else -1)
    south, north = lat0, lat0 + 1
    west, east = lon0, lon0 + 1

    url = (
        f"https://portal.opentopography.org/API/globaldem"
        f"?demtype=SRTMGL1&south={south}&north={north}"
        f"&west={west}&east={east}&outputFormat=GTiff"
    )
    out = OUT_DIR / f"{tile}.tif"
    if out.exists():
        print(f"  ✓ already have {tile}.tif")
        return out
    try:
        print(f"  downloading {tile} from OpenTopography...")
        req = urllib.request.Request(url, headers={"User-Agent": "WUDAPT-FUSE/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(out, "wb") as f:
            f.write(r.read())
        size = out.stat().st_size / 1e6
        if size < 0.1:
            out.unlink()
            print(f"    ✗ response too small ({size:.2f} MB)")
            return None
        print(f"    ✓ saved {tile}.tif ({size:.1f} MB)")
        return out
    except Exception as e:
        print(f"    ✗ OpenTopography failed: {type(e).__name__}: {e}")
        out.unlink(missing_ok=True)
        return None


def main():
    print("=" * 60)
    print("Download SRTM 30-m DEM for 3 GBA cities")
    print("=" * 60)
    print(f"Output dir: {OUT_DIR}")
    print()

    success = 0
    for tile in TILES:
        print(f"\n[{tile}]")
        # Try methods in order
        result = try_aws_terrain(tile) or try_opentopography(tile)
        if result is not None:
            success += 1
        else:
            print(f"  ⚠ All sources failed for {tile}")
            print(f"    Manual fallback: download via")
            print(f"    https://earthexplorer.usgs.gov/ (need free NASA Earthdata account)")
            print(f"    Search: SRTM 1-arc-second Global, tile {tile}")

    print()
    print("=" * 60)
    print(f"Result: {success}/{len(TILES)} tiles downloaded")
    print("=" * 60)
    return 0 if success > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
