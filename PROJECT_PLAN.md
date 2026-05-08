# WUDAPT-FUSE 项目路线图

**目标**: 6 个月内完成 Nature Communications / Building and Environment 投稿

**起始日期**: 2026-05-06
**预计投稿日期**: 2026-11-06

---

## 总览：六阶段路线

```
Phase 0  项目初始化       Week 0 (本周)
Phase 1  数据采集与对齐   Month 1
Phase 2  神经下采样模型   Month 2
Phase 3  拓扑数据分析     Month 3
Phase 4  符号回归 + 因果  Month 4
Phase 5  Gini 不平等应用 Month 5
Phase 6  论文写作投稿    Month 6
```

---

## Phase 0: 项目初始化（Week 0，**当前阶段**）

### 目标
搭建可复现的开发环境，确认所有工具链可用。

### 任务清单
- [x] 创建项目目录结构
- [x] 编写 README 与项目计划
- [ ] 配置 Conda 环境（Python 3.11 + PyTorch + GUDHI + PySR）
- [ ] 验证 GPU 可用性
- [ ] 注册 ERA5 / Earth Engine / USGS 账号
- [ ] 下载第一批样本数据（Shenzhen, 2020-07）
- [ ] 跑通 hello-world Python 脚本

### 交付物
- `environment.yml` 完整依赖清单
- `setup_windows.ps1` 一键安装脚本
- `scripts/verify_install.py` 验证脚本
- `scripts/download_sample.py` 样本数据下载脚本

---

## Phase 1: 数据采集与对齐（Month 1）

### 目标
建成统一时空基准的多源数据集（深圳全域，2020 年）。

### 子任务

#### Week 1: 大尺度数据下载
- [ ] ERA5-HEAT UTCI 下载（25km × 1h，整个 2020 年）
- [ ] HiTiSEA UTCI 下载（10km × 日）
- [ ] ERA5 单变量数据（AT, RH, WS, MRT 组分，9km）

#### Week 2: 高分辨率遥感数据
- [ ] Landsat 8/9 LST（30m × 16 天，全年）
- [ ] MODIS LST（1km × 4×/天）
- [ ] Sentinel-2 反射率（10m × 5 天）
- [ ] VIIRS 夜间灯光（500m）

#### Week 3: 静态特征数据
- [ ] WUDAPT LCZ 地图（100m）
- [ ] DEM SRTM（30m）
- [ ] 建筑数据（OpenStreetMap + 高德 API）
- [ ] 计算 UMPs：BSF, MBH, SBH, MBW, SVF, PSF, BV, GFA, MSW, WSF

#### Week 4: 站点观测 + 数据对齐
- [ ] 116 MMS 站点数据获取（深圳气象网）
- [ ] 时空对齐：所有数据重采样到 100m × 1h 统一基准
- [ ] 数据 QC：缺失值填补、异常值检测
- [ ] ETL 管道：构建 xarray 多维数据集

### 交付物
- `data/processed/shenzhen_2020_unified.zarr`（约 30 GB）
- `notebooks/01_data_exploration.ipynb`
- `src/data_loaders/` 完整数据加载模块

---

## Phase 2: 神经下采样模型（Month 2）

### 目标
训练 Fourier Neural Operator 实现 9km → 100m UTCI 降尺度，RMSE < 0.8 K。

### 子任务

#### Week 5: 模型架构
- [ ] FNO 主干实现（基于 neuralop 库）
- [ ] LCZ-aware 注意力机制
- [ ] 物理约束损失头（UTCI 公式 + 能量平衡 + 空间平滑）
- [ ] 单元测试

#### Week 6: 训练管道
- [ ] PyTorch Lightning 训练器
- [ ] 数据增强（旋转、镜像）
- [ ] 学习率调度（OneCycle / Cosine）
- [ ] WandB 实验跟踪

#### Week 7: 调参 + 训练
- [ ] 网格搜索关键超参（hidden_channels, n_modes, n_layers）
- [ ] 全季节训练（4 周 × 4 季）
- [ ] 检查点保存

