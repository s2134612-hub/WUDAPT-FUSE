# WUDAPT-FUSE — Master Paper Draft

> 论文整合主稿。投稿前从此文件聚合 Methods + Results + 图表 + 摘要。
>
> 投稿目标: Nature Communications (IF 16.6)
> 备选: Building and Environment / Sustainable Cities and Society
>
> 起草时间: 2026-05-06
> 当前阶段: Phase 3 完成（OSM/UMPs + 39 亚类 + Gini 分解）

---

## 文档清单

```
docs/paper/
├── MASTER_DRAFT.md          ← 本文件（聚合稿）
├── 00_key_numbers.md        ← 所有关键数字速查
├── 01_methods.md            ← Methods 章节（~1500 词）
├── 02_results.md            ← Results 章节（~2000 词）
├── 03_abstract_v2.md        ← 摘要 + Cover Letter
└── 04_figure_captions.md    ← 图说
```

---

## 目录结构（投稿时拆分）

### Title

**Within-class thermal inequality dominates urban heat exposure: an
empirical refutation of the morphology-driven LCZ subcategorization
hypothesis using a workstation-runnable framework**

### Abstract
*(见 03_abstract_v2.md, 200 词)*

### 1. Introduction
*(待写, ~800 词)*

要点:
- 城市化与极端热浪 → SDG 11
- LCZ 框架进展（Stewart-Oke 2012, Demuzere 2022）
- 亚类化趋势（Huang 2026, Liu 2026 = 26 亚类）
- 不平等研究（Zhengzhou Sci Rep, Qingdao SCS）
- **Gap**: 形态学亚类化能否真的解释类内不平等？无大规模实证检验
- **Our contribution**: 首次通过 39 亚类 + 真实 UTCI 实证检验，发现 1.2% 残余 → 反驳

### 2. Methods
*(见 01_methods.md, ~1500 词)*

### 3. Results
*(见 02_results.md, ~2000 词)*

### 4. Discussion
*(待写, ~700 词)*

要点:
- 与已有研究比较（Huang 2026 假设的反驳）
- 三个解释（coarse-scale dominance, population masking, form-class incompleteness）
- 政策启示（LCZ 3, 10 优先干预）
- WUDAPT-FUSE 后续路线（FNO 神经下采样, TDA, PySR, CCM）
- 局限性（单城单月, ERA5 25km 分辨率瓶颈）

### 5. Methods (full version)
*(从 01_methods.md 整合)*

### Data and Code Availability
*(从 01_methods.md §2.8)*

### References
*(整合 ~50 篇)*

### Supplementary

#### Supplementary Methods
- LCZ proxy comparison (Path C)
- 1-week vs 1-month robustness
- Atkinson index sensitivity

#### Supplementary Figures
- LCZ-AT proxy results (前面 fig01)
- Hourly time series for selected LCZ subcategories
- UMPs maps (BSF, MBH, SVF)

#### Supplementary Tables
- Full 39-subcategory table with all UMPs
- Per-LCZ Gini decomposition

---

## 待补充内容（优先级排序）

### 🔴 必需（投稿前）

1. **Introduction 章节** (~800 词)
   - 撰写一段简洁有力的"问题动机 + 文献综述 + 我们的贡献"
   - 强调反驳形态学亚类化的 narrative

2. **Discussion 章节** (~700 词)
   - 限制 + 未来工作 + 政策意义

3. **Figure 1 概念图**
   - 重新设计：4 阶段流程图 + 深圳地图 + 人口图

4. **完整 References（~50 篇）**
   - 当前已有 ~10 篇，需补 LCZ、不平等、UTCI、机器学习等领域综述

### 🟡 增强（如时间允许）

5. **Phase 4: TDA 分析**
   - 持续同调 + Mapper 算法
   - 构成 Figure 5

6. **Phase 4: PySR 符号回归**
   - 自动发现 UTCI ~ UMPs 表达式
   - 构成 Figure 6

7. **Phase 4: 因果分析（CCM）**
   - 测试形态-暴露的非线性因果
   - 构成 Figure 7

8. **跨城市测试**
   - 在广州或东莞重做分析
   - 构成 Figure 8

### 🟢 可选（投顶刊加分项）

9. **FNO 神经下采样实验**
   - 学习 100m UTCI 直接而非 25km + 偏差
   - 验证亚类间真实差异是否因下采样而被压缩

10. **多维 SHAP 分析**
    - UTCI ~ f(LCZ, UMPs, lat, lon, hour, pop)
    - 揭示真正驱动因素

---

## Author contributions（拟定）

- **PI**: Conceptualization, Funding, Writing
- **Lead Author (you)**: Methodology, Software, Analysis, Writing
- **Co-authors**: Data curation (建议联系深圳大学 / 中山大学 同行)

---

## 投稿时间表

```
2026-05-07 ~ 06-15:  完善 Methods + Results + Discussion
2026-06-15 ~ 07-15:  Phase 4 (TDA + PySR)
2026-07-15 ~ 08-15:  Phase 5 (跨城市测试)
2026-08-15 ~ 09-15:  论文打磨 + 内审
2026-09-15:          投稿 Nature Communications
```

---

## 编辑反馈预演（自检）

Q: "Why is Shenzhen the right testbed?"
A: Subtropical megacity, 17.6 M residents, well-defined urban-natural
   gradient (south-north), high-quality OSM coverage (151k buildings),
   reference paper exists (Huang et al. 2026).

Q: "Why is 1.2 % within-Gini reduction meaningful?"
A: It refutes a strong implicit hypothesis in current LCZ literature
   that has driven 26-39 subcategory schemes globally. Without this
   empirical test, refinement schemes proliferate without rigorous
   validation.

Q: "How do you know your UMPs are accurate?"
A: 151,896 OSM buildings + height inference yield LCZ-class mean
   BSF/MBH consistent with literature ranges (Stewart-Oke 2012). LCZ
   1: BSF=0.20, MBH=44m vs literature 0.4-0.6, 25-100m. Slight
   under-estimation of BSF reflects OSM coverage incompleteness for
   informal buildings, but does not affect inequality decomposition
   conclusions.

Q: "Is 25-km ERA5 too coarse?"
A: Yes—and this is part of the finding. The 25-km ceiling limits
   how much heterogeneity our deviation injection can encode. Phase
   4's FNO-based downscaling will lift this constraint. Even at
   current resolution, the within-class >> between-class pattern is
   robust.

Q: "Can subcategorization ever close the gap?"
A: Not with morphology alone, per our results. Closing the gap
   requires multi-dimensional features (location, time, climate
   context). This motivates the broader WUDAPT-FUSE framework.

---

## 论文级 narrative 一句话

> "We empirically test whether morphology-driven LCZ subcategorization
> explains within-class urban thermal inequality, find it accounts for
> only 1.2% of the within-class Gini, and conclude that **multi-
> dimensional analytical frameworks—not finer morphological
> partitioning—are needed to close the inequality explanation gap**."

---

## 当前完成度

```
Phase 0: 项目初始化     ✅ 100%
Phase 1: 数据采集对齐    ✅ 100%
Phase 2: UTCI 数据集     ✅ 100% (1 周 + 1 月)
Phase 3: UMPs + 亚类     ✅ 100% (39 个)
Phase 4: TDA + PySR + CCM  ⏳ 0%
Phase 5: 跨城市测试       ⏳ 0%
Phase 6: 论文写作         🔄 30% (Methods + Results 草稿完成)
Phase 7: 投稿             ⏳ 0%
```

整体进度: **约 60%** （主要数据分析 + 核心实证发现完成）
