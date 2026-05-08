# Abstract (v2 — reflecting actual findings)

> 200 词，按 Nature Comm 风格分四块。
> 与 docs/01_paper_outline.md 中的 v1 不同，本版反映真实实证发现。

---

## Working title (revised)

**Within-class thermal inequality dominates urban heat exposure: an
empirical refutation of the morphology-driven LCZ subcategorization
hypothesis using a workstation-runnable framework**

---

## Abstract (≈200 words)

**[Background]** Local Climate Zone (LCZ) frameworks are widely used
to map urban thermal heterogeneity, with recent studies advocating
intra-class subcategorization based on urban morphological parameters
(UMPs) to improve resolution. Whether morphology-driven
subcategorization can fully explain within-class thermal inequality
remains untested at large scale.

**[Methods]** We developed WUDAPT-FUSE, a workstation-runnable
framework integrating multi-source data (ERA5-HEAT 25-km UTCI,
Demuzere 100-m LCZ, WorldPop, OpenStreetMap), to synthesize hourly
100-m Universal Thermal Climate Index (UTCI) for Shenzhen, China
(July 2020, 14.67 M residents, 744 hours, 389,515 valid grid cells).
We computed eight UMPs from 151,896 OSM building footprints,
performed k-means clustering to derive 39 LCZ subcategories (mean
Silhouette = 0.81), and applied Pyatt-Yitzhaki Gini decomposition
under multiple grouping schemes.

**[Results]** Population-weighted Gini coefficients reach 0.057 for
heat-degree hours, with 83.5 % of inequality residing **within** LCZ
classes. Surprisingly, our 39-subcategory refinement absorbs only
1.2 % of this within-class share—refuting the hypothesis that
morphology-driven subcategorization closes the gap. LCZ 3 (compact
low-rise) shows the largest hidden inequality (HDH spread = 481).

**[Significance]** Within-class thermal inequality is governed by
factors beyond urban morphology, motivating a multi-dimensional
analytical framework that combines topological, symbolic, and causal
analyses—the WUDAPT-FUSE program. The full pipeline ran in <5 min on
a single RTX 3060 GPU, enabling reproducible deployment in any
research lab.

---

## Highlights (5 short bullets)

- We synthesized 100-m hourly UTCI for Shenzhen July 2020 using a
  fast deviation-injection method (744 h × 598,000 cells, <1 min).
- Population-weighted Gini = 0.057 (HDH); the most-stressed
  subcategory (LCZ 1E) accumulates 327 hours of strong heat stress
  in a single month.
- Within-LCZ-class inequality accounts for 83.5 % of total Gini—
  far exceeding between-class inequality (40.5 %).
- 39 OSM-UMP subcategories absorb only 1.2 % of within-class
  inequality, refuting the morphology-driven subcategorization
  hypothesis.
- Hidden inequality is concentrated in LCZ 3 and LCZ 10, suggesting
  these should be priority targets for adaptation, not the visible
  high-rise CBD.

---

## One-sentence summary

> "**Morphology cannot explain hidden thermal inequality at the
> neighborhood scale; multi-dimensional analysis is needed.**"

---

## Cover-letter pitch (for editor)

Dear Editor,

We submit our manuscript "Within-class thermal inequality dominates
urban heat exposure" for consideration at Nature Communications.

Recent advances in Local Climate Zone (LCZ) classification have
fueled enthusiasm for intra-class subcategorization to refine urban
microclimate analysis. We empirically test this approach using a
fully reproducible, workstation-runnable framework applied to
Shenzhen (14.67 M residents, July 2020, 744 hours).

Our central finding contrasts with prevailing assumptions: 39 OSM-
derived morphological subcategories—**1.5× more refined than the
state-of-the-art**—reduce within-class Gini by only 1.2 percentage
points. Within-class inequality (83.5 % of total) is therefore not
primarily driven by urban form; it must be governed by interactions
between coarse climate drivers, population distribution, and
non-morphological factors that current LCZ frameworks overlook.

This negative result reframes the research agenda: future work must
move beyond morphology-only refinement toward multi-dimensional
analysis (e.g., topological, symbolic, causal). Our finding has
direct policy implications—LCZ 3 (compact low-rise) and LCZ 10
(heavy industry), not the visible CBD, host the largest hidden
inequality and should be priority targets for adaptation.

The full pipeline runs in <5 min on a single RTX 3060 GPU,
democratizing high-resolution urban-climate research beyond
super-computing centers. All code, data, and the 39-subcategory
dataset are released under open licenses.

We believe this work will be of broad interest to the urban
climate, environmental justice, and computational geography
communities. We confirm this work is original and not under
consideration elsewhere.

[Sincerely, Authors]
