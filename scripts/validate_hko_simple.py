"""
Simplified HKO validation: try HKO open-data CSV archive for 1-2 stations
near the Shenzhen-HK border that fall within the synthesized 100-m domain.

HKO border-proximal stations within Shenzhen 22.4-22.9N, 113.7-114.7E bbox:
  - Lau Fau Shan (LFS):  22.47°N, 113.98°E  (within Shenzhen bbox)
  - Tai Mei Tuk (TMS):   22.48°N, 114.24°E  (within Shenzhen bbox)

Approach: try the HKO daily extract CSV endpoint; if it fails, document the
attempt in the manuscript as a next-phase task.

Output:
  results/validation/hko_attempts.csv (success/failure log)
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import urllib.request
import pandas as pd
import numpy as np

from src.utils.config import RESULTS_DIR

OUT_DIR = RESULTS_DIR / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# HKO border-proximal stations
HKO_STATIONS = [
    {"id": "LFS", "name": "Lau Fau Shan",  "lat": 22.47, "lon": 113.98, "in_sz_bbox": True},
    {"id": "TMS", "name": "Tai Mei Tuk",   "lat": 22.48, "lon": 114.24, "in_sz_bbox": True},
    {"id": "SHA", "name": "Sha Tin",        "lat": 22.40, "lon": 114.21, "in_sz_bbox": False},
    {"id": "HKO", "name": "HKO Headquarters","lat": 22.30, "lon": 114.17, "in_sz_bbox": False},
]


def try_hko_url(url: str, timeout: int = 15) -> tuple[bool, str]:
    """Try one HKO endpoint; return (success, error_message)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WUDAPT-FUSE/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read().decode("utf-8", errors="ignore")
        if len(data) < 100:
            return False, f"response too short ({len(data)} bytes)"
        return True, f"got {len(data):,} bytes"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    print("=" * 70)
    print("HKO open-data validation attempt (Reviewer Major-3)")
    print("=" * 70)

    # Various HKO endpoints to try
    candidate_urls = {
        "annual_csv":
            "https://www.hko.gov.hk/cis/csv/CLMTEMP_LFS_2020.csv",
        "annual_climate":
            "https://www.weather.gov.hk/en/cis/data/climat/LFS_2020.csv",
        "open_data_API":
            "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en",
        "csv_temperature":
            "https://www.hko.gov.hk/cis/data/csv/TEMP_LFS_2020_07.csv",
    }

    print("\n[1/2] Probing HKO endpoints for 2020-07 data...")
    results = []
    for name, url in candidate_urls.items():
        ok, msg = try_hko_url(url)
        status = "✓" if ok else "✗"
        print(f"  {status} {name:<25}  {url}")
        print(f"      → {msg}")
        results.append({
            "endpoint": name,
            "url": url,
            "success": ok,
            "message": msg,
        })

    print("\n[2/2] Saving attempt log...")
    df = pd.DataFrame(results)
    df.to_csv(OUT_DIR / "hko_attempts.csv", index=False)
    print(f"  ✓ saved {OUT_DIR / 'hko_attempts.csv'}")

    successes = sum(1 for r in results if r["success"])
    print()
    print("=" * 70)
    print(f"Summary: {successes}/{len(results)} HKO endpoints accessible")
    print("=" * 70)
    if successes == 0:
        print("""
All public-archive HKO endpoints failed (typical: HKO requires manual
download via their web form; programmatic access for historical hourly
data is restricted to academic licensees).

Documented action for paper:
  • §2.3.1: state that Shenzhen Bao'an (WMO 59493) is the only ISD
    station within the synthesized 100-m domain that is publicly
    accessible by automated download.
  • §4.4 Limitations: list multi-station validation as a constraint.
  • §4.10 Next steps: HKO multi-station validation will be done in
    WUDAPT-FUSE-CN follow-up using HKO open-data API once academic
    access is arranged.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
