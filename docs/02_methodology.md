# WUDAPT-FUSE 方法学详细规范

---

## 总体架构

```
INPUT (多源数据)
    │
    ├── Tier 1: 大尺度先验
    │   ├── ERA5-HEAT UTCI (25km × 1h)
    │   └── HiTiSEA UTCI (10km × 日)
    │
    ├── Tier 2: 高分辨率锚点
    │   ├── Landsat 8/9 LST (30m × 16d)
    │   └── MODIS LST (1km × 4×/d)
    │
    ├── Tier 3: 静态特征
    │   ├── LCZ 地图 (100m)
    │   ├── 10 个 UMPs (100m)
    │   ├── DEM (30m)
    │   └── 距离海岸/山脉
    │
    └── Tier 4: 真值
        └── 116 MMS 站点 (站点级 × 分钟)

         │
         ▼
[Layer 1: 数据融合 ETL]
   - 时空重采样到 100m × 1h
   - 缺失填补 (kriging + IDW)
   - 数据 QC

         │
         ▼
[Layer 2: 神经下采样]
   - Fourier Neural Operator
   - LCZ-aware Attention
   - Physics-Informed Loss
   - 输出: 100m × 1h × UTCI

         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
    [Layer 3a]      [Layer 3b]     [Layer 3c]
    TDA 拓扑分析    PySR 符号回归   CCM 因果推断

         │              │              │
         └──────┬───────┴──────────────┘
                ▼
[Layer 4: 应用]
   Gini 不平等 + 跨城市迁移

         │
         ▼
OUTPUT (论文成果)
```

---

## Layer 1: 数据融合 ETL

### 1.1 时空对齐

**目标网格**: 深圳全域 100m × 100m，UTM Zone 50N (EPSG:32650)
**时间网格**: 2020-01-01 00:00 至 2020-12-31 23:00 UTC，1 小时步长
**总时空点**: ~ 100 万网格 × 8760 小时 ≈ 8.76 × 10⁹ 数据点

### 1.2 重采样规则

| 数据 | 原分辨率 | 重采样方法 |
|------|---------|----------|
| ERA5-HEAT UTCI | 25km × 1h | 双线性插值（空间）+ 不变（时间） |
| HiTiSEA UTCI | 10km × 日 | 双立方插值 + 时间立方样条 |
| Landsat LST | 30m × 16d | 平均聚合 + 时间最近邻（仅作锚点） |
| MODIS LST | 1km × 4×/d | 双立方 + 时间线性 |
| LCZ | 100m | 直接对齐 |
| UMPs | 100m | 直接对齐 |
| DEM | 30m | 平均聚合至 100m |
| MMS 站点 | 点 × 分钟 | 1h 平均，作为标签 |

### 1.3 缺失值处理

**Landsat 云覆盖**:
- 时序 Whittaker 平滑 + Savitzky-Golay
- 空间 Krige 插值

**站点缺失**:
- < 6 小时: 线性插值
- 6-24 小时: 同时段 ARIMA 预测
- > 24 小时: 标记为缺失

### 1.4 输出

```python
ds = xr.Dataset({
    'utci_25km':       ('time', 'y', 'x'),  # ERA5-HEAT
    'utci_10km':       ('time', 'y', 'x'),  # HiTiSEA
    'lst_landsat':     ('time', 'y', 'x'),  # Landsat
    'lst_modis':       ('time', 'y', 'x'),  # MODIS
    'lcz':             ('y', 'x'),
    'bsf':             ('y', 'x'),
    'mbh':             ('y', 'x'),
    # ... 其他 8 个 UMPs
    'dem':             ('y', 'x'),
    'dist_coast':      ('y', 'x'),
})
ds.to_zarr('data/processed/shenzhen_2020.zarr')
```

---

## Layer 2: Fourier Neural Operator (FNO)

### 2.1 数学基础

FNO 学习参数化算子 $\mathcal{G}_\theta: a \mapsto u$，其中：
- $a \in A$: 输入函数（多源特征场）
- $u \in U$: 输出函数（UTCI 场）

每层运算：

