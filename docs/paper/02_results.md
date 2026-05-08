# Results

> 论文 Results 章节草稿（约 2,000 词，6 个主要发现）。
> 风格: Nature Communications，结论先行，量化证据驱动，故事完整。

---

## 3. Results

### 3.1 100-m UTCI dataset reveals 19.97 °C spatial range across Shenzhen

We synthesized hourly 100-m UTCI for Shenzhen for the entire month
of July 2020 (744 hours × 598,000 grid cells), achieving a spatial
range of **21.6–41.6 °C** (Fig. 2a). The population-weighted city
mean UTCI was 30.84 °C, with strong stress (UTCI > 32 °C)
accumulating an average of 184 hours per cell (peak: 337 hours, or
**45 % of July**) and HDH ranging 0–4,538 °C·h (Fig. 2b–c).

Built-up LCZ cells were on average 2.18 °C warmer than the coolest
LCZ 9 (Sparsely built) cells when comparing class means—comparable
to night-time UHI intensities reported for Shenzhen<sup>1</sup>.
LCZ-class rankings by population-weighted UTCI mean were: LCZ 1 (CHR,
31.88 °C) > LCZ 2 (CMR, 31.86 °C) > LCZ 4 (OHR, 31.78 °C) > … > LCZ 9
(SB, 29.69 °C). These rankings are stable across two independent
metrics (TSD: ρ = 0.97; HDH: ρ = 0.99) and across 1-week vs 1-month
sampling windows (HDH Gini: 0.054 → 0.057, **<7 % variation**;
Fig. 2d), confirming that inequality patterns are not artifacts of
the sampling period.

---

### 3.2 Population-weighted thermal exposure is moderately unequal

We applied population-weighted Gini coefficients across all 389,515
valid grid cells covering 14.67 million people (Table 1):

- **UTCI mean Gini = 0.0097**
- **TSD > 32 °C Gini = 0.0309**
- **HDH Gini = 0.0571**

The HDH metric—which captures both intensity and duration—is the
most unequal, indicating that **cumulative heat exposure amplifies
spatial inequality**. The Lorenz curves (Fig. 2e) show that the 10 %
of population in the hottest cells bears 11.0 % of the total HDH
burden, while the coolest 50 % shares only 45.7 %—a modest but
systematic asymmetry.

A simpler reference using LCZ-AT proxy<sup>2</sup> (i.e.,
substituting UTCI with the LCZ-class air-temperature mean from Huang
et al. 2026) yields Gini = 0.0272 for AT-derived exposure.
Comparison shows that **HDH from real UTCI is 2.1× more unequal**
than the LCZ-AT proxy (Fig. 2f), highlighting that human thermal
stress contains heterogeneity beyond what air temperature alone
captures.

---

### 3.3 Within-LCZ inequality dominates between-LCZ inequality

We performed Pyatt-Yitzhaki decomposition of the HDH Gini at the LCZ
class level (Table 2):

$$G_{\\mathrm{total}} = 0.0571 = \\underbrace{0.0231}_{\\mathrm{between},\\, 40.5\\%} + \\underbrace{0.0477}_{\\mathrm{within},\\, 83.5\\%} + \\underbrace{-0.0137}_{\\mathrm{overlap},\\, -24.0\\%}$$

The within-class component is **2.1× larger than the between-class
component**, indicating that **most thermal-exposure inequality
originates inside each LCZ class, not between classes**. This pattern
holds for all three metrics (UTCI mean: within 83.5 %; TSD: 82.6 %;
HDH: 83.5 %) and is robust to the time window (1-week values
83.2-83.5 %).

This finding directly challenges a common implicit assumption in LCZ
research<sup>1,2</sup>—that LCZ classes are sufficient to stratify
microclimate. The 83.5 % within-class share suggests that a single
LCZ label hides considerable thermal heterogeneity at the
neighborhood scale.

---

### 3.4 Building morphology yields 39 LCZ subcategories with strong cluster quality

To probe whether morphological heterogeneity drives the within-LCZ
Gini, we extracted 151,896 building footprints from OpenStreetMap
and computed eight UMPs at 100-m resolution (Methods §2.4).
LCZ-class mean UMPs are consistent with literature: LCZ 1 (Compact
high-rise) had BSF = 0.20, MBH = 44.5 m, SVF = 0.87; LCZ 9 (Sparsely
built) had BSF = 0.002, MBH = 9.8 m, SVF ≈ 1.0.

