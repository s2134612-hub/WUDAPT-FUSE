# Discussion 章节草稿

> 约 700 词，分 5 段。
> 风格: Nature Communications，洞察驱动、未来导向。

---

## 4. Discussion

### 段落 1: 主要发现摘要

Our analysis of 14.67 million Shenzhen residents over July 2020
reveals two complementary findings on urban thermal inequality.
First, the population-weighted Gini for heat-degree hours reaches
0.057, with **83.5 % of total inequality residing within LCZ
classes**. Second, despite refining the 9 built-up LCZ classes
into 39 morphology-driven subcategories—exceeding the 26 reported
by Huang et al. for the same city<sup>1</sup>—**within-class Gini
decreases by only 1.2 percentage points**. This is a strong
empirical refutation of an implicit hypothesis pervasive in current
LCZ literature: that morphology-driven subcategorization is
sufficient to explain within-class microclimate variability.

### 段落 2: 解释为何形态学不足

We propose three non-exclusive explanations for the limited
explanatory power of morphology. **First**, our deviation-injection
synthesis is constrained by the 25-km resolution of ERA5-HEAT
reanalysis<sup>2</sup>. Within each parent ERA5 cell, the dominant
temporal signal varies on the order of several Kelvin between days,
overwhelming the ~2.2 K LCZ-class anomalies and the smaller within-
class variations introduced by morphological subcategorization. A
neural-operator-based downscaling that learns 100-m UTCI directly
from UMPs and station observations<sup>3</sup>—rather than
projecting from a parent cell—could lift this constraint and is the
target of Phase 4 of WUDAPT-FUSE. **Second**, 88.4 % of the city's
HDH burden falls on five LCZ classes (8, 4, 2, 6, 5) that contain
many subcategories with statistically similar mean exposure;
subcategorization redistributes but does not segregate the
exposure. **Third**, urban thermal inequality is governed by
factors beyond building form: green-blue infrastructure proximity,
prevailing wind patterns, distance to coast/mountains, and
anthropogenic heat fluxes<sup>4-6</sup>. None of these can be
recovered by UMP-only clustering.

### 段落 3: 政策意义

The findings reframe adaptation priorities. The most-exposed
subcategories are not concentrated in the visible compact high-rise
CBD (LCZ 1: HDH spread = 74); rather, they are scattered across
LCZ 3 (compact low-rise; HDH spread = 481) and LCZ 10 (heavy
industry; HDH spread = 348). LCZ 3 hosts informal and legacy
housing where intervention costs are lower but population
vulnerability is higher; LCZ 10 represents mixed industrial-
residential zones where workers and families are exposed during
peak heat. Top-down policies focused on iconic high-rise zones
(such as the existing focus on greening the Futian CBD) miss
these communities. **Targeted "blue-green" infrastructure
investment<sup>7</sup> in LCZ 3 and 10—specifically, dispersed
small parks and reflective pavements—is likely to yield greater
per-capita benefit than centralized high-rise interventions**.

### 段落 4: 方法学限制

Several limitations should be acknowledged. (i) ERA5-HEAT 25-km
resolution limits the spatial detail that any synthesis method can
recover at 100-m scale. Our deviation-injection captures
inter-class but not intra-class heterogeneity. (ii) OSM building
data has incomplete height information (28.9 % of buildings) and
under-represents informal structures, especially in LCZ 3. We
imputed median height where missing, but this introduces
attenuation bias in our UMP estimates. (iii) The 100-m grid
inherits LCZ classification errors, which propagate to all
analyses. (iv) Our analysis is single-city and single-month; the
within-class dominance pattern may differ in other climates or
seasons. (v) Population data come from WorldPop, which estimates
nighttime distribution; daytime exposure for commuters and workers
differs. Future work should integrate dynamic population data from
mobile-phone signaling.

### 段落 5: 未来方向 — WUDAPT-FUSE 的下一步

These findings define the next research agenda for WUDAPT-FUSE.
First, **Fourier Neural Operator-based downscaling** will replace
the deviation-injection method, learning 100-m UTCI directly from
multi-source inputs and breaking the 25-km ERA5 ceiling. Second,
**topological data analysis (TDA)** of the 100-m UTCI fields,
using persistent homology of the urban heat-island connectivity
graph, may reveal geometric structure that morphology cannot
encode. Third, **symbolic regression** (PySR) can discover closed-
form expressions linking UMPs to UTCI nonlinearly, exposing
non-additive interactions. Fourth, **convergent cross-mapping**
(CCM) on time-lagged station data can identify causal drivers of
within-class inequality—wind, radiation, and anthropogenic
emissions—that current LCZ frameworks treat implicitly. Together,
these multi-dimensional analyses, applied first to Shenzhen and
extended to Guangzhou, Hong Kong, and other Greater Bay Area
megacities, will deliver a complete answer to the question this
paper opens: **what really drives urban thermal inequality at the
neighborhood scale?**

---

### References (Discussion 引用 ~15 篇，整合到主参考文献)

1. Huang, J. *et al.* *Sustain. Cities Soc.* **136**, 107099 (2026).
2. Di Napoli, C. *et al.* *Geosci. Data J.* **8**, 2-10 (2021).
3. Li, Z. *et al.* *Building Environ.* (2025).
4. Liu, L. *et al.* *Sustain. Cities Soc.* **141**, 107292 (2026).
5. Cai, M. *et al.* *Build. Environ.* **142**, 134-149 (2018).
6. Yang, X. *et al.* *Build. Environ.* **183**, 107069 (2020).
7. Norton, B. A. *et al.* *Landsc. Urban Plan.* **134**, 127-138
   (2015).
