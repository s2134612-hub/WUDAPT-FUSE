# 论文大纲：WUDAPT-FUSE

**目标期刊**: Nature Communications（IF 16.6）
**字数**: 约 5,000 词正文 + 50 个参考文献 + 7 张主图

---

## 标题（候选）

**主标题**:
> WUDAPT-FUSE: A workstation-runnable framework integrating multi-source fusion, neural downscaling, and topological-symbolic-causal analysis for urban thermal comfort discovery

**备选 1**:
> Discovering hidden urban thermal comfort patterns through multi-source neural fusion and topological-symbolic-causal analysis

**备选 2**:
> Beyond black-box prediction: a workstation-runnable framework for interpretable urban microclimate science

---

## 摘要结构（约 200 词）

```
[Background, 30 词]
Urban microclimate prediction at fine spatial scales has relied on
computationally expensive numerical weather models (e.g., WRF), limiting
accessibility for routine research and policy applications.

[Gap, 40 词]
Existing machine-learning post-processing approaches improve speed but
remain black-box, fail to reveal physical equations governing thermal
environments, and cannot establish causal relationships between urban
morphology and microclimate—severely limiting their scientific value.

[Method, 50 词]
We present WUDAPT-FUSE, a workstation-runnable framework that (i) replaces
WRF with multi-source data fusion using ERA5, satellite LST, and weather
stations; (ii) trains a Fourier Neural Operator with physics-informed
constraints to downscale UTCI to 100m; and (iii) applies topological,
symbolic, and causal analyses to discover hidden patterns.

[Results, 50 词]
Applied to Shenzhen (2020), the framework achieved RMSE = 0.71 K (LOOCV)
using <500 CPU·hr, comparable to WRF-ML at 1/100 the cost. Topological
analysis revealed three previously unrecognized LCZ subcategories with
distinct thermal "fingerprints"; symbolic regression discovered four
governing equations; causal inference identified non-linear pathways
not captured by SHAP.

[Significance, 30 词]
WUDAPT-FUSE establishes a paradigm shift from black-box prediction to
interpretable scientific discovery in urban climate research, accessible
to any researcher with a workstation.
```

---

## 章节结构

### 1. Introduction（约 800 词）

#### 1.1 段落 1: 城市微气候研究的紧迫性
- 全球城市化、UHI、人体健康、SDG 11
- 引用 IPCC AR6, Lancet Countdown 2026

#### 1.2 段落 2: 现有方法两难
- WRF: 物理可信但算力极高（引用文章一）
- 纯 ML: 速度快但黑箱（引用 GSM-UTCI 等）
- LCZ 框架: 描述性强但缺机制
- **Gap**: 缺一个工作站可跑、物理一致、可解释、能因果推断的统一框架

#### 1.3 段落 3: 本文贡献（4 点）
1. **方法学**: 首次将 WRF 重物理替换为多源融合 + FNO，算力降低 100×
2. **认知**: 引入 TDA 揭示 k-means 看不到的拓扑差异
3. **可解释性**: 用 PySR 自动发现城市气候解析方程
4. **因果性**: 用 CCM 量化非线性因果效应

#### 1.4 段落 4: 论文组织
- "We organize this paper as follows..."

---

### 2. Methods（约 1,200 词）

#### 2.1 数据
- 9 类多源数据
- 时空对齐至 100m × 1h × 全年（2020）
- 详见 `docs/03_data_sources.md`

#### 2.2 多源融合架构（Layer 1）
- ERA5/HiTiSEA 提供大尺度先验
- Landsat LST 提供细粒度锚点
- MMS 站点提供训练标签
- 详见 `docs/02_methodology.md`

#### 2.3 物理约束神经下采样（Layer 2）
- Fourier Neural Operator 架构
- LCZ-aware attention
- 物理约束损失（UTCI 公式 + 能量平衡 + 空间梯度）
- 训练: PyTorch Lightning + WandB

#### 2.4 拓扑数据分析（Layer 3a）
- Cubical Complex 持续同调
- Persistence Diagram → 拓扑指纹向量
- Bottleneck/Wasserstein 距离

#### 2.5 符号回归（Layer 3b）
- PySR 进化搜索
- 物理量纲约束
- 多目标 Pareto 前沿

#### 2.6 因果推断（Layer 3c）
- Convergent Cross Mapping (CCM)
- 双重机器学习 (DML)
- 反事实推断

#### 2.7 验证
- LOOCV 站点交叉验证
- 时序外推（2021）
- 与文章一 XGBoost 基线对比

---

### 3. Results（约 2,000 词）

#### 3.1 模型精度（Fig 1）
- LOOCV RMSE 跨季节
- 与文章一 WRF-ML 对比表
- 物理一致性（能量平衡残差）

