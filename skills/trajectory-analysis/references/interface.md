# 界面分布

## 1. 相对表面坐标与参考面

不同条件下的晶胞原点或基底热运动高度可能发生微移，**不要直接沿用固定绝对 $z$ 窗**（例如硬编码 `z in [12, 15] Å`）：
- 常用定义：每帧取表层金属原子（如顶层 `tag` 或 `role == "slab_top"`）的平均 $z_{\text{surf}}(t)$ 作为参考零点：
  $$z_{\text{rel}, i}(t) = \text{wrap}_{z}\!\bigl(z_i(t) - z_{\text{surf}}(t)\bigr)$$
- 明确法向正方向（指向液相侧为正），并将上下两个界面（若对称双界面）与真空区清晰分离，避免跨周期折叠混到一起。

## 2. 平面密度剖面与归一化

对于法向分箱宽度 $\Delta z$、截面积 $A_{xy}(t) = |\mathbf{a}(t) \times \mathbf{b}(t)|_z$：
- **数密度 / 质量密度**：
  $$\rho(z_k) = \frac{\langle N_k(t) \rangle}{A_{xy} \Delta z} \quad \text{或质量密度}\;(\text{g/cm}^3) = \rho_{\text{num}}\,(\text{molecules/\AA}^3) \times \frac{M_{\text{mol}}}{N_A \cdot 10^{-24}}$$
  （对于含 $N_{\text{frames}}$ 帧的变胞 NPT 轨迹，明确采用逐帧除以瞬时体积 $A_{xy}(t)\Delta z$ 再平均，还是总计数除以累计体积。）
- **区分三种常用纵轴**：粒子绝对个数 $N(z_k)$、质量密度（$\text{g/cm}^3$）与归一化概率密度 $P(z_k)$（$\sum P(z_k)\Delta z = 1$）量纲完全不同；**必做自检**：将数密度沿区间积分，应精确等于该区间内的预期分子数。
- **体相密度窗口**：应选取远离表面至少 10–15 Å 的平缓平台区间统计体相密度，不把第一/第二吸附水层密度峰当成体相密度。

## 3. 水分子取向统计

- **偶极向量重建（防 PBC 撕裂）**：使用最小像距求出同一水分子中 $\mathbf{v}_1 = \text{MIC}(\mathbf{r}_{\text{H}_1} - \mathbf{r}_{\text{O}})$ 与 $\mathbf{v}_2 = \text{MIC}(\mathbf{r}_{\text{H}_2} - \mathbf{r}_{\text{O}})$，偶极方向为 $\hat{\mu} = (\mathbf{v}_1 + \mathbf{v}_2) / \|\mathbf{v}_1 + \mathbf{v}_2\|$（即 O 指向 H–H 中点，注意这是水分子偶极正方向；若论文定义负方向请显式注明）。
- **测度陷阱**：
  - $\langle \cos\theta \rangle$（带正负号：区分 H 朝向液相 vs H 朝向表面）与 $\langle |\cos\theta| \rangle$ 含义不同；
  - $\arccos\langle \cos\theta \rangle \ne \langle \theta \rangle$；
  - 在三维各向同性分布下，$P(\cos\theta)$ 是均匀分布（平直线），而 $P(\theta) \propto \sin\theta$（因球面面积元 $\mathrm{d}\Omega = 2\pi \sin\theta\,\mathrm{d}\theta$），因此**不能直接比较 $P(\theta)$ 与 $P(\cos\theta)$ 曲线形状**。
- **取向加权密度**：$\rho(z)\langle \cos\theta(z) \rangle$ 表达的是极化取向净分布，若无电荷与偶极矩大小乘积因子，不要直接标注为“偶极密度”或“极化电荷密度”。

## 4. RDF 与配位数（CN）

```python
# 示例：使用 ASE MIC 计算两组间距直方图及累计配位数
from ase.geometry import get_distances
_, dists = get_distances(pos_ref, pos_target, cell=atoms.cell, pbc=atoms.pbc)
```

- 同物种自身算 RDF（如 `O_w - O_w`）必须排除自身对（$i = j$）；计算溶质-水配位时写明是否排除同分子内部原子。
- **受限界面注意**：传统三维均匀 RDF 归一化因子 $4\pi r^2 \rho_0 \Delta r$ 假设四周无限均匀分布；对于贴近固体金属表面的水层，半空间被金属占据，在较大 $r$ 处 $g(r)$ 不会自动收敛到 `1.0`（除非扣除不可及金属体积或按局部参照定义），报告时应予以注明或优先给出明确第一溶剂层截止半径 $r_{\text{cut}}$ 内的**积分平均配位数 CN**。
