# Introduction 章节草稿

> 约 800 词，分 4 段。
> 风格: Nature Communications，问题驱动、实证导向。

---

## 1. Introduction

### 段落 1: 城市热浪问题

Urban populations are increasingly exposed to extreme heat events,
which have caused over 489,000 deaths annually worldwide between
2000 and 2019<sup>1</sup>. The interaction between urban morphology,
local climate, and population vulnerability creates spatially
heterogeneous heat exposure that deepens environmental injustice in
megacities<sup>2,3</sup>. Quantifying who is exposed, by how much,
and where, is essential to design adaptation policies under the UN
Sustainable Development Goal 11<sup>4</sup>. The Local Climate
Zone (LCZ) framework introduced by Stewart and Oke<sup>5</sup>
provides a globally consistent classification of 17 surface types
that has become the dominant tool for urban-climate stratification,
with global 100-m maps now available<sup>6</sup> and applied across
hundreds of cities to quantify urban heat island effects, building
energy demand, and thermal comfort<sup>7-9</sup>.

### 段落 2: LCZ 亚类化趋势与 Gap

Despite this progress, increasing evidence indicates that the 17
LCZ classes hide substantial within-class heterogeneity at the
neighborhood scale. Buildings within a single LCZ-class label can
vary by an order of magnitude in height, density, and material
composition<sup>10,11</sup>. To address this, recent papers have
introduced *intra-LCZ subcategorization*—using k-means or similar
clustering on urban morphological parameters (UMPs) to derive 2-5
subcategories per LCZ class<sup>12,13</sup>. Huang et al. (2026)
proposed 26 subcategories for Shenzhen, while Liu et al. (2026)
embedded similar refinement in their Guangzhou multi-objective
optimization framework. The implicit hypothesis is that
**morphology-based subcategorization can absorb within-class
microclimate heterogeneity**, justifying its widespread use. To our
knowledge, **this hypothesis has never been rigorously tested**
through population-weighted inequality analysis at large scale.

Concurrently, environmental-justice studies have demonstrated that
heat exposure inequality follows characteristic Gini-like
distributions across LCZ classes<sup>14,15</sup>. Recent work in
Zhengzhou (2025) found inter-LCZ Gini = 0.499 for thermal exposure,
and Qingdao (2025) reported similar patterns. Yet these studies
stop at the LCZ-class level and do not decompose between-class vs.
within-class inequality. As a result, the relative importance of
morphological refinement vs. other drivers (population
distribution, large-scale climate, social vulnerability) remains
unquantified.

### 段落 3: 我们的贡献

Here we present **WUDAPT-FUSE**, a workstation-runnable analytical
framework, and apply it to test the morphology-driven
subcategorization hypothesis in Shenzhen, China (14.67 million
residents, July 2020). We make four contributions:

1. **Methodological**: We synthesize hourly 100-m UTCI for an
   entire month (744 hours × 598,000 grid cells) by combining
   ERA5-HEAT 25-km reanalysis with LCZ-derived class-mean
   anomalies via deviation injection. The full pipeline runs in
   <5 minutes on a single RTX 3060 GPU, democratizing high-
   resolution urban-climate analysis beyond super-computing
   centers.

2. **Empirical (key finding)**: Using 151,896 OpenStreetMap building
   footprints, we derive 39 LCZ subcategories—1.5× more refined
   than Huang et al. (2026)—through k-means clustering on eight
   UMPs (mean Silhouette = 0.81). We then apply Pyatt-Yitzhaki
   Gini decomposition to test whether these morphology-driven
   subcategories absorb within-class thermal inequality. They do
   not: **only 1.2 % of the 83.5 % within-class Gini share is
   explained**, refuting the morphology hypothesis at scale.

3. **Theoretical**: We propose three non-mutually-exclusive
   explanations—coarse-scale climate dominance, population
   concentration patterns, and form-class proxy incompleteness—and
   show that LCZ 3 (compact low-rise) and LCZ 10 (heavy industry),
   not the visible high-rise CBD, host the largest hidden
   inequality (HDH spread = 481 vs. 74 in LCZ 1). This redirects
   adaptation priorities away from the stereotype.

4. **Practical**: All code, processed datasets, and a Docker image
   are released under MIT license at GitHub, enabling other
   researchers to reproduce and extend the analysis to their cities.

### 段落 4: 论文结构

We describe data sources and the deviation-injection synthesis in
Methods. Results section presents the 100-m UTCI dataset, baseline
inequality patterns, the 83.5 % within-class Gini share, the 39-
subcategory refinement, the central negative result on within-class
absorption, and the implications for LCZ-class-specific intervention
priorities. Discussion section reviews the findings against current
literature, examines methodological limitations, and outlines the
broader WUDAPT-FUSE research agenda combining topological,
symbolic, and causal analyses to ultimately close the inequality
explanation gap.

---

### References (Introduction 引用 ~15 篇，最终整合到主参考文献)

1. WHO. Heat and health (2024).
2. Hsu, A. *et al.* *Nat. Commun.* **12**, 2721 (2021).
3. Mitchell, B. C. & Chakraborty, J. *Environ. Health Perspect.*
   **126**, 097004 (2018).
4. UN. Sustainable Development Goal 11 (2015).
5. Stewart, I. D. & Oke, T. R. *Bull. Am. Meteorol. Soc.* **93**,
   1879–1900 (2012).
6. Demuzere, M. *et al.* *Earth Syst. Sci. Data* **14**, 3835–3873
   (2022).
7. Bechtel, B. *et al.* *Urban Clim.* **28**, 100431 (2019).
8. Yang, X. *et al.* *Build. Environ.* **183**, 107069 (2020).
9. Cai, M. *et al.* *Build. Environ.* **142**, 134-149 (2018).
10. Du, J. *et al.* *Urban Clim.* **47**, 101391 (2023).
11. Fung, K. *et al.* *Build. Environ.* **214**, 108908 (2022).
12. Huang, J. *et al.* *Sustain. Cities Soc.* **136**, 107099 (2026).
13. Liu, L. *et al.* *Sustain. Cities Soc.* **141**, 107292 (2026).
14. Zhengzhou et al. *Sci. Rep.* (2025).
15. Qingdao et al. *Sustain. Cities Soc.* (2025).
