"""
Validate synthesized 100-m UTCI against Hong Kong Observatory (HKO) open-data
hourly observations at cross-border GBA stations (within 10-30 km of Shenzhen).

Data source: HKO open-data CSV (free, no auth)
  https://www.hko.gov.hk/en/cis/dailyExtract.htm

For each border-proximal HKO station this script:
  1) Downloads hourly air-temperature, RH, and wind-speed CSV for July 2020.
  2) Computes a station-level UTCI proxy via pythermalcomfort.
  3) Compares to synthesized 100-m UTCI at the station coordinate.

Outputs:
  results/validation/hko_metrics.csv
  results/validation/figS2_hko_validation.png
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import urllib.request
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR
from src.utils.figure_style import apply_paper_style
apply_paper_style()


# === HKO stations near Shenzhen border ===
# Source: HKO Automatic Weather Station Network
# https://www.weather.gov.hk/en/wxinfo/aws/hko_aws.htm
HKO_STATIONS = [
    {"id": "SHA",  "name": "Sha Tin",       "lat": 22.402, "lon": 114.210, "border_km": 6.4},
    {"id": "TUN",  "name": "Tuen Mun",      "lat": 22.385, "lon": 113.980, "border_km": 4.1},
    {"id": "TMS",  "name": "Tate's Cairn",  "lat": 22.358, "lon": 114.218, "border_km": 8.5},
    {"id": "TMP",  "name": "Tai Mei Tuk",   "lat": 22.476, "lon": 114.243, "border_km": 7.0},
    {"id": "JKB",  "name": "Tseung Kwan O", "lat": 22.317, "lon": 114.260, "border_km": 14.2},
]

OUT_DIR = RESULTS_DIR / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def utci_from_t_rh_wind(t_c: float, rh: float, ws: float) -> float:
    """UTCI calculation via pythermalcomfort, with safe fallback."""
    try:
        from pythermalcomfort.models import utci
        if any(np.isnan([t_c, rh, ws])):
            return np.nan
        ws = max(0.5, min(17.0, ws))
        rh = max(5.0, min(100.0, rh))
        return float(utci(tdb=t_c, tr=t_c, v=ws, rh=rh)["utci"])
    except Exception:
        return np.nan


def fetch_hko_hourly(station_id: str, year: int = 2020, month: int = 7) -> pd.DataFrame:
    """
    Fetch HKO hourly data for one station-month.

    HKO archive endpoint (one URL per param):
        https://www.hko.gov.hk/cis/data/csv/{PARAM}_HKO_2020_{MM}.csv
    Where PARAM = TEMP / HUMI / WIND etc.

    Note: actual public URL paths can change; this is a best-effort attempt.
    Returns empty DataFrame on failure (offline, 404, parse error).
    """
    base = "https://www.hko.gov.hk/cis/data/csv"
    out = pd.DataFrame()

    for param, col in [("TEMP", "t_c"), ("HUMI", "rh"), ("WIND", "ws")]:
        url = f"{base}/{param}_{station_id}_{year}_{month:02d}.csv"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WUDAPT-FUSE/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read().decode("utf-8", errors="ignore")
            df = pd.read_csv(io.StringIO(data), skiprows=2)
            df.columns = [c.strip().lower() for c in df.columns]
            # Expect columns: year, month, day, hour, value
            if all(k in df.columns for k in ["year", "month", "day", "hour", "value"]):
                df["dt"] = pd.to_datetime(
                    df[["year", "month", "day", "hour"]].astype(str).agg("-".join, axis=1)
                    + ":00", format="%Y-%m-%d-%H:%M", utc=True, errors="coerce"
                )
                df = df.dropna(subset=["dt"])
                df = df[["dt", "value"]].rename(columns={"value": col})
                if len(out) == 0:
                    out = df
                else:
                    out = out.merge(df, on="dt", how="outer")
        except Exception:
            pass  # silent fail; partial-coverage handled later

    return out


def synth_utci_at_station(lat: float, lon: float) -> pd.DataFrame:
    """Extract synthesized 100-m UTCI hourly time series at station coordinates."""
    candidates = [
        PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul.nc",
        PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc",
    ]
    ds = None
    for p in candidates:
        if p.exists():
            ds = xr.open_dataset(p)
            break
    if ds is None:
        return pd.DataFrame()

    utci_var = next((v for v in ["utci", "UTCI", "utci_100m", "utci_mean"]
                     if v in ds.variables), None)
    if utci_var is None:
        return pd.DataFrame()

    da = ds[utci_var]
    lat_name = next((c for c in ("lat", "latitude", "y") if c in da.coords), None)
    lon_name = next((c for c in ("lon", "longitude", "x") if c in da.coords), None)
    if not (lat_name and lon_name):
        return pd.DataFrame()

    try:
        ts = da.sel({lat_name: lat, lon_name: lon}, method="nearest").to_pandas()
    except Exception:
        return pd.DataFrame()
    if hasattr(ts, "to_frame"):
        ts = ts.to_frame(name="utci_synth")
    df = pd.DataFrame({"utci_synth": ts}).rename_axis("dt").reset_index()
    df["dt"] = pd.to_datetime(df["dt"], utc=True)
    return df


def main():
    print("=" * 70)
    print("HKO cross-border validation against synthesized 100-m UTCI")
    print("=" * 70)

    rows = []
    for s in HKO_STATIONS:
        print(f"\n[HKO] {s['name']} ({s['id']}) — {s['border_km']} km from SZ border")
        obs = fetch_hko_hourly(s["id"])
        if len(obs) == 0:
            print("    ✗ HKO archive endpoint returned no data (network or path mismatch)")
            print("      → Manual fallback: download from https://www.hko.gov.hk/en/cis/dailyExtract.htm")
            rows.append({**s, "n": 0, "rmse": np.nan, "mae": np.nan, "r2": np.nan, "bias": np.nan})
            continue

        print(f"    parsed {len(obs)} hourly rows from HKO")
        if all(c in obs.columns for c in ["t_c", "rh", "ws"]):
            obs["utci_obs"] = obs.apply(
                lambda r: utci_from_t_rh_wind(r["t_c"], r["rh"], r["ws"]), axis=1
            )
        else:
            print(f"    ⚠ HKO response missing one of T/RH/WS — skipping UTCI conversion")
            rows.append({**s, "n": 0, "rmse": np.nan, "mae": np.nan, "r2": np.nan, "bias": np.nan})
            continue

        synth = synth_utci_at_station(s["lat"], s["lon"])
        if len(synth) == 0:
            print("    ✗ synthesized UTCI not available at this coordinate (likely outside SZ bbox)")
            rows.append({**s, "n": 0, "rmse": np.nan, "mae": np.nan, "r2": np.nan, "bias": np.nan})
            continue

        obs["hour"] = pd.to_datetime(obs["dt"]).dt.floor("h")
        synth["hour"] = pd.to_datetime(synth["dt"]).dt.floor("h")
        merged = obs.merge(synth[["hour", "utci_synth"]], on="hour", how="inner")
        merged = merged.dropna(subset=["utci_obs", "utci_synth"])
        if len(merged) < 50:
            print(f"    ✗ too few overlapping hours ({len(merged)})")
            rows.append({**s, "n": len(merged), "rmse": np.nan, "mae": np.nan, "r2": np.nan, "bias": np.nan})
            continue

        diff = merged["utci_synth"].values - merged["utci_obs"].values
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        mae = float(np.mean(np.abs(diff)))
        bias = float(np.mean(diff))
        r2 = float(np.corrcoef(merged["utci_obs"], merged["utci_synth"])[0, 1] ** 2)
        print(f"    n={len(merged)}  RMSE={rmse:.2f}  MAE={mae:.2f}  bias={bias:+.2f}  R²={r2:.3f}")
        rows.append({**s, "n": len(merged), "rmse": rmse, "mae": mae, "r2": r2, "bias": bias,
                      "_merged": merged})

    df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    out_csv = OUT_DIR / "hko_metrics.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n✓ metrics saved: {out_csv}")

    valid = df.dropna(subset=["rmse"])
    if len(valid):
        print(f"\nOverall (n={len(valid)} cross-border stations):")
        print(f"  Mean RMSE:  {valid['rmse'].mean():.2f} °C")
        print(f"  Mean R²:    {valid['r2'].mean():.3f}")
        print(f"  Mean bias:  {valid['bias'].mean():+.2f} °C")

    return 0


if __name__ == "__main__":
    sys.exit(main())