$$\mathcal{F}^{-1}(R_\theta \cdot \mathcal{F}(v))(x) + Wv(x)$$

其中 $\mathcal{F}$ 是 Fourier 变换，$R_\theta$ 是可学习的频域参数。

### 2.2 网络架构

```python
class WUDAPT_FUSE_FNO(nn.Module):
    def __init__(
        self,
        in_channels=15,        # 多源特征数
        out_channels=1,        # UTCI
        hidden_channels=64,
        n_modes=(16, 16),
        n_layers=4
    ):
        super().__init__()

        # Lifting (channel projection)
        self.lifting = nn.Conv2d(in_channels, hidden_channels, 1)

        # FNO 主干
        self.fno_blocks = nn.ModuleList([
            FNOBlock(hidden_channels, n_modes)
            for _ in range(n_layers)
        ])

        # LCZ-aware attention
        self.lcz_attention = LCZAttention(hidden_channels, num_lcz=10)

        # Projection
        self.projection = nn.Conv2d(hidden_channels, out_channels, 1)

    def forward(self, x, lcz_map):
        h = self.lifting(x)
        for block in self.fno_blocks:
            h = block(h)
        h = self.lcz_attention(h, lcz_map)
        return self.projection(h)
```

### 2.3 输入特征（15 通道）

| # | 特征 | 来源 |
|---|------|------|
| 1 | UTCI_25km (插值至 100m) | ERA5-HEAT |
| 2 | UTCI_10km (插值至 100m) | HiTiSEA |
| 3 | LST_landsat | Landsat |
| 4 | LST_modis | MODIS |
| 5 | NDVI | Sentinel-2 |
| 6 | BSF | UMPs |
| 7 | MBH | UMPs |
| 8 | SBH | UMPs |
| 9 | SVF | UMPs |
| 10 | PSF | UMPs |
| 11 | BV | UMPs |
| 12 | DEM | SRTM |
| 13 | dist_coast | 计算 |
| 14 | hour_sin | 时间编码 |
| 15 | hour_cos | 时间编码 |

### 2.4 LCZ-aware Attention

```python
class LCZAttention(nn.Module):
    """每个 LCZ 类型有独立的注意力权重"""
    def __init__(self, channels, num_lcz=10):
        super().__init__()
        self.lcz_embeddings = nn.Embedding(num_lcz + 1, channels)

    def forward(self, h, lcz_map):
        # h: [B, C, H, W]
        # lcz_map: [B, H, W] (LCZ 类型 1-10)
        lcz_emb = self.lcz_embeddings(lcz_map.long())  # [B, H, W, C]
        lcz_emb = lcz_emb.permute(0, 3, 1, 2)         # [B, C, H, W]
        return h * torch.sigmoid(lcz_emb)
```

### 2.5 物理约束损失

```python
def physics_informed_loss(pred, target, inputs, weights=None):
    """
    pred:   预测 UTCI [B, 1, H, W]
    target: 观测 UTCI [B, 1, H, W]  (站点处)
    inputs: 多源输入字典
    """
    # 1. 数据损失（仅在有站点的位置计算）
    mask = ~torch.isnan(target)
    L_data = F.mse_loss(pred[mask], target[mask])

    # 2. UTCI 公式一致性约束
    AT = inputs['t2m']
    RH = inputs['rh']
    WS = inputs['ws10']
    MRT = estimate_mrt_simple(AT, inputs['svf'])

    utci_formula = utci_polynomial(AT, RH, WS, MRT)
    L_formula = F.mse_loss(pred, utci_formula)

    # 3. 空间梯度平滑约束
    grad_x = torch.abs(pred[:, :, :, 1:] - pred[:, :, :, :-1])
    grad_y = torch.abs(pred[:, :, 1:, :] - pred[:, :, :-1, :])
    L_smooth = grad_x.mean() + grad_y.mean()

    # 4. 物理范围约束（UTCI 通常在 -50 到 +50）
    L_range = F.relu(pred - 50).mean() + F.relu(-50 - pred).mean()

    return L_data + 0.3*L_formula + 0.05*L_smooth + 0.1*L_range
```

### 2.6 训练配置