#### Week 8: 验证
- [ ] 留一站点交叉验证（LOOCV，116 折）
- [ ] 时序外推验证（2021 年）
- [ ] 物理一致性检查
- [ ] 与文章一 XGBoost 基线对比

### 交付物
- `src/models/wudapt_fuse.py` 完整模型
- `models/checkpoints/best_model.pth`
- `data/processed/utci_100m_full.nc`（深圳全域 UTCI）
- 验证报告 `results/validation_report.md`

---

## Phase 3: 拓扑数据分析（Month 3）

### 目标
计算 26 个 LCZ 亚类的"热场拓扑指纹"，发现 k-means 无法捕捉的几何差异。

### 子任务

#### Week 9: TDA 工具搭建
- [ ] GUDHI Cubical Complex 流程
- [ ] Persistence Diagram 计算
- [ ] Persistence Landscape / Image 提取

#### Week 10: 全市 TDA 计算
- [ ] 每个 LCZ 亚类的拓扑指纹（β₀, β₁, persistence entropy）
- [ ] 跨亚类拓扑距离矩阵（Wasserstein / Bottleneck）
- [ ] Mapper 算法揭示亚类间网络

#### Week 11: 统计推断
- [ ] PERMANOVA 检验亚类拓扑差异显著性
- [ ] 拓扑特征与 UMPs 的回归
- [ ] 与文章一 k-means 结果对比

#### Week 12: TDA 可视化
- [ ] Persistence Diagram 集合图
- [ ] 拓扑指纹热图（26 亚类）
- [ ] Mapper 网络图

### 交付物
- `src/analysis/tda.py`
- `notebooks/03_tda_analysis.ipynb`
- 4 张拓扑分析图（TDA Fig 1-4）

---

## Phase 4: 符号回归 + 因果推断（Month 4）

### 目标
- 用 PySR 自动发现 UTCI ~ f(UMPs) 解析方程
- 用 CCM/DML 推断"形态 → 微气候"的非线性因果效应

### 子任务

#### Week 13-14: 符号回归
- [ ] PySR 物理约束设置（量纲、单调性）
- [ ] 多目标搜索（精度 vs 复杂度，帕累托前沿）
- [ ] 发现的方程的物理解释
- [ ] 与 XGBoost 精度对比（应 R² 仅低 5-10%）

#### Week 15-16: 因果推断
- [ ] CCM 计算每个 UMP 对 UTCI 的非线性因果强度
- [ ] DML（双重机器学习）估计平均处理效应
- [ ] 反事实推断：If SVF +0.1, ΔUTCI = ?
- [ ] 与 SHAP 相关性结果对比

### 交付物
- `src/analysis/symbolic_regression.py`
- `src/analysis/causal_inference.py`
- 发现的 3-5 个候选方程
- 因果效应量化表

---

## Phase 5: Gini 不平等应用（Month 5）

### 目标
基于 100m UTCI 数据集，做 LCZ 亚类层级分层 Gini 分解。

### 子任务

#### Week 17: 人口数据准备
- [ ] WorldPop 100m 下载
- [ ] 七普街道级数据降尺度
- [ ] 5 类脆弱人群（老人、儿童、低收入、户外工作、流动人口）

#### Week 18: Gini 计算
- [ ] 实现 Pyatt-Yitzhaki 三层分解
- [ ] 多人群 × 多指标矩阵（5 × 3 = 15 个 Gini）
- [ ] Lorenz 曲线对比

#### Week 19: 空间统计
- [ ] LISA 局部聚类
- [ ] 局部 Gini 热点检测
- [ ] 沿海 vs 山区对比

#### Week 20: 整合分析
- [ ] 串联 TDA / PySR / CCM 结果讲故事
- [ ] 政策启示提炼

### 交付物
- `src/analysis/gini.py`
- 不平等矩阵 `results/gini_matrix.csv`
- 4 张不平等图

---

## Phase 6: 论文写作与投稿（Month 6）

### 目标
完成首版论文（约 10,000 字），投稿目标期刊。

### 子任务

#### Week 21: 引言 + 方法
- [ ] Introduction（3 张图：研究背景、问题、贡献）
- [ ] Methods（4 节：数据、模型、分析、验证）

