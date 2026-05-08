# Figure Captions

> 现有 4 张图的论文级详细说明文字。
> 每张图均产自 `figures/` 目录，约 100-200 KB 大小。
> 后续 Phase 4-6 会补 fig05 (TDA), fig06 (PySR), fig07 (causal)。

---

## Figure 1 — WUDAPT-FUSE Framework: workflow and study area

> 文件: `figures/fig01_concept.png` (503 KB, 1783 × 1385 px)
> 注: 之前 fig01 (Path C 代理基线) 已迁移至 figS1_preliminary_proxy.png

**(a)** WUDAPT-FUSE four-stage analytical workflow. **Stage 1**
fuses four data sources—ERA5-HEAT (25 km × 1 h reanalysis,
Copernicus CDS), Demuzere LCZ map (100 m, 2022), WorldPop 2020
gridded population (100 m, constrained), and OpenStreetMap building
footprints (151,896 polygons). **Stage 2** synthesizes hourly 100-m
UTCI for July 2020 (744 hours × 598,000 cells, range 21.6–41.6 °C)
through a deviation-injection method that preserves both city-mean
ERA5 dynamics and LCZ-class spatial heterogeneity. **Stage 3**
extracts eight urban morphological parameters (UMPs: BSF, MBH, SBH,
MBW, BV, GFA, SVF, PSF) from OSM buildings and applies k-means
clustering with Silhouette criterion (K ∈ {2…5}) to derive 39 LCZ
subcategories—1.5 × more refined than Huang et al. (2026).
**Stage 4** computes population-weighted Gini coefficients and
applies Pyatt-Yitzhaki decomposition at three grouping levels
(LCZ type, class, subcategory) to test the morphology-driven
subcategorization hypothesis.

**(b)** Shenzhen study area (113.7°–114.7° E, 22.4°–22.9° N),
showing the 100-m LCZ map. Built-up classes (LCZ 1–10, 54.6 % area)
cluster in the southern coastal plain; natural classes (LCZ 11–17,
45.4 %) dominate the northern mountain belt. The eight ERA5-HEAT
25-km cells (C1–C8) covering Shenzhen are overlaid as dashed black
lines, with cell centers marked by '+'. The complete LCZ legend
follows the Stewart-Oke (2012) standard color scheme.

**(c)** WorldPop 2020 100-m gridded population, showing 14.67 million
residents concentrated south of the mountain belt. Population
density reaches 366 persons per 100-m cell in dense urban districts;
ERA5 cell boundaries are overlaid as dotted white lines.

**(d)** Synthesized 100-m UTCI mean for July 2020. The
deviation-injection method preserves both large-scale ERA5 patterns
and LCZ-class anomalies (population-weighted city mean: 30.84 °C;
range across cells: 21.6–41.6 °C; maximum strong-stress duration:
337 hours = 45 % of July). White dashed lines indicate ERA5 25-km
cell boundaries.

The figure illustrates how WUDAPT-FUSE bridges the resolution gap
between coarse climate reanalysis (panel d shows fine spatial
structure absent from the original 25-km ERA5 input) and the
neighborhood-scale heterogeneity required for inequality analysis.

---

## Figure 2 — 100-m UTCI dataset characteristics and inequality
> 文件: `figures/fig02_utci_inequality.png` (174 KB)

**(a)** Lorenz curves of population vs. cumulative thermal exposure
for three metrics: UTCI mean (Gini = 0.0097), TSD > 32 °C
(Gini = 0.0309), and HDH (Gini = 0.0571). The hottest 10 % of
population bears 11.0 % of the total HDH burden.

**(b)** Top 10 LCZ classes by HDH exposure share. LCZ 8 (Large
low-rise) carries 40.6 % of the city's heat-degree-hour burden,
followed by LCZ 4 (20.8 %) and LCZ 2 (13.9 %). Built-up classes
(red) dominate over natural classes (green).

**(c)** Built-up LCZ thermal phase-space: mean UTCI vs TSD > 32 °C,
with marker size proportional to population. LCZ 1 shows the highest
UTCI mean and TSD; LCZ 9 the lowest.

**(d)** Gini decomposition of UTCI mean: between-LCZ-class component
(40.5 %) vs. within-LCZ-class (83.5 %). Within > between confirms
that intra-class heterogeneity dominates.

**(e)** Population-weighted distribution of UTCI mean. Bimodal shape
indicates two regimes (cool natural areas near the mountains vs.
warm urban core).

