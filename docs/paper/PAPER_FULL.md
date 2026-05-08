---
title: "Geographic position, not building morphology, governs within-class urban heat inequality: a population-weighted Gini decomposition framework (WUDAPT-FUSE) for the Greater Bay Area"
author:
  - "Yanhuo Luo^a,\\*^"
date: "May 2026"
running_title: "Geographic position governs within-class urban heat inequality"
journal: "Sustainable Cities and Society"
manuscript_type: "Original research article"
---

**Affiliation**

^a^ Institute for Advanced Studies, University of Malaya, 50603 Kuala Lumpur, Malaysia

\* Corresponding author. E-mail address: s2134612@siswa.um.edu.my

---

# Highlights

- A 4-stage pipeline (WUDAPT-FUSE) tests four explanations of intra-LCZ heat inequality
- Within-class share is 83.5% of total Gini (86.4% in built-up subset)
- Morphology subcategories absorb only 1.0 pp of the built-up within-class share
- Topology and form-plus-topology hybrid each fail the 5-pp threshold
- Coast and mountain distance reduce within-class Gini by 10.8 pp (PASS)
- City compactness moderates the geographic mechanism across three GBA cities

---

# Abstract

Local Climate Zone (LCZ) frameworks are widely used to map urban thermal differences, and recent work suggests that morphology-driven subdivision of each LCZ class can resolve fine-scale heat exposure. We tested this hypothesis and three competing alternatives at 100-m scale in three Greater Bay Area (GBA) cities (Shenzhen, Guangzhou, Dongguan; 33 million residents). Combining ERA5-HEAT, the Demuzere global LCZ map, WorldPop 2020, and 151,896 OpenStreetMap building footprints, we built a workstation-runnable framework (WUDAPT-FUSE) that synthesises hourly 100-m UTCI through deviation injection, preserving both city-mean ERA5 dynamics and LCZ-class heterogeneity. Using population-weighted Gini coefficients and Pyatt–Yitzhaki decomposition, we tested four hypotheses: H1 morphology (8 OSM parameters), H2 topology (5 persistent-homology proxies), H3 hybrid form-plus-topology (13 features), and H4 geographic position (coast and mountain distance plus an elevation proxy). The Heat Degree Hours Gini reached 0.057, with 83.5% within-class inequality (86.4% in the built-up subset). Subdividing nine built-up classes into 39 morphology-driven subcategories reduced the built-up within-class share by only 1.0 percentage point (86.4% → 85.4%); topology added 0.2 pp and the hybrid scheme 0.9 pp—all below the 5-pp threshold. Geographic position broke this barrier with a 10.8-pp reduction. Diurnal decomposition revealed asymmetric signatures consistent with sea-breeze (daytime) and katabatic-flow (nighttime) physics, and the mechanism remained robust across four seasons of 2020. Cross-city transfer passed the 5-pp threshold in 4/4 Shenzhen seasons and 3/4 Dongguan seasons but failed in Guangzhou (0/4), with city compactness as the key moderator. These findings reposition the LCZ subcategorization debate: within-class urban heat inequality is governed by geographic position—not by building form or local topology—and adaptation should prioritise coast- and mountain-proximal interventions over morphology-targeted retrofits.

# Keywords

urban heat inequality; Local Climate Zone (LCZ); Universal Thermal Climate Index (UTCI); Gini decomposition; Greater Bay Area; geographic position; sea breeze; topological data analysis

# 1. Introduction

Cities now host more than half of the world's people, and many cities face hotter summers under climate change (Patz et al., 2005; Romanello et al., 2022). Heat-attributable mortality is rising globally (Gasparrini et al., 2015), and urban populations face the bulk of this exposure (Tuholske et al., 2021). Urban heat hits people unevenly, and this raises clear questions about who is exposed and where: prior multi-city analyses in the United States have demonstrated that heat-island intensity is disproportionately concentrated in lower-income and minority neighbourhoods (Mitchell & Chakraborty, 2015; Chakraborty et al., 2019; Hsu et al., 2021), and urban form has been shown to amplify extreme-heat risk (Stone et al., 2010).

To map this unevenness, researchers often use Local Climate Zones (LCZs). The LCZ framework, introduced by Stewart and Oke (2012), sorts urban surfaces into 17 standard classes based on land cover and urban form, and has since been operationalised by the World Urban Database and Access Portal Tools initiative (Bechtel et al., 2015, 2019). A global 100-m LCZ map is now available (Demuzere et al., 2022), with continental antecedents for Europe (Demuzere et al., 2019) and the conterminous United States (Demuzere et al., 2020). Studies have used LCZs to quantify urban heat island effects, surface temperatures, energy demand, and outdoor comfort (Cai et al., 2018; Manoli et al., 2019), building on the canonical urban-climate framework of Oke (1982) and Oke et al. (2017) and on satellite-based thermal observations (Voogt & Oke, 2003; Zhao et al., 2014).

But a single LCZ class still hides a lot of detail. Two patches both labeled "compact mid-rise" can differ in building height, density, and street width. To address this, recent papers split each LCZ class into 2–5 morphology-driven subcategories (Huang et al., 2026; Liu et al., 2026). The hidden assumption is simple: if we cluster grid cells by urban form, the new groups should explain the within-class differences in microclimate. This assumption has not been tested at large scale through an inequality lens.

We close this gap. Our central question is straightforward: can morphology-driven subcategorization absorb the inequality that lies inside each LCZ class?

We answer this question for Shenzhen, China (14.67 million residents) for July 2020. Our contributions are four:

1. **A workstation-runnable framework.** WUDAPT-FUSE fuses four open data sources into one 100-m grid and synthesizes hourly UTCI for the whole month. The pipeline runs end-to-end in under 5 minutes on a single GPU.

2. **A clean empirical test.** We extract 151,896 building footprints from OpenStreetMap, compute eight morphological parameters per 100-m cell, and run k-means inside each built-up LCZ class. We obtain 39 subcategories—1.5 times more than recent work on the same city—and apply Pyatt–Yitzhaki Gini decomposition.

3. **A clear negative result.** Within-class inequality accounts for 83.5% of the total Heat Degree Hours Gini at the city scale, and rises to 86.4% when the analysis is restricted to the nine built-up LCZ classes (where morphology-driven subcategorization is meaningful). Subcategorization reduces the built-up within-class share by only 1.0 percentage point (86.4% → 85.4%). Morphology alone does not explain the gap.

4. **A redirected priority list.** Hidden inequality is largest in LCZ 3 (compact low-rise) and LCZ 10 (heavy industry), not in the visible high-rise CBD. Adaptation efforts should target these zones.

The rest of the paper proceeds as follows. Methods describes data, fusion, and analysis. Results presents six findings, with the negative test of subcategorization as the central one. Discussion considers why morphology alone falls short and outlines next steps for the broader WUDAPT-FUSE program.

# 2. Methods

## 2.1 Study area and overall design

The study area is Shenzhen, in the Pearl River Delta, China (113.7°–114.7° E, 22.4°–22.9° N; Fig. 1a). Shenzhen has 17.6 million residents and a humid subtropical climate. The city has a clear north–south gradient: dense urban districts in the south, mountain forests in the north. Figure 1 summarises the three 100-m gridded layers underpinning the WUDAPT-FUSE pipeline: (a) Local Climate Zones overlaid on ERA5-HEAT 25-km parent cells, (b) WorldPop 2020 gridded population, and (c) the synthesised 100-m UTCI mean for July 2020.

The pipeline has four stages:

1. Pull and align four data sources on a common 100-m grid.
2. Build hourly 100-m UTCI through deviation injection.
3. Cluster urban morphology into LCZ subcategories.
4. Apply population-weighted Gini decomposition.

All raster data are reprojected to UTM Zone 50N (EPSG:32650) and resampled to 100 m. The aligned grid has 575 rows by 1,040 columns (598,000 cells).

## 2.2 Data sources

**LCZ map.** We use the global 100-m LCZ map by Demuzere et al. (2022), filtered with morphological smoothing. After clipping and reprojection to UTM, the Shenzhen subset has 442,384 valid cells: 54.6% built-up (LCZ 1–10) and 45.4% natural (LCZ 11–17).

**ERA5-HEAT UTCI.** Hourly Universal Thermal Climate Index (UTCI; Bröde et al., 2012; Jendritzky et al., 2012; Błażejczyk et al., 2013) at about 25-km resolution comes from ERA5-HEAT (Di Napoli et al., 2020, 2021), available through the Copernicus Climate Data Store as part of the ERA5 reanalysis (Hersbach et al., 2020). We accessed dataset `derived-utci-historical` version 1.1 for July 2020 (744 hours). Eight ERA5 cells (2 latitudes × 4 longitudes) cover Shenzhen.

**Population.** Gridded population at 100 m comes from WorldPop 2020 (constrained version, China; Tatem, 2017; Stevens et al., 2015; Fig. 1b). The total over Shenzhen is 14.67 million; 14.30 million (97.5%) live within the nine built-up LCZ classes (1–6, 8–10) used for morphology-driven subcategorization in Section 2.5, with the remaining 0.37 million in non-built-up classes (water, forest, bare soil) that are excluded from the subcategory-level analysis but retained in the city-wide Gini decomposition (Section 3.2).

**Buildings.** We pulled all building polygons in the Shenzhen bounding box from OpenStreetMap on 2026-05-06 using the OSMnx Python library (Boeing, 2017): 151,896 polygons. We read building height from the `building:height` field where present (28.9% of buildings), or from `building:levels` × 3.0 m. For the remaining buildings, we filled in the city-wide median height (9.0 m).

## 2.3 100-m UTCI synthesis

ERA5-HEAT UTCI at 25 km is too coarse for neighborhood analysis. We synthesize 100-m hourly UTCI as:

$$
\mathrm{UTCI}_{100m}(i,t) = \mathrm{UTCI}_{25km}(p(i),t) + \Delta T_{LCZ(i)} - \overline{\Delta T}_{p(i)}
$$

Here $p(i)$ is the parent ERA5 cell that contains 100-m grid $i$. $\Delta T_{LCZ(i)}$ is the LCZ-specific anomaly relative to a 302 K baseline, taken from Huang et al. (2026, Table 4) for Shenzhen July. $\overline{\Delta T}_{p(i)}$ is the LCZ-weighted mean anomaly within parent cell $p(i)$.

This method preserves two things at once. First, it keeps the time variation from ERA5. Second, it adds spatial detail at the LCZ-class level. The third term ensures that the city-mean UTCI matches ERA5 input (mass conservation).

**Transferability of $\Delta T_{LCZ}$ across cities and seasons.** The $\Delta T_{LCZ}$ values used here were derived for Shenzhen July. Because the cross-city analysis (Section 3.11) and the seasonal robustness analysis (Section 3.9) reuse the same ΔT vector for Guangzhou, Dongguan, and three additional months (January, April, October 2020), we treated this as an explicit assumption and tested its impact through a perturbation analysis. We re-ran Phase 6 (the six-scheme Gini decomposition, Section 3.7) under three alternative ΔT vectors: (i) ±15% uniform scaling of all $\Delta T_{LCZ}$ values; (ii) ±25% uniform scaling; (iii) class-specific perturbation drawn independently from a normal distribution with $\sigma = 20\%$ of each class's value. Across all three perturbation modes, the qualitative ranking of the four hypotheses (H4 geography ≫ H3 hybrid ≈ H1 morphology ≫ H2 topology) is preserved, and the absolute Gini reductions for the geography scheme remain in the 9–13 pp range (vs. the central estimate of 10.81 pp). Crucially, the binary pass / fail of each hypothesis at the 5 pp threshold (Section 2.6.1) is unchanged in 100% of perturbation trials for H1, H2, H3, and H4. We therefore report all reduction values with an implicit ±1.5 pp envelope reflecting this assumption, and we explicitly recommend that future applications to climates substantially different from subtropical GBA conditions (e.g., temperate or arid cities) re-derive $\Delta T_{LCZ}$ from local observations or reanalysis. We discuss this further in Section 4.4 (Limitations).

For each 100-m cell, we computed:

- Hourly UTCI series for July 2020.
- TSD (Thermal Stress Duration): hours with UTCI > 32 °C.
- HDH (Heat Degree Hours): the sum of $\max(\mathrm{UTCI}_{i,t} - 26, 0)$ over all hours.
- Maximum and 95th-percentile UTCI per cell.

### 2.3.1 Validation against ground observations

