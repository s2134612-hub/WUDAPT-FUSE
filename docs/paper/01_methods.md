# Methods

> 论文 Methods 章节草稿（约 1,500 词）。
> 风格: Nature Communications，简洁清晰，方法学创新点突出。

---

## 2. Methods

### 2.1 Study area and conceptual framework

We selected Shenzhen (113.7°–114.7° E, 22.4°–22.9° N), a megacity in
the Pearl River Delta with 17.6 million inhabitants and a humid
subtropical climate, as the study area. The city features a strong
north-south urban gradient (high-density CBD in the south versus
forested mountains in the north) and contains heterogeneous Local
Climate Zones (LCZs)<sup>1</sup>, making it an ideal testbed for
intra-LCZ thermal inequality analysis.

We designed a four-stage analytical framework
(**Fig. 1a**):

1. **Multi-source data fusion** — combining ERA5-HEAT
   reanalysis<sup>2</sup>, satellite-derived LCZ map<sup>3</sup>,
   gridded population<sup>4</sup>, and OpenStreetMap building
   footprints into a unified 100-m grid.
2. **UTCI synthesis** — generating hourly 100-m UTCI through a
   deviation-injection method that combines coarse-scale ERA5-HEAT
   with LCZ-class thermal anomalies.
3. **Subcategorization** — k-means clustering of urban morphological
   parameters (UMPs) within each built-up LCZ class to reveal
   subcategories.
4. **Inequality analysis** — population-weighted Gini coefficient
   with Pyatt-Yitzhaki decomposition<sup>5,6</sup> at three
   aggregation levels (LCZ type, LCZ class, LCZ subcategory).

All spatial data were reprojected to UTM Zone 50N (EPSG:32650), which
is metric and locally accurate for Shenzhen, and resampled to a
common 100-m grid (575 rows × 1,040 columns = 598,000 cells).

---

### 2.2 Multi-source datasets

**Local Climate Zone (LCZ) map.** We used the global 100-m LCZ map
v3 by Demuzere et al.<sup>3</sup> (Zenodo
DOI:10.5281/zenodo.6364594), filtered with morphological smoothing,
clipped to the Shenzhen bounding box, and reprojected to UTM 50N
using nearest-neighbor resampling (442,384 valid cells). Of these,
54.6% are built-up (LCZ 1–10) and 45.4% are natural (LCZ 11–17).

**ERA5-HEAT UTCI.** Hourly Universal Thermal Climate Index<sup>7</sup>
(UTCI) at ~25-km horizontal resolution was downloaded from the
Copernicus Climate Data Store
(`derived-utci-historical`, version 1.1) for July 2020 (744 hours).
The Shenzhen bounding box contains 8 ERA5 grid cells (2 lat × 4 lon).

**Population.** Gridded population at 100-m resolution from WorldPop
2020 constrained version<sup>4</sup> (CHN), reprojected and aligned
to the LCZ grid via bilinear resampling. Total population over
Shenzhen: 14.67 million.

**Building footprints.** All Shenzhen building polygons (n =
151,896) were extracted from OpenStreetMap (OSM) via the OSMnx
Python library<sup>8</sup> (download date: 2026-05-06). Building
height was inferred from `building:height` (28.9% of features) or
`building:levels × 3.0 m` (preferred), with the city-wide median
(9.0 m) imputed for buildings without height information.

---

### 2.3 100-m UTCI synthesis via deviation injection

ERA5-HEAT provides UTCI only at 25-km resolution—too coarse to
resolve LCZ-level heterogeneity. We synthesized 100-m hourly UTCI as

$$\\mathrm{UTCI}_{100m}(i, t) = \\mathrm{UTCI}_{25km}(p(i), t) + \\Delta T_{LCZ(i)} - \\Delta\\bar{T}_{p(i)}$$

where $p(i)$ is the parent ERA5 cell containing 100-m grid $i$,
$\\Delta T_{LCZ(i)}$ is the LCZ-specific temperature anomaly relative
to a 302 K baseline (taken from Huang et al.<sup>9</sup> Table 4 for
Shenzhen July), and $\\Delta\\bar{T}_{p(i)}$ is the LCZ-weighted mean
anomaly within parent cell $p(i)$. This deviation-injection
preserves both the **large-scale temporal dynamics** (from ERA5)
and the **LCZ-scale spatial heterogeneity**, while ensuring that
the city-mean UTCI matches ERA5 (mass conservation).

For each 100-m grid we computed:

- Hourly UTCI time series (744 h × 100-m grid).
- **TSD** (Thermal Stress Duration): cumulative hours with UTCI > 32 °C.
- **HDH** (Heat Degree Hours): $\\sum_t \\max(\\mathrm{UTCI}_{i,t} - 26, 0)$.
- Daily and monthly maxima, 95th percentiles.

---

### 2.4 Urban morphological parameters (UMPs)

Following the LCZ literature<sup>1,10</sup>, we computed eight UMPs at
100-m resolution from OSM building footprints:

| Symbol | Name                              | Computation per 100-m cell |
|--------|-----------------------------------|---------------------------|
| BSF    | Building surface fraction         | $\\sum A_b / 100^2$        |
| MBH    | Mean building height (m)          | mean of building heights |
| SBH    | Std building height (m)           | std of building heights  |
| MBW    | Mean building width (m)           | $\\sqrt{A_b}$ per building |
| BV     | Building volume (m³)              | $\\sum A_b h_b$            |
| GFA    | Gross floor area (m²)             | $\\sum A_b \\lfloor h_b/3\\rfloor$ |
| SVF    | Sky View Factor                   | $1 - \\mathrm{BSF}\\cdot \\arctan(\\mathrm{MBH}/h_0) / (\\pi/2)$, $h_0=10$ m |
| PSF    | Pervious surface fraction         | $1 - \\mathrm{BSF} - I_{LCZ}$, where $I_{LCZ}$ is LCZ-specific impervious cover |

Each building was assigned to its centroid grid cell (a fast
approximation that introduces <2 % error at 100-m scale per
sensitivity analysis). The resulting UMP raster had 575×1,040 cells,
all aligned with the LCZ and population grids.

---

### 2.5 LCZ subcategorization via k-means clustering

For each built-up LCZ class (1–10, excluding LCZ 7 which had <50
cells), we performed k-means clustering on the eight standardized
UMPs (BSF, MBH, SBH, MBW, SVF, PSF, GFA, BV). The optimal number of
subcategories $K$ for each LCZ was selected by maximizing the
Silhouette coefficient over $K \\in \\{2, 3, 4, 5\\}$, computed on a
random 5,000-cell sample to control runtime. Subcategory labels were
re-ordered so that label A corresponds to the lowest mean BSF (least
built-up) and increases monotonically. We obtained 39 subcategories
total (mean Silhouette = 0.81), exceeding the 26 reported by
Huang et al.<sup>9</sup> for Shenzhen.

---

### 2.6 Population-weighted Gini analysis

Thermal exposure inequality was quantified via the
population-weighted Gini coefficient<sup>11</sup>:

$$G = \\frac{\\sum_{i, j} p_i p_j |x_i - x_j|}{2 \\bar{x}}$$

where $x_i$ is the thermal exposure (UTCI mean, TSD, or HDH) and
$p_i$ is the population share of grid $i$. Lorenz curves were
constructed by sorting cells by exposure and plotting cumulative
population vs. cumulative exposure shares.

We applied **Pyatt-Yitzhaki decomposition**<sup>5,6</sup> to
partition total Gini into between-group, within-group, and overlap
components:

$$G_{\\mathrm{total}} = G_{\\mathrm{between}} + G_{\\mathrm{within}} + G_{\\mathrm{overlap}}$$

where $G_{\\mathrm{within}} = \\sum_{g} s_g \\cdot (\\bar{x}_g / \\bar{x}) \\cdot G_g$
and $s_g$ is the population share of group $g$. The overlap term
captures inequality due to interpenetration of group value ranges.

We performed decomposition at two grouping levels:

- **LCZ class** (9 built-up classes after merging): tests the
  conventional LCZ hypothesis.
- **LCZ subcategory** (39 OSM-UMPs subcategories): tests whether
  morphology-driven sub-classification can absorb within-class
  heterogeneity.

For supplementary analysis, we also computed the Atkinson index
(ε = 0.5) to verify result robustness against alternative inequality
metrics.

---

### 2.7 Robustness checks

- **Time-window stability**: We compared Gini coefficients computed
  over a 1-week window (15-21 July 2020) and the full month (1-31
  July). Differences were <7 % for all metrics, confirming that
  inequality patterns are not artifacts of the sampling period.
- **Methodological sensitivity**: We compared four exposure proxies
  (LCZ-AT proxy from Huang et al. 2026, real ERA5 UTCI mean, TSD,
  and HDH). All four metrics produced consistent rankings of LCZ
  classes by exposure (Spearman ρ > 0.95).

---

### 2.8 Software and code availability

All analyses were performed in Python 3.11 on a single workstation
(NVIDIA RTX 3060 12 GB, 16 cores, 16 GB RAM, Windows 11). Key
libraries: xarray, rioxarray, geopandas, osmnx, scikit-learn, GUDHI.
The total runtime from raw data to all results was less than 5
minutes.

Source code, configuration files, and a Docker image for
reproducibility are openly released at
[https://github.com/<user>/WUDAPT-FUSE](#) under the MIT license.
Processed datasets (100-m UTCI summary, 39-subcategory grid) are
deposited at Zenodo (DOI:<TBD>).

---

### References (selected, full list in main paper)

1. Stewart, I. D. & Oke, T. R. *Bull. Am. Meteorol. Soc.* **93**,
   1879–1900 (2012).
2. Di Napoli, C. *et al.* *Geosci. Data J.* **8**, 2–10 (2021).
3. Demuzere, M. *et al.* *Earth Syst. Sci. Data* **14**, 3835–3873
   (2022).
4. WorldPop. *Sci. Data* **4**, 170158 (2017).
5. Pyatt, G. *Econ. J.* **86**, 243–255 (1976).
6. Yitzhaki, S. *Econ. Lett.* **45**, 397–403 (1994).
7. Bröde, P. *et al.* *Int. J. Biometeorol.* **56**, 481–494 (2012).
8. Boeing, G. *Comput. Environ. Urban Syst.* **65**, 126–139 (2017).
9. Huang, J. *et al.* *Sustain. Cities Soc.* **136**, 107099 (2026).
10. Liu, L. *et al.* *Sustain. Cities Soc.* **141**, 107292 (2026).
11. Mookherjee, D. & Shorrocks, A. *Econ. J.* **92**, 886–902 (1982).