**(f)** Method comparison: Path C's LCZ-AT proxy yields a misleadingly
small inequality estimate (Gini = 0.027), while real ERA5-HEAT UTCI
indicators give 2-6× higher values. HDH is the most discriminating
metric.

---

## Figure 3 — LCZ subcategories from urban morphological parameters
> 文件: `figures/fig03_lcz_subcategories.png` (155 KB)

**(a)** Number of subcategories per built-up LCZ class. Most classes
(LCZ 1, 2, 3, 4, 5, 8, 10) split into 5 subcategories; LCZ 6 and 9
into 2. Total: 39 subcategories, vs. 26 reported by Huang et al. 2026
for the same city.

**(b)** Subcategory positions in BSF-MBH phase space. Marker size is
proportional to grid count. Subcategory labels follow the convention
LCZ<class><letter>, e.g., 1A is the lowest-BSF subset of LCZ 1.

**(c)** Silhouette coefficients per LCZ. All values exceed 0.5
(strong cluster quality, green dashed line); LCZ 9 reaches 0.99
(near-perfect separation between sparse and slightly built grids).

**(d)** Radar chart of normalized UMPs (BSF, MBH, SBH, SVF, PSF) for
the five LCZ 1 subcategories (1A–1E). Within a single LCZ class, BSF
spans 0.04–1.00 (×25) and MBH spans 4–286 m (×72), demonstrating
extreme intra-class morphological diversity.

---

## Figure 4 — Subcategorization fails to absorb within-class inequality (key result)
> 文件: `figures/fig04_subcategory_gini_test.png` (189 KB)

**(a)** Within-group Gini share (Pyatt-Yitzhaki decomposition)
under two grouping schemes: LCZ class (9 groups, orange) vs. LCZ
subcategory (39 groups, green). Across UTCI mean, TSD, and HDH, the
within-group share **decreases by only 1-2 percentage points**
despite a 4.3× increase in group count. This is the key empirical
refutation of the morphology-driven subcategorization hypothesis.

**(b)** Between-group Gini share. The subcategorization moderately
increases between-group share (+6.6 % for HDH), but cannot offset
the persistent within-group dominance.

**(c)** Top 10 hottest subcategories by HDH. LCZ 1E (extreme compact
high-rise canyon) tops the list at 4,466 °C·h. LCZ 1C, 1D, 1B—all
five subcategories of LCZ 1—appear in the top 4, indicating that
LCZ 1 is uniformly hot across its subdivisions.

**(d)** Subcategory population vs. mean HDH (log-x scale, colored by
LCZ class). Larger subcategories (e.g., LCZ 8A with 74,504 grids)
contain mid-range exposure; smaller specialized subcategories
(LCZ 1E with 2 grids) reach extreme values but affect tiny
populations.

**(e)** Within-LCZ HDH spread (max subcategory minus min) per LCZ
class. LCZ 3 (compact low-rise) shows the largest spread (Δ = 481
°C·h), followed by LCZ 10 (Δ = 348) and LCZ 2 (Δ = 270). Bar color
encodes spread magnitude. This identifies LCZ 3 and 10 as priority
intervention targets, not the high-rise CBD.

**(f)** Summary text box with key statistics: 151,896 OSM buildings
yielded 39 subcategories; HDH within-class Gini share dropped only
from 86.4 % (class) to 85.4 % (subcategory) — a -1.2 % change.

---

## Figure 5 (planned) — Multi-dimensional drivers beyond morphology

> Phase 4 deliverable. Will combine SHAP analysis on UTCI ~
> f(LCZ, UMPs, distance-to-coast, distance-to-mountain, hour-of-day,
> population density) to identify what drives the residual within-
> class inequality.

---

## Figure 6 (planned) — Topological signatures of LCZ subcategories

> Phase 4 deliverable. Persistent homology of UTCI fields at 100-m
> scale will produce a topological fingerprint per subcategory; we
> hypothesize that geometric structure (e.g., heat-island connectivity)
> distinguishes thermally-similar subcategories.

---

## Figure 7 (planned) — Symbolic regression of UTCI from UMPs

> Phase 4 deliverable. PySR-discovered closed-form expressions
> linking UMPs to UTCI, with Pareto front of accuracy vs. complexity.

---

## Figure 8 (planned) — Cross-city transferability

> Phase 5 deliverable. Test framework on Guangzhou and Hong Kong
> using the same workflow, demonstrating that the within-class
> dominance pattern generalizes beyond Shenzhen.