```yaml
# configs/fno_train.yaml
model:
  type: WUDAPT_FUSE_FNO
  hidden_channels: 64
  n_modes: [16, 16]
  n_layers: 4

training:
  batch_size: 8
  num_epochs: 100
  optimizer: AdamW
  lr: 1e-3
  weight_decay: 1e-4
  scheduler: OneCycleLR
  precision: 16  # 混合精度

data:
  train_split: 0.8
  val_split: 0.1
  test_split: 0.1
  patch_size: [128, 128]  # 12.8 km × 12.8 km patches
  augment: true

loss:
  weights:
    data: 1.0
    formula: 0.3
    smooth: 0.05
    range: 0.1

logging:
  wandb_project: wudapt-fuse
  log_freq: 10
```

---

## Layer 3a: 拓扑数据分析（TDA）

### 3a.1 Persistent Homology 工作流

```
UTCI 二维场 (H × W)
    │
    ▼
Cubical Complex 构建
    │
    ▼
计算 H_0, H_1 维持续同调
    │
    ▼
Persistence Diagram (出生时间, 死亡时间)
    │
    ▼
向量化: Persistence Image / Landscape
    │
    ▼
拓扑特征向量 (维度 ~ 100-500)
```

### 3a.2 关键指标

```python
import gudhi
import numpy as np

def compute_topology_features(utci_field):
    """对 UTCI 场计算拓扑特征"""
    cc = gudhi.CubicalComplex(top_dimensional_cells=utci_field)
    cc.compute_persistence()

    diagrams = cc.persistence()

    features = {}

    # H_0: 连通分量
    h0 = [pd for d, pd in diagrams if d == 0]
    features['n_components'] = len(h0)
    features['max_component_lifetime'] = max(b - d for b, d in h0 if d != float('inf'))

    # H_1: 一维洞 (热岛环绕的冷岛)
    h1 = [pd for d, pd in diagrams if d == 1]
    features['n_holes'] = len(h1)
    features['total_hole_lifetime'] = sum(d - b for b, d in h1)

    # Persistence entropy
    features['persistence_entropy'] = compute_pe(diagrams)

    # Persistence landscape (用于后续聚类)
    features['landscape'] = compute_landscape(diagrams, num_landscapes=3, resolution=100)

    return features
```

### 3a.3 拓扑距离

```python
from gudhi.wasserstein import wasserstein_distance

def topology_distance(diag1, diag2, p=2):
    return wasserstein_distance(diag1, diag2, order=p)

# 26 × 26 距离矩阵（LCZ 亚类间）
distance_matrix = np.zeros((26, 26))
for i, sub1 in enumerate(subcategories):
    for j, sub2 in enumerate(subcategories):
        distance_matrix[i, j] = topology_distance(
            diagrams[sub1], diagrams[sub2]
        )
```

### 3a.4 Mapper 网络

```python
from sklearn.cluster import DBSCAN
from gtda.mapper import make_mapper_pipeline

mapper = make_mapper_pipeline(
    filter_func='UMAP',          # 使用 UMAP 作为投影
    cover='CubicalCover',
    clusterer=DBSCAN(eps=0.5)
)
graph = mapper.fit_transform(topological_features_matrix)
```

---

## Layer 3b: 符号回归（PySR）

### 3b.1 配置

```python
from pysr import PySRRegressor

model = PySRRegressor(
    # 进化搜索
    niterations=300,
    populations=20,
    population_size=50,

    # 操作符
    binary_operators=["+", "-", "*", "/"],
    unary_operators=["log", "exp", "sqrt", "square"],

    # 物理约束
    constraints={"^": (-2, 2)},
    nested_constraints={
        "exp": {"exp": 0, "log": 0},
        "log": {"log": 0, "exp": 0},
    },
    complexity_of_operators={
        "exp": 3,
        "log": 2,
    },

    # 多目标 Pareto 前沿
    model_selection="best",  # 也可选 'accuracy' 或 'score'
    elementwise_loss="loss(x, y) = (x - y)^2",

    # 性能
    procs=8,
    parsimony=0.0032,

    # 输出
    progress=True,
    verbosity=1,
)

# 训练
model.fit(
    X=df[['BSF', 'MBH', 'SBH', 'SVF', 'PSF', 'BV', 'NDVI']],
    y=df['UTCI']
)

# 输出 Pareto 前沿
print(model.equations_)
# 选择最佳方程
print(model.get_best().equation)
```