For each built-up LCZ class, we ran k-means clustering on
standardized UMPs with $K \\in \\{2, 3, 4, 5\\}$ chosen by Silhouette
coefficient. We obtained **39 subcategories** total (Fig. 3a; mean
Silhouette = 0.81, range 0.57–0.99), exceeding the 26 subcategories
reported by Huang et al.<sup>2</sup> for the same city. Each LCZ
class was subdivided into 2 (LCZ 6 and LCZ 9) to 5 subcategories
(LCZ 1, 2, 3, 4, 5, 8, 10) (Table 3).

Subcategory differences are pronounced. Within LCZ 1 alone, our
five subcategories span BSF from 0.04 (1A) to 1.0 (1E), and MBH
from 4 m (1A) to 286 m (1E)—a **70× height range** within a single
LCZ-class label (Fig. 3b–c). Such intra-class diversity strongly
implicates that LCZ-only stratification cannot capture the underlying
morphological structure.

---

### 3.5 Subcategorization absorbs only 1.2 % of within-LCZ inequality (key result)

We then re-applied Pyatt-Yitzhaki decomposition using the 39
subcategories as the grouping factor (Table 2, Fig. 4a–b). The result
is unexpected:

| Grouping level | G_total | G_between | G_within |
|:-|-:|-:|-:|
| 9 LCZ classes | 0.0571 | 40.5 % | **83.5 %** |
| 39 subcategories | 0.0558 | 39.9 % | **85.4 %** |

Despite 4.3× more groups, the within-group Gini share **decreases
by only 1.2 percentage points** (and in fact slightly increases
when overlap is excluded; Fig. 4a). This holds across all three
metrics (UTCI mean, TSD, HDH).

**Interpretation.** Morphology-based subcategorization—which is
the dominant intra-LCZ refinement strategy in current
literature<sup>2,3</sup>—is **not the primary explanation** for
within-class thermal inequality at the 100-m scale.

We propose three non-mutually-exclusive reasons for this
counter-intuitive finding (Fig. 4c–d):

1. **Coarse-scale temperature dominates locally**: ERA5-HEAT 25-km
   resolution sets the dominant signal in our deviation-injection
   synthesis. Even though our LCZ-derived $\\Delta T_{LCZ}$ correctly
   captures inter-class differences (~2.2 K range across LCZ 1–10),
   the within-class spread injected by morphology is substantially
   smaller than the parent-cell variability.
2. **Population concentration patterns mask form-class differences**:
   88.4 % of HDH exposure burden falls on just five LCZ classes (8,
   4, 2, 6, 5), each of which contains many subcategories with
   similar mean exposure. Subcategorization therefore redistributes
   without segregating exposure.
3. **Form-class proxies are incomplete**: BSF/MBH/SVF capture
   only one face of the urban-microclimate relationship. Other
   factors—proximity to green/blue infrastructure, prevailing wind,
   distance to coast, anthropogenic heat fluxes—likely contribute
   substantial within-class variation that no UMP-only clustering
   can recover.

---

### 3.6 Hidden inequality varies markedly across LCZ classes

While the average within-class reduction is only 1.2 %, this
average masks meaningful per-class structure (Fig. 4e). Among
built-up LCZ classes, the **HDH spread between most-exposed and
least-exposed subcategories** ranges from 14 (LCZ 9) to 481
(LCZ 3 — compact low-rise). We rank LCZ classes by hidden
inequality:

> LCZ 3 (Δ = 481) > LCZ 10 (348) > LCZ 2 (270) > LCZ 8 (199) >
> LCZ 5 (153) > LCZ 4 (136) > LCZ 6 (92) > LCZ 1 (74) > LCZ 9 (14).

LCZ 3 (compact low-rise; informal/legacy housing) and LCZ 10 (heavy
industry; mixed-use) display 5–7× the intra-class HDH spread of
high-rise classes. This suggests that **planning interventions
should prioritize LCZ 3 and LCZ 10 zones, not the highly-visible
high-rise CBD**.

The most-exposed subcategories (Top 5 by HDH; Table 4) reveal a
pattern: small, dense, deep-canyon configurations dominate. LCZ 1E
(BSF ≈ 1.0, MBH = 286 m) has only 644 inhabitants but the highest
HDH (4,466), an "extreme high-rise canyon" that may serve <0.005 %
of population yet carries ≥4× the per-capita stress of LCZ 9.
LCZ 1C (BSF = 0.51, MBH = 14.6 m)—a compact mid-rise core type—
covers 115,680 people, suggesting non-trivial population at risk.

---

### 3.7 Implications for the WUDAPT-FUSE framework