#### Week 22: 结果 + 讨论
- [ ] Results（5 节：模型精度、TDA、PySR、CCM、Gini）
- [ ] Discussion（局限、未来）

#### Week 23: 内部审阅
- [ ] 课题组讨论
- [ ] 同行预审
- [ ] 图表精修

#### Week 24: 投稿
- [ ] Cover Letter
- [ ] Highlights
- [ ] 数据/代码可用性声明
- [ ] 投稿到目标期刊

### 期刊优先级

```
🥇 主选: Nature Communications (IF 16.6)
   - 强调"AI4Science 范式 + 城市气候"
   - 突出工作站可复现性

🥈 次选: Building and Environment (IF 7.4)
   - 强调"方法学 + 应用"
   - 较易接收

🥉 保底: Sustainable Cities and Society (IF 11.7)
   - 同领域权威期刊
   - 录用率较高
```

---

## 关键里程碑（KPIs）

| 里程碑 | 截止日期 | 验收标准 |
|--------|---------|---------|
| M1: 环境就绪 | 2026-05-13 | 所有依赖通过 verify_install.py |
| M2: 数据集成 | 2026-06-06 | 100m × 1h 统一数据集生成 |
| M3: 模型训练 | 2026-07-06 | LOOCV RMSE < 0.8 K |
| M4: TDA 完成 | 2026-08-06 | 26 亚类拓扑指纹库 |
| M5: 三创新分析完成 | 2026-09-06 | TDA + PySR + CCM 全部交付 |
| M6: Gini 应用完成 | 2026-10-06 | 三层分解结果与可视化 |
| M7: 论文投稿 | 2026-11-06 | 投稿系统提交 |

---

## 风险预案

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| ERA5 数据下载受阻 | 低 | 中 | 备用 HiTiSEA / Google Earth Engine |
| Landsat 云覆盖严重 | 中 | 中 | 用 Sentinel-2 / MODIS 补充 |
| FNO 训练发散 | 中 | 高 | 退到 U-Net + Attention |
| TDA 计算量过大 | 低 | 中 | 用 cubical complex 简化 |
| PySR 不收敛 | 中 | 中 | 减少特征数 + 先用 XGBoost 过滤 |
| 文章一作者抢先发表类似 | 中 | 高 | 加速进度，拆分早投稿 |
| 投稿被拒 | 中 | 高 | 备选 3 个期刊 |

---

## 资源需求

### 硬件
- 工作站: i7/i9 + 32GB RAM + RTX 3090/4090
- 存储: 1 TB SSD
- 网络: 稳定 100 Mbps（数据下载）

### 软件（全部免费）
- Anaconda Python 3.11
- PyTorch 2.x + CUDA 12.x
- Julia 1.10（PySR 后端）
- ArcGIS / QGIS（制图）

### 账号
- ECMWF CDS（ERA5）
- USGS EarthExplorer（Landsat）
- NASA EarthData（MODIS）
- Google Earth Engine（备用）
- 高德/百度地图开放平台 API

### 预算估计
- 云端备份（OneDrive Pro）: ¥100/月
- 阿里云临时实例（紧急扩算）: ¥1,000-2,000
- 论文版面费（OA）: ¥15,000-30,000（投稿后）
- **总计**: ¥20,000-40,000

---

## 团队分工建议（如多人协作）

| 角色 | 职责 |
|------|------|
| PI | 整体方向、论文主笔 |
| 数据工程师 | Phase 1 数据管道 |
| 算法工程师 | Phase 2 FNO 模型 |
| 分析师 | Phase 3-5 创新分析 |
| 制图 | 所有可视化 |

如单兵作战，按 Phase 顺序专注推进。

---

## 下一步

立即执行 Phase 0 任务：

1. 运行 `setup_windows.ps1` 配置环境
2. 运行 `python scripts/verify_install.py` 验证
3. 注册 ECMWF CDS 账号
4. 阅读 `docs/02_methodology.md` 了解技术细节

---

**最后更新**: 2026-05-06