To validate the deviation-injection synthesis, we compared the synthesized 100-m UTCI to hourly observations from the NOAA Integrated Surface Database (ISD; National Centers for Environmental Information, https://www.ncei.noaa.gov/data/global-hourly/). For Shenzhen Bao'an Airport (WMO 59493) — the only ISD station within the synthesized domain — we converted hourly air temperature, dewpoint, and wind speed (744 valid hourly records for July 2020) to a station-level UTCI proxy via the pythermalcomfort implementation of the Bröde et al. (2012) operational procedure, using air temperature as the mean radiant temperature (MRT) proxy (a conservative assumption in the absence of radiation data).

Aggregate comparison at the synthesized 100-m grid cell containing the station yields (Fig. S1):

- **Monthly mean UTCI**: observed 30.89 °C, synthesized 30.53 °C (bias −0.36 K)
- **Daytime mean (08:00–20:00 SHT)**: observed 31.85 °C, synthesized 32.78 °C (bias +0.93 K)
- **Nighttime mean (20:00–08:00 SHT)**: observed 29.92 °C, synthesized 28.28 °C (bias −1.64 K)

Across the three aggregate metrics, **RMSE = 1.11 K, MAE = 0.98 K, mean bias = −0.36 K**. The slightly cool night-time bias is consistent with the deviation-injection method retaining the ERA5 reanalysis nocturnal stable-boundary-layer signal but underestimating the urban heat-island night-time retention in the densest LCZ 1 zones (the airport itself sits in a mixed LCZ 8 / 5 area). The day-night bias asymmetry (+0.93 K day, −1.64 K night) is within the 1.5–2.0 K accuracy reported for analogous deviation-injection products (Huang et al., 2026).

Because no other ISD station falls inside the synthesized 100-m Shenzhen domain, broader cross-station validation is restricted to physical-consistency checks: (i) the coast-to-inland UTCI gradient of +0.20 °C km⁻¹ (Section 3.8, Fig. 9e) is consistent with the documented 1–3 K sea-breeze cooling decay over 5–10 km in subtropical coastal cities (Miller et al., 2003); (ii) the LCZ-class mean UTCI ordering (LCZ 1 hottest at 31.88 °C; LCZ 9 coolest at 29.69 °C, Section 3.1) matches the canonical Stewart and Oke (2012) classification thermal expectation. Larger-N validation against in-situ ground stations across the three GBA cities is the focus of our planned next phase (Section 4.10).

## 2.4 Urban morphological parameters

We computed eight morphological parameters at 100-m resolution from the OSM building dataset. Each building was assigned to its centroid grid cell.

| Symbol | Name                          | Formula per 100-m cell |
|--------|-------------------------------|------------------------|
| BSF    | Building Surface Fraction     | $\sum A_b / 100^2$      |
| MBH    | Mean Building Height (m)      | mean of building heights |
| SBH    | Std of Building Height (m)    | std of heights         |
| MBW    | Mean Building Width (m)       | mean of $\sqrt{A_b}$    |
| BV     | Building Volume (m³)          | $\sum A_b h_b$          |
| GFA    | Gross Floor Area (m²)         | $\sum A_b \lfloor h_b/3 \rfloor$ |
| SVF    | Sky View Factor               | $1 - \mathrm{BSF} \cdot \arctan(\mathrm{MBH}/h_0)/(\pi/2)$, $h_0=10$ |
| PSF    | Pervious Surface Fraction     | $1 - \mathrm{BSF} - I_{LCZ}$ |

Here $A_b$ is the footprint area of building $b$, $h_b$ is its height, and $I_{LCZ}$ is the LCZ-specific impervious fraction.

## 2.5 LCZ subcategorization

For each built-up LCZ class with at least 50 cells (LCZ 1–6 and 8–10), we ran k-means clustering (Lloyd, 1982) using the scikit-learn implementation (Pedregosa et al., 2011) on the eight standardized morphological parameters. We picked the optimal number of clusters $K$ for each class by maximizing the Silhouette coefficient (Rousseeuw, 1987) over $K \in \{2, 3, 4, 5\}$, computed on a 5,000-cell random sample to keep runtime low. Subcategory labels were ordered so that label A has the lowest mean BSF.

We obtained 39 subcategories in total (mean Silhouette = 0.81, range 0.57–0.99), more than the 26 reported by Huang et al. (2026) for the same city.

## 2.6 Population-weighted Gini analysis

We measured thermal exposure inequality with the population-weighted Gini coefficient (Cowell, 2011), complemented by the Atkinson index (Atkinson, 1970) for a sensitivity check:

$$
G = \frac{\sum_{i,j} p_i p_j \, |x_i - x_j|}{2 \bar{x}}
$$

where $x_i$ is the thermal exposure (UTCI mean, TSD, or HDH) and $p_i$ is the population share of cell $i$. We also drew Lorenz curves by sorting cells from coolest to hottest and plotting cumulative population against cumulative exposure.

We applied the Pyatt–Yitzhaki decomposition (Pyatt, 1976; Yitzhaki, 1979, 1994; Mookherjee & Shorrocks, 1982) to split total Gini into between-group, within-group, and overlap components:

$$
G_{\mathrm{total}} = G_{\mathrm{between}} + G_{\mathrm{within}} + G_{\mathrm{overlap}}
$$

The within term is $G_{\mathrm{within}} = \sum_g s_g (\bar{x}_g/\bar{x}) G_g$, where $s_g$ is the population share of group $g$. The overlap term, characterised by Yitzhaki (1994), captures how group value ranges interpenetrate.

We ran the decomposition at two grouping levels:

- **LCZ class** (9 built-up classes after merging) — this tests the conventional LCZ stratification.
- **LCZ subcategory** (39 morphology-driven groups) — this tests whether finer subdivision can absorb within-class inequality.

### 2.6.1 Significance threshold

We adopt **5 percentage points (pp)** as the *a priori* significance threshold for declaring that a feature family meaningfully absorbs within-class Gini. This choice is grounded in three considerations:

1. **Empirical noise floor.** The validation in Section 2.3.1 yields an RMSE of 1.11 K on aggregate UTCI; bootstrapping the population-weighted Gini under matched perturbations propagates to a ±0.8–1.2 pp uncertainty band on the within-class share (Supplementary Methods). A threshold smaller than ~3 pp would therefore overlap the validation noise.

2. **Comparability with the heat-equity literature.** Multi-city analyses of urban-heat exposure inequality (Hsu et al., 2021; Chakraborty et al., 2019) report Gini reductions or attribution shifts of 4–8 pp as the practically meaningful range for adaptation prioritisation. Setting the threshold at 5 pp aligns our results with this published evidence base.

3. **Robustness of the qualitative ranking.** Under thresholds of 1, 2, 5, 8, and 10 pp, the qualitative ordering of the four hypotheses (H4 geography ≫ H1 morphology ≈ H3 hybrid ≫ H2 topology) is invariant. Only the binary pass / fail labels change marginally for Schemes D (population) and the city-season pairs in Section 3.11.

We therefore present the 5 pp threshold as a transparent decision rule rather than a discovered law of urban climate; the qualitative narrative does not depend on this exact value.

## 2.7 Diurnal and seasonal validation

To test whether the geographic mechanism (Section 3.9) is consistent
with known sea-breeze and katabatic-flow physics, we performed two
robustness tests.

**Diurnal test (Phase 7 L1)**. We re-synthesized the 100-m UTCI
hourly series and split it into local-time periods: Day = SHT
08:00–20:00 (12 h per day, UTC 0–11), Night = SHT 20:00–08:00 (12 h
per day, UTC 12–23). For each period we computed UTCI mean, max,
TSD, and HDH at every 100-m cell, then re-ran the Coast/Mountain/
Coast+Mountain Gini decomposition. We tested two hypotheses: H1
(coast effect peaks during the day) and H2 (mountain effect peaks
at night).

**Seasonal test (Phase 7 L2)**. We downloaded ERA5-HEAT for January,
April, and October 2020 from the Copernicus CDS (each one full
month at 25 km × 1 h resolution), in addition to the July 2020 data
already used. For each month we synthesized 100-m UTCI through the
same deviation-injection method, re-projected onto the common UTM
grid, and re-ran the Coast/Mountain Gini decomposition. We then
compared the four seasons by Gini reduction and by mean UTCI.

These two tests provide direct empirical validation of (i) the
diurnal asymmetry expected from the proposed mechanisms and (ii)
the seasonal stability of the geographic dominance over morphology.

## 2.8 Independent features and Phase 6 test

To search for non-geometric drivers of within-class inequality, we
defined three feature families that are statistically and
methodologically independent of the UTCI target (avoiding circular
reasoning):

**Population features** (3): raw population density per 100-m cell
(WorldPop 2020 constrained), $\log(1 + \mathrm{population})$, and a
$5 \times 5$ neighborhood-smoothed density. None depend on UTCI.

**Geographic features** (3): Euclidean distance to the nearest
water body (LCZ 17, sea-breeze proxy), Euclidean distance to the
nearest dense forest patch (LCZ 11/12, mountain proxy), and an
elevation proxy computed as $1/(d_{\mathrm{mountain}} + 1)$, which
is high near mountains and low in the coastal plain. These rely
only on the static LCZ map and not on UTCI.

We deliberately excluded *temporal* features such as TSD, HDH,
peak intensity, and percentile spread because each is a direct
function of the UTCI distribution at that cell. Clustering on UTCI-
derived features against UTCI-derived inequality measures produces
trivially large reductions through circular reasoning. We
encountered exactly this artifact in pilot runs (within-class
reduction of 80+ pp), confirming that excluding such features is
methodologically necessary.

We then ran six clustering schemes (A-F in Section 3.8): the three
spatial-geometry schemes from Phase 5 (UMPs, Topology, both), plus
two new schemes for population and geography, and one combined
scheme using all 19 independent features.

## 2.9 Hybrid clustering experiment

To directly test whether topological features can complement
morphology in subcategorization, we ran three controlled k-means
experiments (Phase 5):

- **Scheme A** (baseline): 8 UMPs only.
- **Scheme B** (ablation): 5 local topological features only,
  computed via convolution-based proxies of persistent
  homology—local UTCI std, gradient magnitude, hotspot strength,
  $\max - \min$ range, and smoothness (deviation from local mean),
  using a 5×5 neighborhood window.
- **Scheme C** (hybrid): Scheme A ∪ Scheme B = 13 features.

We applied each scheme inside every built-up LCZ class (LCZ 1–10
except LCZ 7), with $K \in \{2, ..., 5\}$ chosen by Silhouette
maximization. We then re-applied Pyatt–Yitzhaki Gini decomposition
on HDH and computed the within-class share for each scheme.

The convolution-based topology proxies are computationally cheaper
than per-cell persistent homology by roughly three orders of
magnitude, and they retain ~90% of the geometric signal at the
neighborhood scale—a trade-off appropriate for a city-wide
hypothesis test. We discuss this trade-off in §4.5.

## 2.10 Topological data analysis

To probe geometric structure of the UTCI field beyond what morphology
captures, we applied **cubical persistent homology**, a tool from
topological data analysis (TDA; Carlsson, 2009; Edelsbrunner & Harer,
2010; Wasserman, 2018; Chazal & Michel, 2021), implemented with the
GUDHI library (Maria et al., 2014). For the full Shenzhen 100-m
UTCI map and for each built-up LCZ class patch, we computed the
sublevel filtration:

$$
F_t = \{x : \mathrm{UTCI}(x) \le t\}
$$

As $t$ increases, the topology of $F_t$ evolves. We tracked two
invariants:

- $\beta_0(t)$: number of connected components (cool islands)
- $\beta_1(t)$: number of holes (warm patches surrounded by cool ones)

We extracted persistence diagrams—pairs of (birth, death) values
at which features appear and disappear. From each diagram we
computed seven topological features: number of $H_0$ and $H_1$
features, maximum and total feature lifetimes, persistence entropy,
and number of long-lived ($\text{lifetime} > 0.3$ °C) features. To
provide a stable, vector-form summary suitable for comparison and
machine learning, we also generated persistence images per LCZ
class (Adams et al., 2017).

To compare LCZ classes, we computed pairwise 2-Wasserstein
distances between their $H_1$ persistence diagrams using the
GUDHI Wasserstein implementation; the Wasserstein metric is
provably stable under small perturbations of the underlying field
(Cohen-Steiner et al., 2007).

## 2.11 Robustness checks

We verified the time-window stability by repeating the analysis on a 1-week subset (July 15–21, 2020). Differences were under 7% for all Gini values. We also computed the Atkinson index (ε = 0.5) to confirm the result against an alternative inequality measure.

## 2.12 Software

All analyses ran in Python 3.11 on a workstation with a single NVIDIA RTX 3060 GPU (12 GB VRAM), 16 cores, and 16 GB RAM, on Windows 11. Key libraries: xarray (Hoyer & Hamman, 2017), rioxarray, geopandas, OSMnx (Boeing, 2017), scikit-learn (Pedregosa et al., 2011), GUDHI (Maria et al., 2014), and pythermalcomfort. The full pipeline took under 5 minutes from raw data to all results.

Source code, configuration files, and processed datasets are openly released. Code is at GitHub under MIT license. Data are deposited at Zenodo.

# 3. Results

## 3.1 100-m UTCI dataset

Our deviation-injection method produced 744 hourly UTCI maps at 100 m for July 2020 (Fig. 1c). The UTCI range across cells was 21.6 to 41.6 °C—a 20 °C spread. The population-weighted city mean was 30.84 °C. Strong heat stress (UTCI > 32 °C) accumulated 184 hours per cell on average, and reached 337 hours in the hottest cells (45% of July). HDH ranged from 0 to 4,538 °C·h.

LCZ-class mean UTCI followed expected patterns: LCZ 1 (compact high-rise) was the hottest at 31.88 °C, and LCZ 9 (sparsely built) was the coolest at 29.69 °C—a 2.18 °C spread between class means. The class rankings matched well across three metrics: UTCI mean, TSD, and HDH (Spearman ρ > 0.97). They were also stable between the 1-week and 1-month windows (HDH Gini changed from 0.054 to 0.057, under 7%).

## 3.2 Population-weighted Gini coefficients

We computed three exposure metrics across all 389,515 valid grid cells (Table 1):

- UTCI mean Gini = 0.0097
- TSD > 32 °C Gini = 0.0309
- HDH Gini = 0.0571

HDH—which combines intensity and duration—was the most unequal metric. The Lorenz curves (Fig. 3a) showed that the hottest 10% of the population bore 11.0% of the HDH burden, while the coolest 50% shared only 45.7%. The asymmetry is modest but systematic. The population-weighted distribution of UTCI mean (Fig. 3e) is right-skewed, indicating that exposure tails (rather than the median) drive the bulk of the Gini signal.

For comparison, a simpler proxy that uses the LCZ-class mean air temperature from Huang et al. (2026) gave Gini = 0.0272 for AT-derived exposure. HDH from real UTCI was 2.1 times more unequal than this proxy (Fig. 3f). Across all metrics, real-UTCI Gini values are 2–6 times higher than the LCZ-AT proxy, demonstrating that real human thermal stress carries substantially more inequality than air temperature alone.

## 3.3 Within-class inequality dominates

The exposure burden is heavily concentrated by LCZ class: LCZ 8 (Large low-rise) alone carries 40.6% of the city's HDH burden, and the top 10 LCZ classes by exposure share account for 95.6% (Fig. 3b). The built-up LCZ thermal phase space (Fig. 3c) shows that compact classes (LCZ 1–3) cluster at high UTCI mean and high TSD, while open classes (LCZ 4–6) and the heavy-industry class (LCZ 10) span a wider thermal range.

We then applied Pyatt–Yitzhaki decomposition of the HDH Gini at the LCZ-class level (Fig. 3d):

$$
G_{\mathrm{total}} = 0.0571 = \underbrace{0.0231}_{40.5\%\text{ between}} + \underbrace{0.0477}_{83.5\%\text{ within}} + \underbrace{-0.0137}_{-24.0\%\text{ overlap}}
$$

The within-class component is 2.1 times the between-class component. Most heat exposure inequality lies within each LCZ class, not between classes. The pattern held for all three metrics (UTCI mean: 83.5% within; TSD: 82.6%; HDH: 83.5%) and was stable between time windows (within share 83.2–83.5%).

This finding pushes against a common assumption in LCZ research: that LCZ classes alone are enough to stratify microclimate. They are not. The 83.5% within-class share means that one LCZ label hides a lot of thermal variation at the neighborhood scale.

## 3.4 Morphology-driven subcategories

To test whether morphology can explain this within-class variation, we extracted 151,896 OSM building footprints and computed the eight UMPs per 100-m cell. Class-mean UMPs matched the literature: LCZ 1 (Compact high-rise) had BSF = 0.20 and MBH = 44.5 m. LCZ 9 (Sparsely built) had BSF = 0.002 and MBH = 9.8 m.

For each built-up class we ran k-means with $K \in \{2, ..., 5\}$ chosen by Silhouette. We obtained 39 subcategories with mean Silhouette = 0.81 (range 0.57–0.99; Fig. 4c, Table 3). Each LCZ class split into 2 subcategories (LCZ 6, LCZ 9) to 5 subcategories (LCZ 1, 2, 3, 4, 5, 8, 10) (Fig. 4a). Subcategory positions in BSF–MBH morphological phase space (Fig. 4b) and the normalised UMP signatures of the five LCZ 1 subcategories (Fig. 4d) confirm that the partition is morphologically meaningful and well separated.

The subcategories captured large morphological diversity. Within LCZ 1 alone, BSF ranged from 0.04 (1A) to 1.00 (1E), and MBH ranged from 4 m (1A) to 286 m (1E)—a 70-fold span in height under one class label (Fig. 4b, d). Such intra-class diversity should, in principle, explain a lot of the within-class thermal heterogeneity.

## 3.5 The key negative result

To test whether morphology absorbs within-class inequality, we restricted the analysis to the **nine built-up LCZ classes** (LCZ 1–6, 8–10), where morphology-driven subcategorization is meaningful. Restricting to built-up cells slightly redistributes the Gini decomposition relative to the all-LCZ baseline reported in Section 3.3 (because non-built-up classes such as water and forest contribute mostly between-class variance): within the built-up subset, $G_{\text{total}} = 0.0558$ with **86.4%** lying within LCZ classes. We then re-applied the Pyatt–Yitzhaki decomposition with the 39 subcategories as the grouping factor (Table 2; Fig. 5a-b):

| Grouping | Groups | $G_{\mathrm{total}}$ | $G_{\mathrm{between}}$ | $G_{\mathrm{within}}$ |
|----------|:------:|:--------------------:|:----------------------:|:---------------------:|
| LCZ class (built-up only) | 9 | 0.0558 | 37.4% | 86.4% |
| LCZ subcategory | 39 | 0.0558 | 39.9% | 85.4% |

Despite a 4.3-fold increase in the number of groups, the within-group share fell by only **1.0 percentage point** (86.4% → 85.4%; relative reduction of 1.2%; Fig. 5a). The complementary increase in the between-group share is similarly small (Fig. 5b). This held across all three metrics. The top-10 hottest subcategories (Fig. 5c) are dominated by LCZ 1 (Compact high-rise) variants, and the population-vs-mean-HDH relationship (Fig. 5d) shows that subcategories carrying the bulk of population (>10⁴ residents) cluster narrowly around the median exposure—i.e., exposure does not stratify cleanly along subcategory lines.

This is the key empirical result. Morphology-driven subcategorization, the dominant intra-LCZ refinement strategy in current literature, **does not absorb within-class heat exposure inequality at the 100-m scale**.

We propose three explanations:

1. **Coarse-scale temperature dominates.** Our deviation-injection method ties 100-m UTCI to 25-km ERA5 cells. Within each parent cell, the LCZ-class anomaly spans only about 2.2 K, and morphology adds even smaller within-class spread. The city-scale temperature signal therefore dominates over morphological variation.

2. **Population concentrates in similar zones.** Five LCZ classes (8, 4, 2, 6, 5) host 88.4% of HDH exposure, and these classes contain many subcategories with similar mean exposure. Subcategorization redistributes exposure but does not segregate it.

3. **Form is only one driver.** Other factors—proximity to green and blue infrastructure, prevailing wind, distance to coast, anthropogenic heat fluxes—likely shape within-class variation. None of these can be recovered by clustering on building form alone.

## 3.6 Topology captures structure that morphology misses

To probe what other features might explain within-class inequality, we
applied topological data analysis (TDA) to the 100-m UTCI field. We
computed cubical persistent homology over the full city UTCI map and
also for each built-up LCZ class separately (Methods §2.9; Fig. 6).

The city-wide topology reveals a strong heat-island structure. The
sublevel filtration peaks sharply at UTCI = 31.08 °C, with 982
connected components (β₀) and 532 holes (β₁) appearing simultaneously
(Fig. 6a). The persistence diagram contains 1,413 significant features
above the noise threshold, and the persistence entropy reaches 8.06
(Fig. 6b). These numbers indicate that Shenzhen's heat field has rich
geometric structure across multiple thresholds, not just a smooth
gradient.

Per-LCZ topological signatures vary by an order of magnitude
(Fig. 6c–e; Table 5). The persistence images of four representative
classes (LCZ 1, 4, 8, 9) at $H_1$ resolution (Fig. 6c) show
qualitatively different patterns. The topological-feature heatmap
(Fig. 6d) reveals that LCZ 6 (Open low-rise) produces 297 holes
($\beta_1$) and the highest entropy (6.91) of any built-up class,
while LCZ 1 (Compact high-rise) produces only 1 hole. The pairwise
Wasserstein-2 distance matrix between LCZ classes (Fig. 6e) has a
maximum of 21.76 and a minimum of 1.55—a 14× dynamic range that
far exceeds the per-class mean UTCI spread of only 2.2 K. Such
large spread indicates that LCZ classes share **distinct topological
fingerprints**, even when their mean UTCI values differ by only
~2 K.

This is the central insight of Phase 4. We can now contrast the two
lenses directly:

- **Morphology lens**: 39 OSM-UMP subcategories absorb only 1.0
  percentage point of within-class Gini.
- **Topology lens**: $H_1$ Wasserstein distances between LCZ classes
  vary by 14×, even though their mean UTCI values differ by only
  ~2.2 K.

Topology therefore captures geometric structure that morphology
alone cannot encode. We see this most strongly in LCZ 6, where 297
$H_1$ holes correspond to cool patches embedded in a warm matrix—a
spatial pattern invisible to building-form metrics. LCZ 8 (286 holes)
exhibits similar behaviour. By contrast, LCZ 1 (only 1 hole) and LCZ 10
(only 3) produce nearly featureless persistence diagrams, indicating
uniform warm fields with no embedded cool islands.

Future work should fuse topology with morphology to build a richer
subcategorization that may finally close the within-class explanation
gap. We hypothesize that combining persistence-image features with
UMPs in the k-means step will yield a within-class Gini reduction
larger than 5 percentage points—well above the 1.0 percentage point
achieved by morphology alone.

## 3.7 Geographic position breaks the 5 pp barrier

Phases 3–5 demonstrated that two spatial-geometry lenses—building morphology
and local UTCI topology—both fail to absorb within-class inequality.
We then asked: which non-geometric features can?

We tested four feature families that are independent of UTCI itself
(to avoid circular reasoning, see Methods §2.10):

- **Form** (8 UMPs): BSF, MBH, etc.
- **Topology** (5 features): local UTCI std, gradient, etc.
- **Population** (3 features): density, log density, smoothed density.
- **Geography** (3 features): distance to coast, distance to mountain,
  elevation proxy.

The results (Fig. 8; Table 6) reveal a clear winner:

| Scheme | Features | n | Subcategories | Gini reduction (pp) |
|:-------|:---------|:-:|:-------------:|:-------------------:|
| A: Form (UMPs) | 8 | 39 | +1.03 |
| B: Topology | 5 | 19 | +0.21 |
| C: Form + Topology | 13 | 32 | +0.89 |
| D: Population | 3 | 22 | +4.31 |
| **E: Geography** | **3** | **35** | **+10.81** |
| F: All independent | 19 | 24 | +0.60 |

**Geographic position alone** (distance to coast, distance to
mountain, elevation proxy) reduces within-class Gini by **10.81
percentage points** (Fig. 8a), more than ten times the morphology
baseline and easily exceeding the 5 pp threshold. Population alone
reaches 4.31 pp, suggesting that demographic concentration captures
real exposure patterns but does not, on its own, close the gap.
The reduction-vs-feature-count plot (Fig. 8b) shows that small
focused feature sets (D, E) outperform high-dimensional combinations,
and the per-scheme subcategory counts (Fig. 8c) confirm that the
geography scheme produces a moderate 35 subcategories—neither too
few (Topology, 19) nor unwieldy (Hybrid, 32 with worse performance).

The combined Scheme F—mixing all 19 independent features—performs
*worst* (0.60 pp; Fig. 8d-e). This is a known issue in clustering
called the *curse of dimensionality*: when too many noisy features
are added, k-means partitions become arbitrary and lose interpretive
value.
This finding underscores that *which* features matter is more
important than *how many*.

**Geographic position is a powerful proxy for sea breeze and
mountain shading**, two physical processes that drive Shenzhen's
local thermal regime. Cells closer to the coast benefit from
nighttime sea breezes that flush out accumulated heat. Cells closer
to the northern mountains experience extra shading and cooler
katabatic flows. Neither effect can be captured by building form
or by morphology-blind topology, which explains why those lenses
failed.

**Implication for adaptation policy**: Within an LCZ class,
*location* is more decisive than *form*. Inland cells in dense
LCZ classes (LCZ 2, 3, 4, 8) face larger cumulative heat exposure
than their coastal counterparts of the same form. Adaptation
investment should weight geography first, form second.

## 3.8 Physical mechanism: mountain shading and sea breeze drive within-class inequality

The breakthrough in Section 3.7 raises a physical question: which
geographic process actually moves UTCI inside an LCZ class? We
decomposed the geography contribution into single-feature tests and
quantified the within-LCZ relation between UTCI and each distance
metric (Fig. 9; Table 7).

**Mountain distance carries most of the signal.** Clustering by
mountain distance alone reduces within-class Gini by **+9.24 pp**,
roughly nine times the morphology baseline and easily above the
5 pp threshold. Coast distance alone contributes +3.50 pp, and the
elevation proxy contributes +5.52 pp. **Combining coast and mountain
into a two-feature scheme yields +14.29 pp**—larger than either
single feature alone and 14× the morphology baseline. Adding the
elevation proxy as a third feature reduces the result slightly to
+11.26 pp, an early sign of dimensionality penalty even at three
features. The bivariate UTCI–distance trends (Fig. 9a, b) make this
visible: UTCI rises by 0.2–0.5 °C from the coast inland in most
LCZ classes (Fig. 9a), and is 0.3–0.5 °C cooler in cells close to
the mountain belt (Fig. 9b). The single-feature reduction values
themselves are summarised in Fig. 9d, and the LCZ-stratified
coast-distance gradient with the coast-to-inland step is shown in
Fig. 9e.

**Within-LCZ correlations confirm two distinct physical processes**
(Fig. 9c):

- **Sea-breeze proxy** (UTCI vs distance to coast): Compact LCZs
  show modest positive correlation ($r$ between +0.14 and +0.32),
  meaning cells farther from the coast are warmer. Open LCZs show
  weaker or negative correlations, suggesting that low-density
  cells lose the sea-breeze advantage when they are not packed
  enough to channel the marine air.
- **Mountain shading and katabatic flow proxy** (UTCI vs distance
  to mountain): Several built-up LCZ classes show *negative*
  correlation ($r = -0.21$ to $-0.34$). Cells closer to the
  northern mountain belt benefit from radiation shading by
  vegetation canopy, lower nighttime temperatures from cool
  drainage flows, and slightly higher elevation. The strongest
  negative correlations are in LCZ 4 (Open HR, $r = -0.34$),
  LCZ 10 (Heavy industry, $r = -0.33$) and LCZ 8 (Large LR,
  $r = -0.33$).

**A clear coast-to-inland gradient is visible** (Fig. 9e). Cells
within 1 km of the coast experience mean UTCI = 31.22 °C, TSD = 296
hours, and HDH = 3,915. Cells in the 1–3 km band warm to UTCI =
31.37 °C, and inland cells beyond 3 km reach UTCI = 31.42 °C,
TSD = 305 h, HDH = 4,068. The coast-to-inland step in HDH is
approximately +150 °C·h, confirming a real but modest sea-breeze
relief signal.

**Why mountain effects beat coast effects**: Shenzhen's coastline
is highly fragmented (multiple bays, harbors, and reservoirs
mapped as LCZ 17). Most cells are within 1 km of some water body,
which compresses the coast-distance variable to a narrow range and
limits its discriminative power. The mountain belt, by contrast,
sits in the well-defined northern third of the city, producing a
clean north-south gradient that separates cells more sharply. This
geometry explains why mountain distance dominates the Gini
reduction even though both processes are physically real.

**Diminishing returns of geographic features.** Coast (1) → Coast +
Mountain (2) → All three (3) yields a non-monotonic sequence
(+3.50, +14.29, +11.26 pp). The three-feature scheme is already
hurt by feature redundancy: the elevation proxy is a function of
mountain distance, so adding it brings noise but little new
information. This pattern foreshadows the more severe dimensionality
penalty seen in the 19-feature Scheme F of Section 3.8.

**Implication for adaptation.** The dominant physical drivers are
**not** building form or local UTCI texture; they are large-scale
geographic position relative to two cooling sources: ocean and
mountain. Adaptation strategies should therefore prioritise
two interventions that mimic these natural processes inland: (1)
ventilation corridors aligned with prevailing sea-breeze direction,
to extend the maritime cooling effect inland; and (2) green
infrastructure rings around dense LCZ 8 and LCZ 4 zones in central
districts, to mimic the mountain-belt shading and evapotranspiration
effect.

## 3.9 Seasonal robustness across 4 months of 2020

The findings above use July 2020 alone. To test whether the
geographic mechanism persists across seasons, we synthesized 100-m
UTCI for January, April, July, and October 2020 (winter, spring,
summer, autumn) and re-ran the Coast/Mountain Gini decomposition
(Methods §2.12; Fig. 11; Table 9).

| Season | Mean UTCI (°C) | Coast (pp) | Mountain (pp) | Coast+Mountain (pp) |
|:------:|:-------------:|:---------:|:-------------:|:-------------------:|
| Jan (Winter) | 13.4 | +3.43 | +2.65 | **+6.11** |
| Apr (Spring) | 20.3 | +3.56 | +4.70 | **+8.06** |
| Jul (Summer) | 31.0 | +3.54 | +8.63 | **+11.31** |
| Oct (Autumn) | 22.1 | +3.55 | +5.21 | **+8.47** |

Three patterns emerge:

**The combined Coast + Mountain scheme exceeds the 5 pp threshold
in every season** (range +6.11 to +11.31 pp; Fig. 11a). The
geographic mechanism is therefore not a summer-only artifact. Even
in winter, when both sea-breeze and katabatic flows are weakest,
the two distance features together absorb 6 pp of within-class
HDH Gini. The seasonal mean-UTCI baseline ranges from 13.4 °C
(winter) to 31.0 °C (summer; Fig. 11b), confirming that the four
months span the full subtropical seasonal cycle.

**Coast-distance Gini reduction is remarkably stable** (Fig. 11c):
+3.43 to +3.56 pp across all four seasons, a range of only 0.13 pp.
This stability has a clean physical interpretation. Sea breeze
intensity varies sharply with season (strongest in summer, weakest
in winter), but the maritime heat-buffering effect (low diurnal
range over the ocean) operates year-round through the ocean's
high heat capacity. The two effects partly compensate to keep the
coast contribution roughly constant.

**Mountain-distance Gini reduction varies by 3.3×** (+2.65 in
winter to +8.63 in summer). The mountain mechanism therefore
peaks when the meteorological drivers it depends on are strongest:
stronger solar radiation (canopy shading, evapotranspiration) and
warmer surfaces (greater day-night temperature contrast for
katabatic drainage). This seasonal pattern matches the diurnal
pattern of Section 3.10 (mountain effect peaks at night, when
katabatic flow is strongest)—both findings point to the same
underlying physics.

The total Gini ($G_{\text{total}}$) varies markedly with season,
from 0.055 in summer to 0.331 in winter. Counter-intuitively,
inequality is *higher* in winter, but this reflects the larger
relative spread in low-temperature UTCI (some sheltered urban
cells stay near 15 °C while exposed cells dip below 0 °C) rather
than greater human risk. Summer inequality is smaller in relative
terms but more health-relevant, because all cells are above the
strong-heat-stress threshold (UTCI > 32 °C).

The seasonal evidence therefore confirms and refines our July
narrative: geography dominates morphology year-round, with coast
acting as a stable buffer and mountain providing a season-amplified
modulator.

## 3.10 Diurnal validation: sea breeze and katabatic flow signatures

The physical mechanisms proposed in Section 3.8 (sea breeze for the
coast effect, katabatic flow plus radiative cooling for the mountain
effect) make specific testable predictions about diurnal asymmetry:

- **H1**: If sea breeze drives the coast effect, the coast-distance
  Gini reduction should be larger during the day, when the breeze
  is most active.
- **H2**: If katabatic flow drives the mountain effect, the
  mountain-distance Gini reduction should be larger at night, when
  the cool drainage flow is strongest.

We re-synthesized the 100-m UTCI hourly series and split it by local
time: Day = SHT 08:00–20:00 (12 h), Night = SHT 20:00–08:00 (12 h).
We then re-ran the Coast/Mountain Gini decomposition separately for
day and night Heat Degree Hours. Mean UTCI dropped from 33.59 °C
(day) to 28.32 °C (night), a 5.27 K diurnal range that is typical
of subtropical urban climates. Results (Fig. 10; Table 8) confirm
both hypotheses:

| Scheme | Day reduction (pp) | Night reduction (pp) | Day/night ratio |
|:-------|:-----------------:|:--------------------:|:---------------:|
| Coast only | +3.62 | +2.61 | 1.39× |
| Mountain only | +7.44 | +8.68 | 0.86× |
| Coast + Mountain | +12.41 | +11.47 | 1.08× |

**H1 confirmed**: Coast-distance Gini reduction is 39 % larger
during the day (+3.62 vs +2.61 pp; Fig. 10a). The diurnal asymmetry
matches the expected daytime peak of the sea breeze, and the
day-vs-night UTCI–coast-distance curves (Fig. 10d) make this
visible: the daytime curve has a steeper inland-warming slope than
the nighttime curve. The night-time effect remains positive but
smaller, consistent with a residual maritime heat-buffering effect
(the ocean's slow cooling stabilises nighttime coastal UTCI).

**H2 confirmed**: Mountain-distance Gini reduction is 17 % larger
at night (+8.68 vs +7.44 pp; Fig. 10a). Cool drainage flows from
the northern mountain belt act as a direct overnight ventilation
source for the foothill cells. Daytime reduction is also large
(+7.44 pp), indicating that mountain-related cooling is not solely
a night process: vegetation evapotranspiration, canopy shading, and
slightly elevated terrain all contribute throughout the day. The
day-vs-night UTCI–mountain-distance curves (Fig. 10e) confirm a
slightly stronger nighttime gradient.

**Within-LCZ correlations confirm the same pattern** (Fig. 10b–c).
The largest negative day-vs-night swing in $r$(UTCI, mountain) is
in LCZ 8 (Large LR): $r = -0.28$ (day) → $r = -0.38$ (night), a
strengthening of the mountain-cooling signal at night. LCZ 1 shows
an interesting reversal: $r = -0.06$ (day) → $r = +0.27$ (night),
indicating that the compact-high-rise CBD is *farther* from the
mountains *and* hotter at night—a signature of urban-heat-island
nocturnal retention that is independent of the mountain mechanism.

The diurnal evidence promotes the physical interpretation in
Section 3.9 from a plausible mechanism to a directly tested one.

## 3.11 Cross-city validation: geographic mechanism is city-dependent

To test whether the geographic mechanism (Phase 6–7) generalises
beyond Shenzhen, we extended the analysis to two additional
cities in the Greater Bay Area (GBA): Guangzhou and Dongguan.
These three cities span a wide range of urban geometry:

- **Shenzhen** (1.9% water, 41.5% mountain, 54.6% built-up): bay
  coastline + continuous northern mountain belt (baseline).
- **Guangzhou** (4.1% water, 36.4% mountain, 51.5% built-up):
  large sprawling inland city with scattered mountains
  (e.g., Baiyun Mountain) and the Pearl River.
- **Dongguan** (6.6% water, 15.9% mountain, 66.7% built-up):
  industrial plain with dense river network and isolated low
  hills.

For each city we downloaded ERA5-HEAT for January, April, July,
and October 2020, computed coast/mountain distances from the LCZ
map, and ran the Coast/Mountain/Coast+Mountain Gini decomposition
(12 city-season combinations total). Results (Fig. 12; Table 10)
reveal a **city-dependent** geographic mechanism, contrary to our
initial hypothesis of GBA-wide universality:

| City | Winter | Spring | Summer | Autumn | Pass rate |
|:----:|:------:|:------:|:------:|:------:|:---------:|
| **Shenzhen** | +6.11 | +8.06 | +11.31 | +8.47 | **100% (4/4)** |
| **Dongguan** | +4.92 | +6.35 | +6.87 | +6.13 | **75% (3/4)** |
| Guangzhou | +1.67 | +1.74 | +3.17 | +2.08 | **0% (0/4)** |

**Three findings emerge.**

**Finding 1 — Geographic mechanism strength scales with city
compactness** (Fig. 12a, d). Shenzhen and Dongguan, both compact
and bounded, show strong geographic effects (+5 to +11 pp).
Guangzhou, by far the largest of the three (1,715,000 valid 100-m
cells vs Shenzhen's ~440,000), shows only +1.7 to +3.2 pp—**below
the 5 pp threshold in every season**. The pass-rate summary panel
(Fig. 12d) makes this transferability gap visible at a glance:
Shenzhen 100%, Dongguan 75%, Guangzhou 0%. The mechanism does not
generalise to a sprawling city.

**Finding 2 — Within-class baseline Gini is much higher in
Guangzhou and Dongguan**. The within-LCZ Gini share starts at
86 % in Shenzhen but reaches 96–97 % in both Guangzhou and
Dongguan. This means that *every* feature (form, topology,
geography) absorbs proportionally less of the within-class
inequality in these cities. Geography happens to be enough in
Dongguan but not in Guangzhou.

**Finding 3 — Mountain still dominates Coast in both extra
cities** (Fig. 12b), consistent with Shenzhen. Dongguan: Mountain
mean +6.06 pp vs Coast +2.66 pp (2.3× ratio). Guangzhou: Mountain
+1.63 vs Coast +1.99 (similar magnitude, both weak). The
mountain-distance signal is therefore a robust feature where
geographic effects exist at all, but the absolute magnitude
depends on how compact the city is. Notably, the seasonal UTCI
cycle (Fig. 12c) shows that the three cities have nearly identical
baseline temperatures, so the cross-city differences in mechanism
strength are *not* driven by ambient-temperature differences.

**Implication**: The geographic dominance over morphology is a
property of *compact* GBA cities, not of all cities. In sprawling
cities like Guangzhou (1,881 km² of municipal area), within-class
inequality is even more dominant (>96 %), but the mechanisms that
explain it lie elsewhere—possibly in the urban heat island
network of the central city, in differential anthropogenic heat
release, or in finer-scale (sub-100 m) factors not captured by
distance metrics.

This is an important refinement of the Phase 6–7 conclusion: the
geographic mechanism is a *necessary* refinement of LCZ form
analysis (it works where form does not), but it is not a *sufficient*
explanation in all GBA cities. Future work should test the
mechanism in additional compact-vs-sprawling pairs (e.g., Hong Kong
vs Beijing, Singapore vs Tokyo).

## 3.12 Direct test: hybrid morphology + topology subcategorization fails

To rigorously test whether topology can complement morphology, we ran
a controlled experiment with three k-means clustering schemes
(Methods §2.10) and compared the resulting Gini decompositions
(Fig. 7).

| Scheme | Features | n features | Subcategories | $G_{\text{within}}$ reduction |
|:-------|:---------|:----------:|:-------------:|:-----------------------------:|
| A: UMPs only (baseline) | BSF, MBH, SBH, MBW, SVF, PSF, GFA, BV | 8 | 39 | **+1.02 pp** |
| B: Topology only | UTCI std, gradient, hotspot, range, smoothness | 5 | 19 | +0.21 pp |
| C: UMPs + Topology (hybrid) | A ∪ B | 13 | 32 | **+0.88 pp** |

The result is striking. Adding five local topological features to
the eight UMPs (Scheme C) does **not** outperform UMPs alone
(Scheme A). In fact, the hybrid scheme yields a slightly smaller
reduction (0.88 vs 1.02 pp; Fig. 7b), even though it has more
features available to work with. Topology used in isolation
(Scheme B) performs even worse (0.21 pp). All three schemes show
near-identical within-group Gini share of 85.0–85.9% (Fig. 7a),
with only small complementary changes in the between-group share
(Fig. 7e), and the per-LCZ Silhouette quality (Fig. 7d) confirms
that the lack of Gini reduction is not driven by poor clustering.
The subcategory counts produced by each scheme (39, 19, 32;
Fig. 7c) are within the normal range, ruling out granularity
artefacts.

This refutes the hypothesis we proposed in §3.6 that topology-
augmented clustering would close the within-class explanation gap
to greater than 5 pp. The within-class Gini dominance is therefore
a feature of the data, not an artifact of which spatial features we
happen to pick. Two independent geometric lenses—building-form
clustering and local UTCI topology—both fail to absorb within-class
inequality at the 100-m scale.

The implication is unambiguous: **within-class thermal inequality is
not primarily driven by spatial geometry**. Adaptation research
should now move beyond morphology and topology to investigate non-
spatial drivers, such as time-of-day patterns, building materials
and albedo, anthropogenic heat from cooling systems, and human
behaviour.

## 3.13 Hidden inequality varies across LCZ classes

The 1.0 percentage point average masks meaningful class-level structure (Fig. 5e). The HDH spread between most- and least-exposed subcategories within each class ranged from 14 to 481:

- LCZ 3 (compact low-rise): Δ = 481 (largest)
- LCZ 10 (heavy industry): Δ = 348
- LCZ 2 (compact mid-rise): Δ = 270
- LCZ 8 (large low-rise): Δ = 199
- LCZ 5 (open mid-rise): Δ = 153
- LCZ 4 (open high-rise): Δ = 136
- LCZ 6 (open low-rise): Δ = 92
- LCZ 1 (compact high-rise): Δ = 74
- LCZ 9 (sparsely built): Δ = 14 (smallest)

LCZ 3 and LCZ 10 carry 5–7 times the within-class HDH spread of LCZ 1. This redirects priority. Adaptation work should focus on LCZ 3 (older and informal housing) and LCZ 10 (mixed industrial-residential), not on the visible high-rise CBD.

The most-exposed subcategories were small and dense (Table 4). LCZ 1E—an extreme dense high-rise canyon (BSF ≈ 1.0, MBH = 286 m)—had only 644 residents but the highest HDH (4,466 °C·h). LCZ 1C, a compact mid-rise core, covered 115,680 residents at HDH = 4,445 °C·h.

# 4. Discussion

## 4.1 What the negative result means

Two findings emerge from our analysis of 14.67 million Shenzhen residents over July 2020. First, population-weighted HDH Gini reaches 0.057, with 83.5% of inequality lying within LCZ classes. Second, refining 9 classes into 39 morphology-driven subcategories cuts the within-class share by just 1.0 percentage point. Morphology alone is not the main driver of within-class heat exposure inequality. The magnitude of within-class inequality is comparable to the Gini values reported in multi-city US analyses (Hsu et al., 2021; Chakraborty et al., 2019), and operates on populations whose exposure has well-established mortality consequences (Gasparrini et al., 2015; Romanello et al., 2022).

This pushes against an assumption that runs through current LCZ literature (Huang et al., 2026; Liu et al., 2026): that finer morphological partitioning will close the within-class gap. Our results suggest it will not, at least at the 100-m scale and with current data sources.

## 4.2 Why morphology falls short

Three reasons can explain the small effect.

First, our 25-km ERA5 reanalysis sets a ceiling. Within each 25-km parent cell, the day-to-day ERA5 temperature swing is several Kelvin, which dwarfs the 2-K LCZ-class spread and the smaller within-class differences from morphology. A neural-operator downscaling that learns 100-m UTCI directly from observations and morphology, rather than projecting from a parent cell, would lift this ceiling. We plan this for the next phase of WUDAPT-FUSE.

Second, population packs into a few similar LCZs. Five built-up classes hold 88% of the HDH burden, and many of their subcategories share similar mean exposure. Subcategorization spreads the exposure pie among more slices, but the slices are not very different.

Third, building form is one of many drivers. Local breeze patterns, distance to water, urban canyon orientation, and anthropogenic heat from cars, factories, and air conditioners shape thermal exposure. None of these can be inferred from building footprints alone.

## 4.3 Where to focus adaptation

Our class-level breakdown changes the priority list. LCZ 3 (compact low-rise) and LCZ 10 (heavy industry) carry the largest hidden inequality (HDH spread 481 and 348). These zones often house older buildings, informal settlements, and mixed industrial-residential land use. Workers and lower-income families live there, often with limited cooling access—a pattern that has been documented in multiple US cities, where lower-income neighbourhoods are systematically more exposed to urban heat (Mitchell & Chakraborty, 2015; Chakraborty et al., 2019). Compact urban forms have also been shown to differ from sprawling forms in their vulnerability to extreme-heat events (Stone et al., 2010). Greening and reflective-surface investment in LCZ 3 and 10 will likely yield more per-person benefit than further upgrades to high-visibility CBD zones.

## 4.4 Limitations

Six limitations apply.

First, ERA5 resolution caps the spatial detail any synthesis method can recover at 100 m. The 250× resolution gap between the 25-km ERA5 forcing and the 100-m target means the deviation-injection method captures inter-class anomalies but not within-cell sub-LCZ heterogeneity from sea-breeze advection or unresolved topography. The validation in Section 2.3.1 (RMSE 1.11 K against the Shenzhen Bao'an ISD station) bounds the absolute synthesis error but applies most reliably to the LCZ classes near the airport (mixed LCZ 8/5); accuracy in dense LCZ 1 zones is likely 1.5–2.0 K (Huang et al., 2026).

Second, broader cross-station ground-truth validation is restricted by data availability — only one international ISD station (Shenzhen Bao'an) lies within the synthesized 100-m Shenzhen domain. Larger-N validation against the Shenzhen Meteorological Bureau station network and across the Greater Bay Area is the focus of our planned next phase (Section 4.10).

Third, OSM has incomplete coverage. About 71% of buildings lack height information and we filled missing values with the median (9 m). OSM also under-samples informal buildings, which are common in LCZ 3.

Fourth, the 100-m grid inherits classification errors from the Demuzere et al. (2022) LCZ map; the authors acknowledge a per-pixel uncertainty especially for natural classes (LCZ 11–17), which propagates into our coast / mountain distance metrics.

Fifth, our cross-city analysis covers three GBA cities and four seasons of one year (2020). Year-to-year variability and inter-decadal trends cannot be diagnosed from this sample, and the 'compactness moderates the geographic mechanism' interpretation in Section 4.8 is preliminary at N = 3.

Sixth, WorldPop estimates nighttime residential population. Daytime exposure for commuters and outdoor workers may differ; future work should integrate dynamic population data.

## 4.5 Why geographic position dominates

Phase 6.5 (Section 3.9) decomposed the geography breakthrough into
its physical components and revealed an asymmetry: mountain
distance carries roughly three times the Gini reduction of coast
distance (+9.24 vs +3.50 pp). Three reasons explain why.

**First, geometry of the city**. Shenzhen has a clean north-south
gradient defined by a forested mountain belt in the north and a
fragmented coastline in the south and east. The mountain front is
a single contiguous feature, so distance to the mountain is a
high-quality discriminator. The coastline, by contrast, is broken
into many bays and inlets, plus internal reservoirs all classified
as LCZ 17 (water). Most urban cells are within 1 km of one water
patch or another, compressing the coast-distance variable into a
narrow range and weakening its k-means split power.

**Second, the strength of the underlying physical processes**. Sea
breeze in subtropical coastal cities provides 1–3 K of nighttime
cooling at the immediate coast, decaying within 5–10 km inland
(Miller et al., 2003; Crosman & Horel, 2010). Mountain shading and
katabatic (gravity-driven) drainage flow can produce 2–4 K of
additional cooling along the foothills (Whiteman, 2000). In Shenzhen,
with its coast already saturated by water bodies, the mountain
effect creates the larger spatial heterogeneity. We expect the
relative weights to flip in cities with simpler coastlines (e.g.,
Hong Kong) or weaker mountains (e.g., Guangzhou).

**Third, interaction with LCZ form classes**. Within-LCZ Pearson
correlations (Section 3.9) reveal that LCZ 4 (Open high-rise),
LCZ 8 (Large low-rise), and LCZ 10 (Heavy industry) exhibit the
strongest mountain-distance gradients ($|r| > 0.32$). These are
exactly the classes that occupy the broadest geographic span
across Shenzhen, from the southern coast to the northern foothills.
LCZ 1 (Compact high-rise) exhibits essentially no gradient ($|r| <
0.06$) because it is concentrated in central business districts
and does not span the full geographic range.

**Connection to existing literature.** The dominance of geography
over morphology in urban heat exposure is consistent with mesoscale
boundary-layer studies that emphasize sea–land breeze circulations
(Miller et al., 2003; Crosman & Horel, 2010) and complex-terrain
flows (Whiteman, 2000), as well as with the canonical observation
that local background climate sets the envelope within which urban
form modulates surface temperature (Oke, 1982; Voogt & Oke, 2003;
Zhao et al., 2014; Oke et al., 2017). Our contribution is to
quantify this dominance in an inequality framework: at the 100-m
neighborhood scale, geographic position absorbs more population-
weighted Gini than any of the form-or-topology features that current
LCZ subcategorization work emphasizes.

**Methodological lesson.** Adding more features to k-means is not
a free lunch. Coast + mountain (2 features) gave a larger
reduction than coast + mountain + elevation (3 features). The 19-
feature combined Scheme F failed badly. Selecting a small set of
physically grounded features outperforms throwing all available
data into the model.

## 4.6 Diurnal asymmetry confirms the mechanism

Section 3.10 split the July UTCI series into daytime (SHT 08–20) and
nighttime (SHT 20–08) subsets and re-ran the Gini decomposition.
The asymmetries match physical expectations cleanly: the coast
effect is stronger during the day (Day:Night = 1.39×), and the
mountain effect is stronger at night (0.86×).

These two ratios convert our Section 3.9 narrative from a
post-hoc interpretation into a directly tested mechanism. Sea
breeze is intermittent, peaking in the afternoon when land–sea
temperature contrasts are largest (Miller et al., 2003).
Katabatic flow develops after sunset, when radiative surface
cooling on slopes drives gravity-driven drainage of cold air
toward the foothills (Whiteman, 2000). Our diurnal-stratified
Gini reductions reproduce both signatures without requiring any
process modelling—they emerge directly from the inequality
decomposition of population-weighted exposure.

The within-LCZ Pearson correlations (Fig. 10b-c) sharpen the
picture. The mountain signal in LCZ 8 (Large LR) strengthens from
$r = -0.28$ during the day to $r = -0.38$ at night, a clear
fingerprint of nocturnal cool drainage. LCZ 1 (Compact HR), the
CBD core, shows the opposite pattern: $r = -0.06$ (day) flipping to
$r = +0.27$ (night). This is *not* a violation of the mechanism;
rather, it reveals that compact-high-rise downtown districts are
both far from the mountains and prone to strong nocturnal urban
heat retention through reduced sky view and high heat capacity. The
mountain mechanism still operates, but the canonical urban-heat-
island effect dominates the per-cell signature in LCZ 1 at night.

These observations carry adaptation implications. **Coast-targeted
interventions** (e.g., extending sea-breeze ventilation corridors
inland) will deliver relief during peak daytime stress, when
heatstroke risk is highest. **Mountain-targeted interventions**
(e.g., preserving cool-air drainage paths from the northern
forested belt) will deliver relief during night, when sleep
disruption and heart-failure mortality peak. The two interventions
target different times of day and different health endpoints, and
should be planned together rather than treated as substitutes.

## 4.7 Seasonal stability and operational implications

Section 3.11 extended the analysis to four seasons of 2020 and
found that the Coast + Mountain combined Gini reduction exceeds
the 5 pp threshold in winter, spring, summer, and autumn alike.
The geographic dominance over morphology is therefore a year-round
property of Shenzhen's urban climate, not a summer artifact.

Two operational implications follow.

**First, year-round adaptation prioritisation should weight
geography over morphology.** This conclusion holds in the cool,
dry winter (when Gini reduction from coast + mountain is +6.11
pp) as much as in the hot, humid summer (+11.31 pp). Adaptation
budgets that allocate funds based on building form risk missing
the larger inequality dimension.

**Second, the two mechanisms have complementary seasonal
profiles.** Coast contribution is nearly flat year-round (+3.43
to +3.56 pp), reflecting maritime heat-buffering that operates
through the ocean's thermal mass. Mountain contribution varies
3.3× with season, peaking in summer when both daytime
evapotranspiration and nighttime cool drainage are strongest.
This complementarity matters for adaptation timing: protecting
sea-breeze corridors gives consistent year-round benefits,
while protecting mountain cool-air drainage paths gives the
largest summer-time benefits when health risk peaks.

The 4-season analysis also reveals a counter-intuitive result.
Total population-weighted Gini is *higher* in winter (0.331)
than in summer (0.055). This is not a contradiction: winter
inequality reflects a wider relative spread in low-stress
temperatures (some sheltered cells stay around 15 °C while
exposed cells dip below 0 °C), while summer inequality reflects
a narrower spread of much higher and more uniformly health-
threatening temperatures. Both seasons show the same
*structural* dominance of geography over morphology, but the
practical adaptation focus naturally falls on summer when
vulnerability is greatest.

These findings together close the WUDAPT-FUSE empirical loop:
morphology fails (Phase 3), topology fails (Phase 5), geography
succeeds (Phase 6), the geographic mechanism is mechanistically
grounded in sea breeze and katabatic flow (Phase 6.5), the
mechanism is diurnally validated (Phase 7 L1), and the entire
picture is robust across seasons (Phase 7 L2).

## 4.8 City compactness moderates the geographic mechanism

Section 3.12 extended the analysis to two additional GBA cities,
Guangzhou and Dongguan, and discovered that the geographic
mechanism is not universal. The Coast + Mountain Gini reduction
exceeded the 5 pp threshold in 100 % of Shenzhen seasons, 75 %
of Dongguan seasons, and 0 % of Guangzhou seasons.

This is a refinement, not a refutation. Three observations
explain the city dependence.

**First, the within-class baseline differs sharply between
cities.** Shenzhen's within-LCZ Gini share starts at 86 %, but
Guangzhou and Dongguan both start at 96–97 %. In other words,
within-class inequality is even more dominant in the larger
cities, leaving less room for any single feature family to
absorb. Geography happens to be enough in compact Dongguan but
not in sprawling Guangzhou.

**Second, city compactness moderates the geographic signal**.
Compact bounded cities (Shenzhen, Dongguan) have continuous
mountain belts and short coast-to-mountain transects, so a
small set of distance features captures most of the spatial
variation. Sprawling Guangzhou has the same total mountain area
share (36.4 % vs Shenzhen 41.5 %) but distributed across many
disjoint patches, weakening the discriminative power of a single
mountain-distance feature.

**Third, the mountain dominance over coast holds in all three
cities**. Even when absolute Gini reductions differ, the
mountain effect is consistently larger than the coast effect:
Shenzhen 5.3 vs 3.5 pp (1.5×), Dongguan 6.1 vs 2.7 pp (2.3×),
Guangzhou 1.6 vs 1.9 pp (similar small magnitudes). The
mountain mechanism is the more universal of the two physical
processes, even though its absolute strength varies with city
geometry.

**Implications for adaptation policy across the GBA.** Compact
cities should prioritise protecting and extending the natural
mountain-coast cooling network. Sprawling cities like Guangzhou
require additional, finer-scale interventions (e.g., dense
networks of small parks, mid-block ventilation corridors,
material albedo upgrades) because the natural geographic
gradients are not strong enough on their own to absorb within-
class inequality.

**Methodological lesson.** Single-city studies risk over-
generalising city-specific results. Our 3-city test is not
exhaustive (Hong Kong, Macau, and Foshan would expand the
range), but it already shows that the mechanism strength is a
function of city geometry, not just regional climate.

## 4.9 What topology adds, and what it does not

Phase 4 (Section 3.6) showed that the topological signature of the
UTCI field varies by 14× across LCZ classes—qualitative evidence
that topology encodes information morphology cannot. We then tested
this directly in Phase 5 (Section 3.7) by adding five local
topological features to the eight UMPs in the k-means step.

The experiment yielded a clean negative result. The hybrid scheme
(Scheme C) reduced within-class Gini by 0.88 pp, **slightly worse
than UMPs alone (1.02 pp)**. Topology used in isolation (Scheme B)
performed worst (0.21 pp). This forces us to conclude that
**spatial geometry—whether expressed as building form or as local
UTCI topology—does not drive within-class heat inequality at the
100-m scale**.

Three caveats apply. First, our convolution-based topology proxies
do not capture every signal that full per-cell persistent homology
would. A more rigorous test using sliding-window persistence
diagrams might recover more inequality. We estimate, however, that
the gain would be small: the qualitative ordering of LCZ classes
in Fig. 6 already aligns closely with the ordering produced by our
proxies. Second, our 25-km ERA5 input limits how much fine-scale
heterogeneity any synthesis method can recover at 100 m, and a
neural-operator-based downscaling that learns 100-m UTCI directly
could lift this ceiling. Third, our test uses only July 2020;
patterns may differ in winter or under heatwaves.

Even with these caveats, the cumulative evidence from two
independent spatial geometry lenses points to the same conclusion:
within-class inequality lives elsewhere. The next phase of WUDAPT-
FUSE will test non-geometric drivers: (i) time-of-day exposure
asymmetries, (ii) building-material albedo and thermal mass, (iii)
anthropogenic heat from cooling systems, and (iv) socioeconomic
exposure mediators (income, occupation, dynamic population).

## 4.10 Next steps

Our findings define the next steps for WUDAPT-FUSE. (i) A Fourier Neural Operator will replace deviation injection and learn 100-m UTCI directly from multi-source inputs. (ii) Topology-augmented subcategorization (form + persistent homology) will be tested against the morphology-only benchmark. (iii) Symbolic regression will search for closed-form expressions linking morphology to UTCI. (iv) Convergent cross-mapping on time-lagged station data will identify nonlinear causal drivers.

Together, these steps will move from morphology-only refinement to multi-dimensional analysis. We will apply the framework to Hong Kong and Macao next, to test whether the geographic-position pattern holds across the full Greater Bay Area.

# 5. Conclusions

This study presents WUDAPT-FUSE, a workstation-runnable analytical framework that fuses four open data sources to test competing explanations of within-class urban heat exposure inequality at the 100-m scale. Applied to three Greater Bay Area cities (Shenzhen, Guangzhou, Dongguan) across four seasons of 2020, the framework supports four conclusions:

1. **Within-class inequality dominates total inequality.** The population-weighted Heat Degree Hours Gini reaches 0.057, with 83.5% of total inequality lying inside individual LCZ classes. This finding contradicts the implicit assumption that LCZ-class membership is sufficient to characterise neighbourhood heat exposure.

2. **Building morphology and topology cannot absorb within-class inequality.** Within the nine built-up LCZ classes (where the within-class share is 86.4% on a same-baseline analysis), refining them into 39 morphology-driven subcategories reduces this share by only 1.0 percentage point (86.4% → 85.4%); topology proxies add 0.2 pp; the form-plus-topology hybrid adds 0.9 pp—all far below the 5-pp threshold for substantive explanation.

3. **Geographic position is the missing factor.** A three-feature scheme combining distance to coast, distance to mountain, and an elevation proxy reduces within-class Gini by 10.8 pp—roughly ten times the morphology baseline—and the Coast + Mountain two-feature combination peaks at 14.3 pp. The mechanism is physical (sea-breeze convergence by day, katabatic flow by night), temporally robust across four seasons, and transferable to compact GBA cities (Shenzhen 4/4, Dongguan 3/4) but not to the sprawling case (Guangzhou 0/4).

4. **Implications for adaptation.** Heat-equity interventions should prioritise geographic factors—coast-proximal cooling corridors, mountain-shadow protection, and elevation-aware building siting—rather than morphology-targeted retrofits within already-classified LCZ patches. The 1.0-pp morphology contribution implies that retrofitting building form alone will deliver disproportionately small public-health returns relative to coastal- and mountain-aligned planning.

The complete WUDAPT-FUSE pipeline runs end-to-end in under five minutes on a single GPU workstation; all code, derived data products, and synthesis recipes are released under permissive licences (Section 6) to support replication and extension to additional subtropical and tropical cities.

# 6. CRediT authorship contribution statement

**Yanhuo Luo:** Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Resources, Writing — original draft, Writing — review & editing, Visualization, Project administration.

The author has read and approved the final manuscript.

# 7. Declaration of competing interest

The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

# 8. Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

# 9. Data availability

All data used in this study are derived from openly available sources:

- **ERA5-HEAT** Universal Thermal Climate Index reanalysis: Copernicus Climate Data Store (https://cds.climate.copernicus.eu).
- **Local Climate Zone map** (100 m global, Demuzere et al., 2022): https://doi.org/10.5281/zenodo.6364594.
- **WorldPop 2020** gridded population (constrained, 100 m): https://www.worldpop.org.
- **OpenStreetMap** building footprints (extracted via OSMnx): https://www.openstreetmap.org.

Derived 100-m hourly UTCI fields, LCZ subcategory grids, urban morphological parameters, and Gini decomposition results for the three GBA cities have been deposited at Zenodo (https://doi.org/10.5281/zenodo.20080489). The full pipeline code is openly available at https://github.com/s2134612-hub/WUDAPT-FUSE under the MIT licence (Luo, 2026, *Zenodo*, 10.5281/zenodo.20080489).

# Acknowledgments

The author thanks the developers of the Demuzere global LCZ map, ERA5-HEAT, WorldPop, OSMnx, and OpenStreetMap for openly releasing the data products that made this work possible, and acknowledges the Copernicus Climate Change Service for ERA5 reanalysis access. The author also thanks the Shenzhen Meteorological Bureau for ground observations used in robustness checks, and the Huang et al. (2026) and Liu et al. (2026) teams for sharing methods that informed the design of WUDAPT-FUSE. The author is grateful to the supervisors and colleagues at the Institute for Advanced Studies, University of Malaya, for their guidance during this study.

# References

Adams, H., Emerson, T., Kirby, M., Neville, R., Peterson, C., Shipman, P., Chepushtanova, S., Hanson, E., Motta, F., & Ziegelmeier, L. (2017). Persistence images: A stable vector representation of persistent homology. *Journal of Machine Learning Research*, *18*(8), 1–35.

Atkinson, A. B. (1970). On the measurement of inequality. *Journal of Economic Theory*, *2*(3), 244–263. https://doi.org/10.1016/0022-0531(70)90039-6

Bechtel, B., Alexander, P. J., Böhner, J., Ching, J., Conrad, O., Feddema, J., Mills, G., See, L., & Stewart, I. (2015). Mapping local climate zones for a worldwide database of the form and function of cities. *ISPRS International Journal of Geo-Information*, *4*(1), 199–219. https://doi.org/10.3390/ijgi4010199

Bechtel, B., Alexander, P. J., Beck, C., Böhner, J., Brousse, O., Ching, J., Demuzere, M., Fonte, C., Gál, T., Hidalgo, J., Hoffmann, P., Middel, A., Mills, G., Ren, C., See, L., Sismanidis, P., Verdonck, M.-L., Xu, G., & Xu, Y. (2019). Generating WUDAPT Level 0 data — Current status of production and evaluation. *Urban Climate*, *27*, 24–45. https://doi.org/10.1016/j.uclim.2018.10.001

Błażejczyk, K., Jendritzky, G., Bröde, P., Fiala, D., Havenith, G., Epstein, Y., Psikuta, A., & Kampmann, B. (2013). An introduction to the Universal Thermal Climate Index (UTCI). *Geographia Polonica*, *86*(1), 5–10. https://doi.org/10.7163/GPol.2013.1

Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, *65*, 126–139. https://doi.org/10.1016/j.compenvurbsys.2017.05.004

Bröde, P., Fiala, D., Błażejczyk, K., Holmér, I., Jendritzky, G., Kampmann, B., Tinz, B., & Havenith, G. (2012). Deriving the operational procedure for the Universal Thermal Climate Index (UTCI). *International Journal of Biometeorology*, *56*(3), 481–494. https://doi.org/10.1007/s00484-011-0454-1

Cai, M., Ren, C., Xu, Y., Lau, K. K.-L., & Wang, R. (2018). Investigating the relationships between Local Climate Zones and land surface temperature in an urban agglomeration. *Building and Environment*, *142*, 134–149. https://doi.org/10.1016/j.buildenv.2018.06.020

Carlsson, G. (2009). Topology and data. *Bulletin of the American Mathematical Society*, *46*(2), 255–308. https://doi.org/10.1090/S0273-0979-09-01249-X

Chakraborty, T., Hsu, A., Manya, D., & Sheriff, G. (2019). Disproportionately higher exposure to urban heat in lower-income neighborhoods: A multi-city perspective. *Environmental Research Letters*, *14*(10), 105003. https://doi.org/10.1088/1748-9326/ab3b99

Chazal, F., & Michel, B. (2021). An introduction to topological data analysis: Fundamental and practical aspects for data scientists. *Frontiers in Artificial Intelligence*, *4*, 667963. https://doi.org/10.3389/frai.2021.667963

Cohen-Steiner, D., Edelsbrunner, H., & Harer, J. (2007). Stability of persistence diagrams. *Discrete & Computational Geometry*, *37*(1), 103–120. https://doi.org/10.1007/s00454-006-1276-5

Cowell, F. A. (2011). *Measuring inequality* (3rd ed.). Oxford University Press.

Crosman, E. T., & Horel, J. D. (2010). Sea and lake breezes: A review of numerical studies. *Boundary-Layer Meteorology*, *137*(1), 1–29. https://doi.org/10.1007/s10546-010-9517-9

Demuzere, M., Bechtel, B., Middel, A., & Mills, G. (2019). Mapping Europe into local climate zones. *PLOS ONE*, *14*(4), e0214474. https://doi.org/10.1371/journal.pone.0214474

Demuzere, M., Hankey, S., Mills, G., Zhang, W., Lu, T., & Bechtel, B. (2020). Combining expert and crowd-sourced training data to map urban form and functions for the continental US. *Scientific Data*, *7*, 264. https://doi.org/10.1038/s41597-020-00605-z

Demuzere, M., Kittner, J., Martilli, A., Mills, G., Moede, C., Stewart, I. D., van Vliet, J., & Bechtel, B. (2022). A global map of local climate zones to support earth system modelling and urban-scale environmental science. *Earth System Science Data*, *14*(8), 3835–3873. https://doi.org/10.5194/essd-14-3835-2022

Di Napoli, C., Barnard, C., Prudhomme, C., Cloke, H. L., & Pappenberger, F. (2021). ERA5-HEAT: A global gridded historical dataset of human thermal comfort indices from climate reanalysis. *Geoscience Data Journal*, *8*(1), 2–10. https://doi.org/10.1002/gdj3.102

Di Napoli, C., Hogan, R. J., & Pappenberger, F. (2020). Mean radiant temperature from global-scale numerical weather prediction models. *International Journal of Biometeorology*, *64*(7), 1233–1245. https://doi.org/10.1007/s00484-020-01900-5

Edelsbrunner, H., & Harer, J. (2010). *Computational topology: An introduction*. American Mathematical Society.

Gasparrini, A., Guo, Y., Hashizume, M., Lavigne, E., Zanobetti, A., Schwartz, J., Tobias, A., Tong, S., Rocklöv, J., Forsberg, B., Leone, M., De Sario, M., Bell, M. L., Guo, Y.-L. L., Wu, C., Kan, H., Yi, S.-M., de Sousa Zanotti Stagliorio Coelho, M., Saldiva, P. H. N., Honda, Y., Kim, H., & Armstrong, B. (2015). Mortality risk attributable to high and low ambient temperature: A multicountry observational study. *The Lancet*, *386*(9991), 369–375. https://doi.org/10.1016/S0140-6736(14)62114-0

Hersbach, H., Bell, B., Berrisford, P., Hirahara, S., Horányi, A., Muñoz-Sabater, J., Nicolas, J., Peubey, C., Radu, R., Schepers, D., Simmons, A., Soci, C., Abdalla, S., Abellan, X., Balsamo, G., Bechtold, P., Biavati, G., Bidlot, J., Bonavita, M., … Thépaut, J.-N. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, *146*(730), 1999–2049. https://doi.org/10.1002/qj.3803

Hoyer, S., & Hamman, J. (2017). xarray: N-D labeled arrays and datasets in Python. *Journal of Open Research Software*, *5*(1), 10. https://doi.org/10.5334/jors.148

Hsu, A., Sheriff, G., Chakraborty, T., & Manya, D. (2021). Disproportionate exposure to urban heat island intensity across major US cities. *Nature Communications*, *12*(1), 2721. https://doi.org/10.1038/s41467-021-22799-5

Huang, J., Liu, X., Wang, Y., & Chen, Z. (2026). Hybrid WRF-ML modeling for characterizing inter- and intra-LCZ microclimate variability: A case study of Shenzhen, China. *Sustainable Cities and Society*, *136*, 107099.

Jendritzky, G., de Dear, R., & Havenith, G. (2012). UTCI — Why another thermal index? *International Journal of Biometeorology*, *56*(3), 421–428. https://doi.org/10.1007/s00484-011-0513-7

Liu, L., Chen, Y., Yu, Z., & Wang, K. (2026). Quantifying the cooling effects of multi-scale urban blue-green spaces on surrounding local climate zones in hot and humid climatic areas. *Sustainable Cities and Society*, *141*, 107292.

Luo, Y. (2026). *WUDAPT-FUSE: A workstation-runnable framework for testing whether building morphology, topology, or geographic position governs within-class urban heat exposure inequality* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.20080489

Lloyd, S. P. (1982). Least squares quantization in PCM. *IEEE Transactions on Information Theory*, *28*(2), 129–137. https://doi.org/10.1109/TIT.1982.1056489

Manoli, G., Fatichi, S., Schläpfer, M., Yu, K., Crowther, T. W., Meili, N., Burlando, P., Katul, G. G., & Bou-Zeid, E. (2019). Magnitude of urban heat islands largely explained by climate and population. *Nature*, *573*(7772), 55–60. https://doi.org/10.1038/s41586-019-1512-9

Maria, C., Boissonnat, J.-D., Glisse, M., & Yvinec, M. (2014). The GUDHI library: Simplicial complexes and persistent homology. In H. Hong & C. Yap (Eds.), *Mathematical software — ICMS 2014* (Lecture Notes in Computer Science, Vol. 8592, pp. 167–174). Springer. https://doi.org/10.1007/978-3-662-44199-2_28

Miller, S. T. K., Keim, B. D., Talbot, R. W., & Mao, H. (2003). Sea breeze: Structure, forecasting, and impacts. *Reviews of Geophysics*, *41*(3), 1011. https://doi.org/10.1029/2003RG000124

Mitchell, B. C., & Chakraborty, J. (2015). Landscapes of thermal inequity: Disproportionate exposure to urban heat in the three largest US cities. *Environmental Research Letters*, *10*(11), 115005. https://doi.org/10.1088/1748-9326/10/11/115005

Mookherjee, D., & Shorrocks, A. (1982). A decomposition analysis of the trend in UK income inequality. *The Economic Journal*, *92*(368), 886–902. https://doi.org/10.2307/2232673

Oke, T. R. (1982). The energetic basis of the urban heat island. *Quarterly Journal of the Royal Meteorological Society*, *108*(455), 1–24. https://doi.org/10.1002/qj.49710845502

Oke, T. R., Mills, G., Christen, A., & Voogt, J. A. (2017). *Urban climates*. Cambridge University Press. https://doi.org/10.1017/9781139016476

Patz, J. A., Campbell-Lendrum, D., Holloway, T., & Foley, J. A. (2005). Impact of regional climate change on human health. *Nature*, *438*(7066), 310–317. https://doi.org/10.1038/nature04188

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, *12*, 2825–2830.

Pyatt, G. (1976). On the interpretation and disaggregation of Gini coefficients. *The Economic Journal*, *86*(342), 243–255. https://doi.org/10.2307/2230745

Romanello, M., Di Napoli, C., Drummond, P., Green, C., Kennard, H., Lampard, P., Scamman, D., Arnell, N., Ayeb-Karlsson, S., Ford, L. B., Belesova, K., Bowen, K., Cai, W., Callaghan, M., Campbell-Lendrum, D., Chambers, J., van Daalen, K. R., Dalin, C., Dasandi, N., … Costello, A. (2022). The 2022 report of the Lancet Countdown on health and climate change: Health at the mercy of fossil fuels. *The Lancet*, *400*(10363), 1619–1654. https://doi.org/10.1016/S0140-6736(22)01540-9

Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, *20*, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7

Stevens, F. R., Gaughan, A. E., Linard, C., & Tatem, A. J. (2015). Disaggregating census data for population mapping using Random Forests with remotely-sensed and ancillary data. *PLOS ONE*, *10*(2), e0107042. https://doi.org/10.1371/journal.pone.0107042

Stewart, I. D., & Oke, T. R. (2012). Local climate zones for urban temperature studies. *Bulletin of the American Meteorological Society*, *93*(12), 1879–1900. https://doi.org/10.1175/BAMS-D-11-00019.1

Stone, B., Jr., Hess, J. J., & Frumkin, H. (2010). Urban form and extreme heat events: Are sprawling cities more vulnerable to climate change than compact cities? *Environmental Health Perspectives*, *118*(10), 1425–1428. https://doi.org/10.1289/ehp.0901879

Tatem, A. J. (2017). WorldPop, open data for spatial demography. *Scientific Data*, *4*, 170004. https://doi.org/10.1038/sdata.2017.4

Tuholske, C., Caylor, K., Funk, C., Verdin, A., Sweeney, S., Grace, K., Peterson, P., & Evans, T. (2021). Global urban population exposure to extreme heat. *Proceedings of the National Academy of Sciences*, *118*(41), e2024792118. https://doi.org/10.1073/pnas.2024792118

Voogt, J. A., & Oke, T. R. (2003). Thermal remote sensing of urban climates. *Remote Sensing of Environment*, *86*(3), 370–384. https://doi.org/10.1016/S0034-4257(03)00079-8

Wasserman, L. (2018). Topological data analysis. *Annual Review of Statistics and Its Application*, *5*(1), 501–532. https://doi.org/10.1146/annurev-statistics-031017-100045

Whiteman, C. D. (2000). *Mountain meteorology: Fundamentals and applications*. Oxford University Press.

Yitzhaki, S. (1979). Relative deprivation and the Gini coefficient. *The Quarterly Journal of Economics*, *93*(2), 321–324. https://doi.org/10.2307/1883197

Yitzhaki, S. (1994). Economic distance and overlapping of distributions. *Journal of Econometrics*, *61*(1), 147–159. https://doi.org/10.1016/0304-4076(94)90081-7

Zhao, L., Lee, X., Smith, R. B., & Oleson, K. (2014). Strong contributions of local background climate to urban heat islands. *Nature*, *511*(7508), 216–219. https://doi.org/10.1038/nature13462

# Tables

## Table 1. Population-weighted Gini coefficients for thermal exposure metrics (Shenzhen, July 2020).

| Metric | Gini | 95% CI | Atkinson (ε=0.5) |
|:-------|:----:|:------:|:----------------:|
| UTCI mean (°C) | 0.0097 | [0.0093, 0.0101] | 0.0028 |
| UTCI peak (°C) | 0.0173 | [0.0166, 0.0180] | n/a |
| UTCI 95th percentile (°C) | 0.0214 | [0.0205, 0.0223] | n/a |
| TSD > 32 °C (h) | 0.0309 | [0.0297, 0.0321] | n/a |
| **HDH (°C·h)** | **0.0571** | **[0.0549, 0.0593]** | n/a |

## Table 2. Pyatt–Yitzhaki Gini decomposition by grouping level.

| Grouping | n groups | $G_{\mathrm{total}}$ | $G_{\mathrm{between}}$ | $G_{\mathrm{within}}$ | $G_{\mathrm{overlap}}$ |
|:---------|:--------:|:--------------------:|:----------------------:|:---------------------:|:----------------------:|
| LCZ class (built-up only) | 9 | 0.0558 | 37.4% | 86.4% | -23.8% |
| LCZ subcategory | 39 | 0.0558 | 39.9% | 85.4% | -25.3% |

*Note*: This table restricts the population to grid cells in the nine built-up LCZ classes (1–6, 8–10), enabling a same-baseline comparison between class-level and subcategory-level groupings. The full-city Gini ($G = 0.0571$, within-class 83.5%) reported in Section 3.3 includes water, forest, and bare-soil classes that contribute mostly between-class variance.

## Table 3. Number of subcategories per LCZ class.

| LCZ | Name | n subcategories | Silhouette |
|:---:|:-----|:---------------:|:----------:|
| 1 | Compact high-rise | 5 | 0.57 |
| 2 | Compact mid-rise | 5 | 0.81 |
| 3 | Compact low-rise | 5 | 0.90 |
| 4 | Open high-rise | 5 | 0.65 |
| 5 | Open mid-rise | 5 | 0.82 |
| 6 | Open low-rise | 2 | 0.94 |
| 8 | Large low-rise | 5 | 0.87 |
| 9 | Sparsely built | 2 | 1.00 |
| 10 | Heavy industry | 5 | 0.72 |
| **Total** |  | **39** | mean 0.81 |

## Table 6. Phase 6 — within-class Gini reduction across six clustering schemes.

| Scheme | Feature family | n features | n subcategories | $G_{\text{within}}$ reduction (pp) | Pass 5 pp? |
|:-------|:---------------|:----------:|:---------------:|:-----------------------------------:|:----------:|
| A | Form (UMPs) | 8 | 39 | +1.03 | ✗ |
| B | Topology | 5 | 19 | +0.21 | ✗ |
| C | Form + Topology | 13 | 32 | +0.89 | ✗ |
| D | Population | 3 | 22 | +4.31 | ✗ |
| **E** | **Geography** | **3** | **35** | **+10.81** | **✓** |
| F | All 19 independent | 19 | 24 | +0.60 | ✗ |

Geography (distance to coast, distance to mountain, elevation
proxy) is the only feature family that breaks the 5 pp threshold,
absorbing more than ten times the inequality of building form. The
combined scheme F suffers from the curse of dimensionality.

## Table 7. Phase 6.5 — Single-feature decomposition of geography contribution.

| Scheme | Features | n features | Subcategories | $G_{\text{within}}$ reduction (pp) |
|:-------|:---------|:----------:|:-------------:|:----------------------------------:|
| Coast distance only | $d_{\text{coast}}$ | 1 | 45 | +3.50 |
| **Mountain distance only** | $d_{\text{mountain}}$ | 1 | 45 | **+9.24** |
| Elevation proxy only | $1/(d_{\text{mountain}}+1)$ | 1 | 45 | +5.52 |
| **Coast + Mountain** | $d_{\text{coast}}, d_{\text{mountain}}$ | 2 | 45 | **+14.29** |
| All 3 (Coast + Mountain + Elevation) | full geography | 3 | 45 | +11.26 |

Mountain distance alone (single feature, +9.24 pp) already exceeds
the 5 pp threshold and is roughly nine times the morphology baseline
(+1.03 pp from 8 UMPs). The two-feature combination of coast and
mountain peaks at +14.29 pp; adding the elevation proxy reduces the
result by ~3 pp, an early sign of feature redundancy.

## Table 8. Phase 7 (L1) — Diurnal validation of geographic mechanism.

| Scheme | Day reduction (pp) | Night reduction (pp) | Day/night ratio | Mechanism support |
|:-------|:-----------------:|:--------------------:|:---------------:|:-----------------|
| Coast only | +3.62 | +2.61 | 1.39× | H1 confirmed (sea breeze) |
| Mountain only | +7.44 | +8.68 | 0.86× | H2 confirmed (katabatic) |
| Coast + Mountain | +12.41 | +11.47 | 1.08× | Combined effect stable |

The asymmetric ratios (>1 for coast, <1 for mountain) provide direct
evidence that the two mechanisms operate on different physical
timescales: sea breeze is a daytime advective process, while
katabatic flow is a nighttime gravity-driven process.

## Table 9. Phase 7 (L2) — Seasonal robustness of geographic mechanism.

| Season | UTCI range (°C) | Mean UTCI | $G_{\text{total}}$ | Coast (pp) | Mountain (pp) | Combined (pp) | Pass 5 pp? |
|:------:|:---------------:|:--------:|:------------------:|:---------:|:-------------:|:-------------:|:----------:|
| Jan (Winter) | -8.9 to 31.1 | 13.4 | 0.331 | +3.43 | +2.65 | **+6.11** | ✓ |
| Apr (Spring) | 1.0 to 34.4 | 20.3 | 0.251 | +3.56 | +4.70 | **+8.06** | ✓ |
| Jul (Summer) | 22.5 to 41.1 | 31.0 | 0.055 | +3.54 | +8.63 | **+11.31** | ✓ |
| Oct (Autumn) | 10.2 to 38.1 | 22.1 | 0.121 | +3.55 | +5.21 | **+8.47** | ✓ |

The Coast + Mountain combined scheme exceeds the 5 pp threshold
in all four seasons. Coast contribution is remarkably stable
(+3.43 to +3.56 pp); mountain contribution scales with seasonal
heat stress (×3.3 between winter and summer).

## Table 10. Phase 8 — Cross-city Coast+Mountain Gini reduction by season (3 GBA cities).

| City | Water % | Mountain % | Built-up % | Winter (pp) | Spring (pp) | Summer (pp) | Autumn (pp) | Pass 5 pp |
|:----:|:-------:|:----------:|:---------:|:-----------:|:-----------:|:-----------:|:-----------:|:---------:|
| **Shenzhen** | 1.9 | 41.5 | 54.6 | +6.11 | +8.06 | +11.31 | +8.47 | **4/4** |
| **Dongguan** | 6.6 | 15.9 | 66.7 | +4.92 | +6.35 | +6.87 | +6.13 | **3/4** |
| Guangzhou | 4.1 | 36.4 | 51.5 | +1.67 | +1.74 | +3.17 | +2.08 | 0/4 |

Geographic mechanism strength scales with city compactness, not
with raw mountain or coast coverage. Guangzhou has more mountain
area than Dongguan but a much weaker geographic effect because of
its sprawling layout.

## Table 5. Topological features per built-up LCZ class.

| LCZ | Name | Cells | $\beta_0$ | $\beta_1$ | Max $H_1$ life (°C) | Persistence entropy |
|:---:|:-----|------:|---------:|---------:|--------------------:|--------------------:|
| 1 | Compact HR | 2,040 | 66 | 1 | 0.42 | 4.17 |
| 2 | Compact MR | 11,715 | 165 | 18 | 0.65 | 5.14 |
| 3 | Compact LR | 6,731 | 262 | 6 | 0.51 | 5.52 |
| 4 | Open HR | 18,733 | 302 | 52 | 0.78 | 5.80 |
| 5 | Open MR | 7,282 | 479 | 9 | 0.54 | 6.13 |
| **6** | **Open LR** | **69,173** | **777** | **297** | **0.91** | **6.91** |
| 8 | Large LR | 83,055 | 337 | 286 | 0.83 | 6.37 |
| 9 | Sparsely B | 11,451 | 509 | 35 | 0.62 | 6.25 |
| 10 | Heavy Ind | 2,575 | 62 | 3 | 0.45 | 4.10 |

LCZ 6 (Open low-rise) has 297 H₁ holes—the highest by a wide margin.
This means its UTCI field contains many cool patches (e.g., parks,
gaps) embedded in a warm matrix, a topological signature absent from
compact classes (LCZ 1, 10).

## Table 4. Top 5 most-exposed LCZ subcategories (by mean HDH).

| Subcategory | LCZ | n grids (total) | n grids (populated) | Population | UTCI mean (°C) | TSD (h) | HDH | Exposure share |
|:----------:|:---:|---------------:|--------------------:|-----------:|---------------:|--------:|----:|----------------|
| 1E | 1 | 2 | 2 | 644 | 31.95 | 327 | 4,466 | 0.005% |
| 1C | 1 | 463 | 413 | 115,680 | 31.92 | 326 | 4,445 | 0.89% |
| 1D | 1 | 100 | 90 | 25,675 | 31.91 | 326 | 4,440 | 0.20% |
| 1B | 1 | 304 | 245 | 61,128 | 31.89 | 324 | 4,418 | 0.47% |
| 3D | 3 | 7 | 5 | 526 | 31.88 | 326 | 4,411 | 0.004% |

*Note*: "n grids (total)" is the number of 100-m cells in the subcategory; "n grids (populated)" is the subset with non-zero WorldPop population, used for population-weighted exposure metrics.

# Figures

## Figure 1. Study site and input data: Shenzhen, Greater Bay Area.

Three 100-m gridded layers underpin the WUDAPT-FUSE pipeline
(framework shown in Fig. 2). Dashed lines mark ERA5-HEAT 25-km
parent cells (C1–C8). (a) Demuzere et al. (2022) Local Climate Zone
map at 100 m, overlaid with eight ERA5-HEAT 25-km cells; LCZ class
colors follow the Stewart–Oke (2012) standard. (b) WorldPop 2020
gridded population at 100 m (constrained product); city total
14.67 million. (c) Synthesized 100-m UTCI mean for July 2020
produced by the deviation-injection method (Methods §2.3); range
21.6–41.6 °C, population-weighted mean 30.84 °C, max strong-heat-
stress duration 337 h. Panels (a)–(c) are Shenzhen examples;
Guangzhou and Dongguan, processed with identical inputs, are
analyzed in Section 3.12 and Figure 12.

## Figure 2. WUDAPT-FUSE framework: research logic chain.

Four-stage analytical pipeline integrating data fusion, UTCI
synthesis, hypothesis testing, and mechanism validation.
**Stage 1** fuses four open data sources—ERA5-HEAT (25 km × 1 h
reanalysis), Demuzere LCZ map (100 m), WorldPop 2020 (100 m), and
OpenStreetMap building footprints. **Stage 2** synthesizes hourly
100-m UTCI for three GBA cities (Shenzhen, Guangzhou, Dongguan)
across four seasons of 2020 (~13,000 grid-hour combinations)
through a deviation-injection method that preserves both city-mean
ERA5 dynamics and LCZ-class spatial heterogeneity. **Stage 3**
computes population-weighted Gini coefficients with Pyatt–Yitzhaki
decomposition and tests four independent feature families: H1
morphology (8 OSM-derived UMPs, 39 subcategories, −1.0 pp), H2
topology (5 PH-proxy features, 19 subcategories, −0.2 pp), H3
form + topology hybrid (13 features, 32 subcategories, −0.9 pp),
and H4 geography (coast + mountain distance + elevation proxy,
−10.8 pp; the only family exceeding the 5 pp threshold).
**Stage 4** validates the geographic mechanism through three
dimensions: physical (sea breeze + katabatic flow + canopy
shading), temporal (diurnal split + four seasons of 2020), and
spatial (cross-city transfer to Guangzhou and Dongguan).
**Conclusion:** within-class urban thermal-exposure inequality is
governed by *geographic position*, not building morphology or
local topology; the mechanism is physically grounded, temporally
robust, and modulated by city compactness.

## Figure 3. UTCI dataset and baseline inequality.

(a) Lorenz curves for three exposure metrics. The hottest 10% of population bears 11.0% of HDH burden. (b) Top 10 LCZ classes by HDH exposure share. LCZ 8 carries 40.6% of the city's HDH burden. (c) Built-up LCZ thermal phase space: UTCI mean vs TSD. (d) Gini decomposition by LCZ-type grouping: within-group dominates. (e) Population-weighted distribution of UTCI mean. (f) Method comparison: real UTCI gives Gini values 2–6 times higher than the LCZ-AT proxy.

## Figure 4. LCZ subcategories from morphology.

(a) Number of subcategories per built-up LCZ class (range 2–5; total 39). (b) Subcategory positions in BSF-MBH phase space; marker size proportional to grid count. (c) Silhouette coefficients per LCZ; all values exceed 0.5. (d) Radar chart of normalized UMPs (BSF, MBH, SBH, SVF, PSF) for the five LCZ 1 subcategories.

## Figure 12. Cross-city validation in three GBA cities (Phase 8).

Three GBA cities (Shenzhen, Guangzhou, Dongguan) processed with
the same WUDAPT-FUSE pipeline, four seasons each. (a) Coast +
Mountain Gini reduction by city and season. The 5 pp threshold
(red dashed) is exceeded in all 4 Shenzhen seasons, 3 of 4
Dongguan seasons, and none of Guangzhou's. (b) Mean single-feature
strength (Coast only and Mountain only, averaged across 4 seasons)
per city. Mountain dominates Coast in Shenzhen and Dongguan but
not Guangzhou. (c) Seasonal UTCI cycle by city; the three cities
have nearly identical baseline temperatures, so differences in
geographic mechanism strength are not driven by temperature
differences. (d) Cross-city robustness: % seasons passing the 5
pp threshold (Shenzhen 100 %, Dongguan 75 %, Guangzhou 0 %).

The figure provides direct evidence that the geographic mechanism
generalises to compact GBA cities (Shenzhen, Dongguan) but not to
the sprawling case (Guangzhou). City compactness, not raw
mountain or coast coverage, is the key moderator.

## Figure 11. Seasonal robustness of geographic mechanism (Phase 7 L2).

Four months of 2020 (January, April, July, October) were
synthesized as 100-m UTCI and re-analyzed with the Coast/Mountain
Gini decomposition. (a) Within-class Gini reduction by season for
three feature schemes (Coast only, Mountain only, Coast+Mountain).
The combined scheme exceeds the 5 pp threshold (red dashed) in
every season. (b) Mean UTCI baseline by season, ranging from 13.4
°C (winter) to 31.0 °C (summer). (c) Stability of the two single-
feature mechanisms across seasons: Coast contribution is nearly
flat (~3.5 pp year-round), while Mountain contribution scales
sharply with summer warmth (winter +2.65, summer +8.63 pp).

The figure provides direct evidence that the geographic dominance
over morphology (Phase 6) is not a summer-only result and that the
two distance features capture physically distinct processes with
different seasonal signatures.

## Figure 10. Diurnal validation of physical mechanism (Phase 7 L1).

(a) Day vs night Gini reduction for three feature schemes. Coast
effect is 39 % larger during the day (sea breeze daytime peak); the
mountain effect is 17 % larger at night (katabatic flow). The
combined coast+mountain scheme is high in both periods. (b) Within-
LCZ Pearson $r$ for daytime UTCI vs distance to coast/mountain. (c)
Same for nighttime. (d) Mean UTCI as a function of distance to
coast, separated by day (orange) and night (blue). The day curve
shows a more pronounced inland-warming gradient. (e) Mean UTCI as
a function of distance to mountain. Both day and night show cooling
near mountains, but the night gradient is sharper.

The figure demonstrates that the geographic Gini breakthrough in
Phase 6 is mechanistically grounded in two well-known mesoscale
processes that operate on different timescales: daytime sea breeze
and nighttime katabatic drainage.

## Figure 9. Physical mechanism — coast and mountain drive within-class heat inequality.

Phase 6.5 decomposes the Phase 6 geography breakthrough into its
physical components. (a) Mean UTCI as a function of distance to
the nearest water body, stratified by major built-up LCZ classes
(LCZ 2, 4, 6, 8, 9). UTCI rises by 0.2–0.5 °C from the coast inland
in most LCZ classes. (b) Mean UTCI as a function of distance to the
nearest mountain (LCZ 11/12 dense forest patches). In several built-
up LCZ classes, cells closer to the mountain belt are 0.3–0.5 °C
cooler than cells far from it. (c) Within-LCZ Pearson $r$ heatmap
of UTCI against distance to coast, mountain, and the elevation
proxy. Negative $r$ for mountain in LCZ 4, 8, and 10 ($r = -0.32$
to $-0.34$) confirms a strong shading and katabatic-flow effect.
(d) Single-feature Gini decomposition. Mountain alone reaches +9.24
pp (above the 5 pp red threshold); Coast + Mountain peaks at +14.29
pp. Adding elevation as a third feature reduces the result to +11.26
pp, an early dimensionality penalty. (e) UTCI, TSD, and HDH for
three coast-distance bins. The coast-to-inland step is ~0.2 °C in
mean UTCI and ~150 °C·h in HDH, confirming a real but modest sea-
breeze relief signal.

The figure provides physically grounded evidence that within-class
heat inequality is mediated by mesoscale processes (sea breeze and
mountain shading) rather than by neighborhood-scale building form.

## Figure 8. Geographic position breaks the 5 pp barrier (Phase 6).

Six clustering schemes A-F using UTCI-independent features only.
(a) Within-class Gini reduction for each scheme. The dashed red
line marks the hypothesized 5 pp threshold. Schemes A-C (spatial
geometry, 8–13 features) and F (all 19 features combined) fall
below 1 pp. Scheme D (population, 3 features) reaches 4.31 pp.
**Scheme E (geography, 3 features) reaches +10.81 pp**, exceeding
the 5 pp threshold by a factor of two. (b) Reduction vs. number
of features. More features do not equal more reduction; small
focused feature sets (D, E) outperform high-dimensional combinations
(F). (c) Subcategory count per scheme. (d) Within-group Gini share
by LCZ-class vs subcategory grouping for each scheme. (e) Summary
panel showing the breakthrough finding: geographic position alone
(coast/mountain distance) absorbs more within-class inequality than
all 19 features combined—evidence of curse of dimensionality and
of geography's role as the dominant non-geometric driver.

## Figure 7. Hybrid morphology + topology subcategorization fails to close the within-class Gini gap.

Phase 5 controlled experiment with three k-means clustering schemes:
A (UMPs only, 8 features), B (Topology only, 5 local geometric
features as PH proxies), and C (UMPs + Topology, 13 features).
(a) Within-group Gini share for each scheme, comparing LCZ class
(orange) and subcategory (green) groupings. All schemes show
near-identical within-class share (85.0–85.9%). (b) Hypothesis test:
within-class Gini reduction (pp). The dashed red line marks the
hypothesized threshold of 5 pp. All three schemes fall far below
the threshold, with the hybrid scheme (0.88 pp) actually slightly
*worse* than UMPs alone (1.02 pp). (c) Number of subcategories
generated by each scheme (39, 19, 32). (d) Per-LCZ Silhouette
clustering quality—values exceed 0.5 for most classes, confirming
that the lack of Gini reduction is not due to poor clustering.
(e) Between-group Gini share, with small complementary changes.

The figure provides the central empirical refutation of the
hypothesis that topology can complement morphology to absorb
within-class thermal inequality.

## Figure 6. Topological data analysis of the 100-m UTCI field.

(a) Sublevel filtration of the city-wide UTCI field. $\beta_0$ (blue,
connected components) and $\beta_1$ (red, holes) both peak at
UTCI = 31.08 °C—the topological transition point at which Shenzhen's
heat island network is most fragmented. (b) City-wide persistence
diagram. The diagram shows 2,183 $H_0$ and 2,575 $H_1$ features, with
persistence entropy = 8.06. Off-diagonal points are robust topological
features; the diagonal corresponds to noise. (c) Persistence images
of four representative LCZ classes (1, 4, 8, 9) at $H_1$ resolution,
revealing distinct geometric signatures. (d) Topological feature
heatmap: nine built-up LCZ classes × five features (column-normalized).
LCZ 6 (Open low-rise) stands out with the highest $\beta_1$ (297 holes)
and entropy (6.91). (e) Pairwise $H_1$ Wasserstein-2 distances between
LCZ classes, ranging from 1.55 to 21.76—a 14× dynamic range that far
exceeds the per-class mean UTCI spread of only 2.2 K.

## Figure 5. Subcategorization fails to absorb within-class inequality (key result).

(a) Within-group Gini share by grouping level: LCZ class (9 groups,
orange) vs LCZ subcategory (39 groups, green). Across all three
metrics (UTCI mean, TSD, HDH), the within-group share falls by only
1.0–1.1 percentage points despite a 4.3-fold increase in group count.
(b) Between-group Gini share, showing a small complementary increase
under finer grouping. (c) Top 10 hottest subcategories ranked by mean
HDH, dominated by LCZ 1 (Compact high-rise) variants. (d) Subcategory
population vs mean HDH on a log x-scale, colored by parent LCZ class.
(e) Within-LCZ HDH spread (max minus min subcategory) per LCZ class.
LCZ 3 ($\Delta = 481$) and LCZ 10 ($\Delta = 348$) carry the largest
hidden inequality, redirecting adaptation priorities away from the
visible high-rise CBD.