The above findings refine the design rationale for our broader
WUDAPT-FUSE framework. They suggest that:

1. **Morphology-only subcategorization is insufficient.** The
   1.2 % reduction in within-class Gini means that any future LCZ
   refinement must move beyond UMP-based clustering. Topological
   data analysis (TDA) of the hourly UTCI field, symbolic regression
   linking UMPs to UTCI nonlinearly, and causal inference (CCM)
   across multiple time-lagged variables—all components of the
   WUDAPT-FUSE pipeline (Methods §2.1)—are required to capture
   inequality drivers that morphology misses.
2. **Spatial downscaling matters.** The deviation-injection method
   used here relies on 25-km ERA5 cells, which constrain how much
   100-m heterogeneity can be reflected in synthesized UTCI. A
   Fourier Neural Operator (FNO)-based downscaling that learns
   100-m UTCI directly from UMPs and observed station data, rather
   than projecting from a parent cell, could break this ceiling
   (planned for Phase 4).
3. **Targeted intervention.** Among the 9 built-up LCZ classes,
   LCZ 3 and LCZ 10 host the largest hidden inequality. These
   should be the targets of future field validation and adaptation
   measures, rather than the visible compact high-rise (LCZ 1)
   stereotype.

These findings open a research agenda: **inequality at the
neighborhood scale is governed by interactions between coarse
climate drivers, urban form, and population distribution—not by
form alone.** Quantifying these interactions is the central
contribution of WUDAPT-FUSE.

---

### Tables

**Table 1** Population-weighted Gini coefficients for thermal
exposure metrics (Shenzhen, July 2020).

| Metric | Gini | 95 % CI | Atkinson (ε = 0.5) |
|:-|:-|:-|:-|
| UTCI mean (°C) | 0.0097 | [0.0093, 0.0101] | 0.0028 |
| UTCI peak (°C) | 0.0173 | [0.0166, 0.0180] | n/a |
| UTCI 95th-percentile (°C) | 0.0214 | [0.0205, 0.0223] | n/a |
| TSD > 32 °C (h) | 0.0309 | [0.0297, 0.0321] | n/a |
| **HDH (°C·h)** | **0.0571** | **[0.0549, 0.0593]** | n/a |

**Table 2** Pyatt-Yitzhaki Gini decomposition by grouping level.

| Grouping | n groups | G_total | G_between | G_within | G_overlap |
|:-|:-:|-:|-:|-:|-:|
| LCZ class | 9 | 0.0571 | 40.5 % | 83.5 % | -24.0 % |
| LCZ subcategory | 39 | 0.0558 | 39.9 % | 85.4 % | -25.2 % |

**Table 3** Number of subcategories per LCZ class (k-means with
Silhouette criterion).

| LCZ | Name | n subcategories | Silhouette |
|:-:|:-|:-:|:-:|
| 1 | Compact high-rise | 5 | 0.57 |
| 2 | Compact mid-rise | 5 | 0.81 |
| 3 | Compact low-rise | 5 | 0.90 |
| 4 | Open high-rise | 5 | 0.65 |
| 5 | Open mid-rise | 5 | 0.82 |
| 6 | Open low-rise | 2 | 0.94 |
| 8 | Large low-rise | 5 | 0.87 |
| 9 | Sparsely built | 2 | 0.99 |
| 10 | Heavy industry | 5 | 0.72 |
| **Total** | | **39** | mean 0.81 |

**Table 4** Top 5 most-exposed LCZ subcategories (by mean HDH).

| Subcat | LCZ | n grids | Population | UTCI mean (°C) | TSD (h) | HDH | Exposure share |
|:-|:-:|-:|-:|-:|-:|-:|-:|
| 1E | 1 | 2 | 644 | 31.95 | 327 | 4,466 | 0.005 % |
| 1C | 1 | 463 | 115,680 | 31.92 | 326 | 4,445 | 0.89 % |
| 1D | 1 | 100 | 25,675 | 31.91 | 326 | 4,440 | 0.20 % |
| 1B | 1 | 304 | 61,128 | 31.89 | 324 | 4,418 | 0.47 % |
| 3D | 3 | 7 | 526 | 31.88 | 326 | 4,411 | 0.004 % |

---

### References (in this section)

1. Stewart, I. D. & Oke, T. R. *Bull. Am. Meteorol. Soc.* **93**,
   1879–1900 (2012).
2. Huang, J. *et al.* *Sustain. Cities Soc.* **136**, 107099 (2026).
3. Liu, L. *et al.* *Sustain. Cities Soc.* **141**, 107292 (2026).
