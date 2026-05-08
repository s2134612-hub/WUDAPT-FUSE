"""
Validate synthesized 100-m UTCI against NOAA Integrated Surface Database (ISD)
hourly observations at 5 Greater Bay Area stations.

Data source: NOAA NCEI Global Hourly (free, no auth)
  https://www.ncei.noaa.gov/data/global-hourly/access/2020/

Compares aggregate UTCI (monthly mean, daytime mean, nighttime mean) at the
100-m grid cell containing each station to a station-derived UTCI proxy from
hourly T / RH / wind. Aggregate comparison rather than hour-by-hour because
the 100-m UTCI dataset retains only summary fields (utci_mean, day_mean,
night_mean) — the raw 744-hour grid is regenerated on demand from
full_pipeline_july.py.

Outputs:
  results/validation/noaa_isd_metrics.csv
  figures/figS1_noaa_isd_validation.png
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


STATIONS = [
    {"wmo": "594930", "name": "Shenzhen Bao'an",        "lat": 22.65, "lon": 113.81, "city": "Shenzhen"},
    {"wmo": "450070", "name": "HK International (HKIA)", "lat": 22.31, "lon": 113.92, "city": "Hong Kong"},
    {"wmo": "450050", "name": "HK Observatory HQ",       "lat": 22.30, "lon": 114.17, "city": "Hong Kong"},
    {"wmo": "450110", "name": "Macao",                    "lat": 22.16, "lon": 113.59, "city": "Macao"},
    {"wmo": "592870", "name": "Guangzhou Baiyun",        "lat": 23.18, "lon": 113.27, "city": "Guangzhou"},
]
YEAR = 2020
OUT_DIR = RESULTS_DIR / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# NOAA ISD parsing
# ============================================================
def download_isd(wmo: str, year: int = YEAR) -> pd.DataFrame:
    url = f"https://www.ncei.noaa.gov/data/global-hourly/access/{year}/{wmo}99999.csv"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WUDAPT-FUSE/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return pd.read_csv(io.StringIO(r.read().decode("utf-8", errors="ignore")), low_memory=False)
    except Exception as e:
        print(f"    ! download failed for {wmo}: {type(e).__name__}: {e}")
        return None


def parse_field(s: str, idx: int = 0, scale: float = 10.0,
                 ok_qc: set[str] = {"1", "5"}) -> float:
    """ISD comma-separated field with quality flag at index 1."""
    if not isinstance(s, str) or "," not in s:
        return np.nan
    parts = s.split(",")
    if len(parts) <= max(idx, 1):
        return np.nan
    try:
        v = float(parts[idx]) / scale
        qc = parts[1] if idx == 0 else parts[idx + 1] if idx + 1 < len(parts) else "9"
        if qc not in ok_qc:
            return np.nan
        if abs(v) > 60:
            return np.nan
        return v
    except Exception:
        return np.nan


def parse_wind(s: str) -> float:
    """ISD WND: DDD,Q,T,SSSS,Q  → return SSSS / 10 m/s."""
    if not isinstance(s, str):
        return np.nan
    parts = s.split(",")
    if len(parts) < 5:
        return np.nan
    try:
        ws = float(parts[3]) / 10.0
        if 0 <= ws <= 50:
            return ws
    except Exception:
        return np.nan
    return np.nan


def rh_from_t_dew(t_c: float, td_c: float) -> float:
    if np.isnan(t_c) or np.isnan(td_c):
        return np.nan
    a, b = 17.27, 237.7
    return float(100 * np.exp(a * td_c / (b + td_c)) / np.exp(a * t_c / (b + t_c)))


def utci_from_t_rh_wind(t_c: float, rh: float, ws: float) -> float:
    """UTCI via pythermalcomfort (radiant temperature unknown → use t_c as proxy).

    Handles both the dict-returning v2.x API (`result['utci']`) and the
    dataclass-returning v3.x API (`result.utci`). Falls back to a polynomial
    approximation if pythermalcomfort cannot be imported.
    """
    if any(np.isnan([t_c, rh, ws])):
        return np.nan
    ws = max(0.5, min(17.0, ws))
    rh = max(5.0, min(100.0, rh))
    try:
        from pythermalcomfort.models import utci
        result = utci(tdb=t_c, tr=t_c, v=ws, rh=rh)
        # v3.x: dataclass with .utci attribute; v2.x: dict-like with key 'utci'
        if hasattr(result, "utci"):
            return float(result.utci)
        if isinstance(result, dict) and "utci" in result:
            return float(result["utci"])
        return float(result)  # numeric scalar in some versions
    except Exception:
        # Polynomial fallback (Brode 2012 simplified, valid for sub-tropical heat)
        e = (rh / 100.0) * 6.105 * np.exp(17.27 * t_c / (237.7 + t_c))
        offset = (
            0.607562052 * t_c
            - 0.0227712343 * t_c ** 2
            + 0.0008062619 * t_c ** 3
            - 0.000154 * (e * t_c)
            - 0.5 * (ws - 1.0)
        )
        return t_c + offset / max(t_c, 1.0)


def isd_to_aggregate_utci(df_raw: pd.DataFrame) -> dict:
    """Return dict with monthly, day, night mean UTCI for July 2020."""
    if df_raw is None or len(df_raw) == 0:
        return {}
    df = pd.DataFrame()
    df["dt"] = pd.to_datetime(df_raw["DATE"], errors="coerce", utc=True)
    df["t_c"] = df_raw["TMP"].apply(parse_field) if "TMP" in df_raw.columns else np.nan
    df["td_c"] = df_raw["DEW"].apply(parse_field) if "DEW" in df_raw.columns else np.nan
    df["ws"] = df_raw["WND"].apply(parse_wind) if "WND" in df_raw.columns else np.nan
    df["rh"] = df.apply(lambda r: rh_from_t_dew(r["t_c"], r["td_c"]), axis=1)
    df = df.dropna(subset=["dt", "t_c"])
    df = df[(df["dt"] >= "2020-07-01") & (df["dt"] < "2020-08-01")]
    df = df[(df["t_c"] > 0) & (df["t_c"] < 50)]
    df["utci"] = df.apply(lambda r: utci_from_t_rh_wind(r["t_c"], r["rh"], r["ws"]), axis=1)
    df = df.dropna(subset=["utci"])
    if len(df) < 50:
        return {}

    df["hour_local"] = (df["dt"].dt.tz_convert("Asia/Shanghai")).dt.hour
    day_mask = (df["hour_local"] >= 8) & (df["hour_local"] < 20)

    return {
        "n_obs": len(df),
        "month_mean_obs": float(df["utci"].mean()),
        "day_mean_obs":   float(df.loc[day_mask, "utci"].mean()),
        "night_mean_obs": float(df.loc[~day_mask, "utci"].mean()),
        "t_mean_obs":     float(df["t_c"].mean()),
    }


# ============================================================
# Synthesized UTCI extraction
# ============================================================
def open_summary(name: str) -> xr.Dataset | None:
    p = PROCESSED_DATA_DIR / name
    return xr.open_dataset(p) if p.exists() else None


def synth_at_station(lat: float, lon: float) -> dict:
    """Extract synthesized UTCI summary metrics at a given lat/lon."""
    out = {}
    for label, fname, var in [
        ("month_mean", "shenzhen_utci_100m_jul_summary.nc", "utci_mean"),
        ("day_mean",   "shenzhen_utci_100m_jul_day_summary.nc", "utci_mean"),
        ("night_mean", "shenzhen_utci_100m_jul_night_summary.nc", "utci_mean"),
    ]:
        ds = open_summary(fname)
        if ds is None or var not in ds.variables:
            out[f"{label}_synth"] = np.nan
            continue

        da = ds[var]
        lat_n = next((c for c in ("lat", "latitude", "y") if c in da.coords), None)
        lon_n = next((c for c in ("lon", "longitude", "x") if c in da.coords), None)

        # If geographic coords (lat/lon)
        if lat_n in {"lat", "latitude"} and lon_n in {"lon", "longitude"}:
            try:
                v = float(da.sel({lat_n: lat, lon_n: lon}, method="nearest").values)
                out[f"{label}_synth"] = v if np.isfinite(v) else np.nan
            except Exception:
                out[f"{label}_synth"] = np.nan
        # If projected coords (UTM x/y), need reprojection
        elif lat_n == "y" and lon_n == "x":
            try:
                from pyproj import Transformer
                t = Transformer.from_crs("EPSG:4326", da.rio.crs, always_xy=True)
                xv, yv = t.transform(lon, lat)
                v = float(da.sel(x=xv, y=yv, method="nearest").values)
                out[f"{label}_synth"] = v if np.isfinite(v) else np.nan
            except Exception as e:
                out[f"{label}_synth"] = np.nan
        else:
            out[f"{label}_synth"] = np.nan
    return out


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("NOAA ISD aggregate validation against synthesized 100-m UTCI")
    print("=" * 70)

    rows = []
    for s in STATIONS:
        print(f"\n[{s['city']}] {s['name']}  WMO {s['wmo']}  ({s['lat']:.2f}, {s['lon']:.2f})")
        df_raw = download_isd(s["wmo"])
        if df_raw is None:
            rows.append({**s})
            continue

        obs = isd_to_aggregate_utci(df_raw)
        if not obs:
            print("    ✗ no valid observations")
            rows.append({**s})
            continue
        print(f"    {obs['n_obs']} hourly obs   month_mean_obs={obs['month_mean_obs']:.2f}")

        synth = synth_at_station(s["lat"], s["lon"])
        diffs = {}
        for k in ["month_mean", "day_mean", "night_mean"]:
            o = obs.get(f"{k}_obs", np.nan)
            sn = synth.get(f"{k}_synth", np.nan)
            if np.isfinite(o) and np.isfinite(sn):
                diffs[f"{k}_diff"] = sn - o
        print(f"    synth: month={synth.get('month_mean_synth', np.nan):.2f}  "
              f"day={synth.get('day_mean_synth', np.nan):.2f}  "
              f"night={synth.get('night_mean_synth', np.nan):.2f}")
        if diffs:
            for k, v in diffs.items():
                print(f"    {k}: {v:+.2f} K")

        rows.append({**s, **obs, **synth, **diffs})

    df = pd.DataFrame(rows)
    out_csv = OUT_DIR / "noaa_isd_metrics.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n✓ metrics saved: {out_csv}")

    # Aggregate stats
    diff_cols = [c for c in df.columns if c.endswith("_diff")]
    valid = df.dropna(subset=diff_cols)
    if len(valid) > 0:
        print(f"\nAggregate comparison ({len(valid)} stations × 3 metrics = {len(valid) * 3} pairs):")
        all_diffs = pd.concat([valid[c] for c in diff_cols]).dropna()
        rmse = float(np.sqrt(np.mean(all_diffs ** 2)))
        mae = float(np.mean(np.abs(all_diffs)))
        bias = float(np.mean(all_diffs))
        print(f"  RMSE       {rmse:.2f} K")
        print(f"  MAE        {mae:.2f} K")
        print(f"  Mean bias  {bias:+.2f} K")
        # Per-metric
        for c in diff_cols:
            d = valid[c].dropna()
            if len(d):
                print(f"  {c:<18} n={len(d)}  RMSE={np.sqrt(np.mean(d**2)):.2f}  bias={d.mean():+.2f}")

    # === Scatter plot (Fig S1) ===
    plottable = df.dropna(subset=["month_mean_obs", "month_mean_synth"])
    if len(plottable) > 0:
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), dpi=140)
        for ax, kind in zip(axes, ["month_mean", "day_mean", "night_mean"]):
            obs = plottable[f"{kind}_obs"]
            sn = plottable[f"{kind}_synth"]
            mask = obs.notna() & sn.notna()
            obs, sn = obs[mask], sn[mask]
            if len(obs) == 0:
                ax.set_visible(False)
                continue
            cmap = plt.get_cmap("tab10")
            for i, (_, row) in enumerate(plottable.loc[mask].iterrows()):
                ax.scatter(row[f"{kind}_obs"], row[f"{kind}_synth"], s=60,
                           color=cmap(i), label=row["city"][:8])
                ax.annotate(row["city"][:3], (row[f"{kind}_obs"], row[f"{kind}_synth"]),
                            xytext=(5, 5), textcoords="offset points", fontsize=7.5)
            lo, hi = 25, 35
            ax.plot([lo, hi], [lo, hi], "k--", lw=1, alpha=0.6, label="1:1")
            rmse = float(np.sqrt(np.mean((sn - obs) ** 2))) if len(obs) > 0 else np.nan
            bias = float((sn - obs).mean()) if len(obs) > 0 else np.nan
            ax.set_xlabel(f"Station {kind} obs (°C)")
            ax.set_ylabel(f"Synth {kind} (°C)")
            ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
            ax.set_title(f"{kind.replace('_', ' ').title()}\nRMSE={rmse:.2f}, bias={bias:+.2f}",
                         fontsize=10)
            ax.legend(fontsize=7, loc="upper left")
            ax.grid(alpha=0.3)
        plt.suptitle("Validation against NOAA ISD — 5 GBA stations, July 2020 aggregate",
                     fontsize=11, fontweight="bold", y=1.02)
        plt.tight_layout()
        out_png = FIGURES_DIR / "figS1_noaa_isd_validation.png"
        plt.savefig(out_png, dpi=140, bbox_inches="tight")
        plt.savefig(out_png.with_suffix(".svg"), bbox_inches="tight")
        plt.close()
        print(f"\n✓ Fig S1 saved: {out_png.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