### 3b.2 期望发现

```
方程候选 1（简洁）:
   UTCI ≈ 28 + 4·BSF − 8·SVF + 0.3·sqrt(BV)
   R² = 0.84, complexity = 12

方程候选 2（中等）:
   UTCI ≈ 27 + 4·BSF − 8·SVF + 0.3·sqrt(BV) − 0.05·PSF·MBH
   R² = 0.88, complexity = 17

方程候选 3（详细）:
   UTCI ≈ 28 + log(1+BV)·sqrt(BSF) − 8·SVF·(1−PSF) − ...
   R² = 0.91, complexity = 23
```

---

## Layer 3c: 因果推断

### 3c.1 Convergent Cross Mapping (CCM)

```python
import skccm
from skccm import Embed

def ccm_causality(X_series, Y_series, lag=1, embed_dim=3):
    """
    检验 X 是否因果驱动 Y
    返回: skill score (0-1)
    """
    # 嵌入
    em_X = Embed(X_series, lag=lag, embed_dim=embed_dim)
    em_Y = Embed(Y_series, lag=lag, embed_dim=embed_dim)

    # 跨映射
    ccm = skccm.CCM()
    ccm.fit(em_X, em_Y)
    sc1, sc2 = ccm.score(score_metric='corrcoef')

    return {
        'X_drives_Y': sc1[-1],  # X→Y
        'Y_drives_X': sc2[-1],  # Y→X
    }

# 应用到每个 UMP
ccm_results = {}
for ump in ['BSF', 'MBH', 'SVF', 'PSF', 'BV', 'NDVI']:
    ccm_results[ump] = ccm_causality(
        X_series=df[ump].values,
        Y_series=df['UTCI'].values
    )
```

### 3c.2 双重机器学习（DML）

```python
from econml.dml import DML

# 估计 SVF 对 UTCI 的因果效应（控制混淆变量）
dml = DML(
    model_y=RandomForestRegressor(n_estimators=200),
    model_t=RandomForestRegressor(n_estimators=200),
    model_final=Lasso(alpha=0.01)
)

dml.fit(
    Y=df['UTCI'],
    T=df['SVF'],
    X=df[['BSF', 'MBH', 'PSF', 'BV', 'dem', 'dist_coast']],  # 混淆
    W=df[['hour', 'season']]                                   # 控制
)

# 平均处理效应
ate = dml.ate()
ate_interval = dml.ate_interval(alpha=0.05)
print(f"ATE of SVF on UTCI: {ate:.3f} (95% CI: [{ate_interval[0]:.3f}, {ate_interval[1]:.3f}])")

# 反事实预测
counterfactual = dml.effect(X_test, T0=current_svf, T1=current_svf + 0.1)
```

---

## Layer 4: 应用

### 4.1 Gini 不平等（详见前文方案）

### 4.2 跨城市迁移

```python
# 在深圳数据上预训练
model_sz = train_fno(shenzhen_data)

# 在广州做迁移学习（少量数据微调）
model_gz = transfer_learning(
    pretrained=model_sz,
    target_data=guangzhou_data,
    freeze_layers=['lifting', 'fno_blocks'],
    finetune_layers=['lcz_attention', 'projection'],
    epochs=10
)
```

---

## 验证策略

### 1. LOOCV 站点交叉验证
- 116 个站点轮流做测试
- 计算 RMSE, MAE, R²
- 报告分位数（5%, 50%, 95%）

### 2. 时序外推
- 用 2020 训练，2021 验证
- 评估时间稳定性

### 3. 物理一致性
- 检查能量平衡残差
- 检查 UTCI 与 AT 的物理关系

### 4. 与文章一对比
- 用同样的 116 站点 LOOCV
- 表格列出 RMSE 对比

---

**最后更新**: 2026-05-06