#### 3.2 100m UTCI 数据集（Fig 2）
- 深圳全域 4 季空间分布图
- 时序特征（热浪日 vs 平常日）

#### 3.3 拓扑指纹发现（Fig 3）
- 26 个 LCZ 亚类的 persistence diagram
- 拓扑距离矩阵聚类（Mapper）
- **关键发现**: 揭示 k-means 无法识别的 3 个新亚类

#### 3.4 符号方程发现（Fig 4）
- 帕累托前沿（精度 vs 复杂度）
- Top-3 解析方程
- 与 XGBoost 精度对比（差距 < 5%）
- **关键发现**: 自动发现 SVF·BV 协同项

#### 3.5 因果路径（Fig 5）
- CCM 因果强度 vs SHAP 相关性对比
- 反事实推断: 干预 SVF +0.1 的 ΔUTCI 期望
- **关键发现**: BSF → UTCI 的非线性因果被 SHAP 严重低估

#### 3.6 应用：热不平等分析（Fig 6）
- 三层 Gini 分解
- 5 类脆弱人群 × 3 暴露指标
- LISA 空间聚类
- 沿海 vs 山区对比

#### 3.7 跨城市迁移（Fig 7）
- 深圳模型 → 广州/东莞/佛山
- 迁移精度
- 通用性论证

---

### 4. Discussion（约 800 词）

#### 4.1 与已有研究比较
- 文章一 (Huang et al. 2026): 同类型 + 关键改进
- Zhengzhou 不平等论文: 拓扑维度新增
- GSM-UTCI: 可解释性新增

#### 4.2 方法学意义
- AI4Science 范式在城市气候的首次完整应用
- 工作站可复现性的科学价值

#### 4.3 政策启示
- 干预 SVF 优于 BSF
- 沿海 LCZ 1B 需优先改造
- 等等

#### 4.4 局限
- 单年单城市
- MRT 简化模型
- TDA 计算瓶颈

#### 4.5 未来工作
- 多年扩展
- 极端天气场景
- 真实干预后验证

---

### 5. 数据与代码可用性

```
代码: github.com/[username]/WUDAPT-FUSE （MIT License）
数据: Zenodo DOI: [待获取]
   - 100m UTCI 全年 (Shenzhen, 2020)
   - 26 个 LCZ 亚类拓扑指纹
   - 模型 checkpoint
```

---

### 6. 参考文献（约 50 篇）

#### 必引论文
1. Huang et al. 2026 (文章一) - 直接对照
2. Liu et al. 2026 (文章二) - UBGS 优化
3. Stewart & Oke 2012 - LCZ 经典
4. Cranmer 2023 - PySR
5. Sugihara et al. 2012 - CCM Science
6. Bröde et al. 2012 - UTCI 公式
7. Demuzere et al. 2022 - LCZ 全球地图
8. Di Napoli et al. 2021 - ERA5-HEAT
9. Yan et al. 2021 - HiTiSEA
10. Zhengzhou 不平等 (Sci Rep 2025)
... [完整列表见 docs/references.md]

---

## 主图设计（7 张主图）

| 图 | 内容 | 类型 | 关键信息 |
|----|------|------|---------|
| Fig 1 | 框架总览 | 流程图 | 5 层架构一览 |
| Fig 2 | 100m UTCI | 4 季地图 | 空间分布主结果 |
| Fig 3 | TDA 指纹 | persistence diagram + 聚类 | 拓扑发现 |
| Fig 4 | 符号方程 | Pareto 前沿 + 公式列表 | 方程发现 |
| Fig 5 | 因果分析 | CCM vs SHAP 对比 | 因果发现 |
| Fig 6 | Gini 不平等 | Lorenz + LISA | 应用 |
| Fig 7 | 跨城迁移 | 散点 + 地图 | 通用性 |

---

## 投稿前 Checklist

- [ ] 摘要 < 200 词
- [ ] 正文 < 5,500 词
- [ ] 7 张主图（每张 < 2 版面）
- [ ] 50 个参考文献
- [ ] 数据/代码 GitHub 仓库
- [ ] Cover Letter（强调创新点）
- [ ] Highlights（5 条）
- [ ] 推荐 4-5 位审稿人

---

## 推荐审稿人候选

1. Matthias Demuzere (Ruhr-Universität Bochum) - LCZ 权威
2. Lutz Katzschner (Kassel University) - 城市气候
3. Manabu Kanda (Tokyo Tech) - 城市边界层
4. Nektarios Chrysoulakis (FORTH) - 城市遥感
5. Dev Niyogi (UT Austin) - 城市气象 ML

---

**最后更新**: 2026-05-06
