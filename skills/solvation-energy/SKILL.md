---
name: solvation-energy
description: "Prepare and analyze frozen-fragment energy decompositions (AWS, WS, AS, S, A) from solvated trajectories or static geometries with strict geometry provenance, electronic-state matching and frame-wise completeness checks."
---
# 溶剂化能与冻结片段分析

基于同源冻结几何（或明确定义的优化几何）构造片段子体系（如完整界面 `AWS`、水-表面 `WS`、吸附物-表面 `AS`、裸表面 `S`、孤立吸附物 `A`），完成单点计算任务编排、逐帧成分完整度核验与能量分解统计。不同组合公式对应不同的物理含义，切勿把冻结单点能差直接等同于平衡态溶剂化自由能 $\Delta G_{\text{solv}}$。

## 开始前确认

- **目标物理量与分解公式**：明确所需组合式（如四项溶剂对吸附能的修正 $\Delta \Delta E_{\text{solv}} = [E(AWS) - E(WS)] - [E(AS) - E(S)]$，或五项包含 $E(A)$ 的交互分解）。
- **几何来源**：从 MD/AIMD 轨迹抽取的冻结瞬时构型、真空优化构型，还是隐式溶剂优化构型（不同来源必须独立贴标）。
- **电子协议**：恒电荷（固定中性或固定 `NELECT`）还是恒电势（含巨正则电化学势变换 $\Omega = E - \mu_e \Delta N_e$），及所有片段是否采用统一的泛函、截断能、k 点与赝势。

## 工作流程

### 1. 抽帧与角色映射

- 从已核验健康的轨迹段按明确步长抽取帧，记录 `sample_id`、`replica_id`、`simulation_step` 与 `time`。
- 利用原子分组表（`slab` / `adsorbate` / `solvent`）确认每帧吸附质未发生非预期解离或质子逃逸；若存在质子转移，按规则归类该帧（如单独分入反应后物种组），不暗中替换吸附质原子索引。

### 2. 原坐标生成冻结片段（严禁重居中或重新包裹）

抽取 `AWS`、`WS`、`AS`、`S`（及所需 `A`、`W`）时，**必须保留原晶胞、PBC 与精确原子绝对坐标**：

```python
# 示例：基于原子分组索引原位切片，禁止调用 .center() 或 .wrap()
def extract_fragment(atoms, indices):
    frag = atoms[indices].copy()
    frag.calc = None
    frag.info.clear()
    return frag
```

若后续还需做空间电荷密度差分或静电势差分，必须保证各片段在同一晶胞原点、同一网格密度下计算，否则无法逐点相减。

### 3. 确定各片段电子态与单点协议

- 为每个片段显式指定总电荷 / `NELECT` 与自旋多重度（详见 [能量组合与参考](references/decomposition.md)）。
- 准备分块/分目录单点输入并记录 `fragment_mapping.csv`。若用户要求按新协议全量重算，全部片段统一重算，不混用旧协议已有的部分结果。

### 4. 逐帧验收完整性后再做减法组合

必须确保同一 `sample_id` 所需的**所有片段**均正常完成且电子 SCF 收敛后，才计算组合能差：
- 只要某帧缺少任意一个片段（如 `WS` 收敛失败），该帧标记为 `incomplete`，**严禁用 0 填充或借用其他帧的 `E(S)`/`E(WS)`**；
- 同时核对单位一致（统一为 eV）并检查是否存在明显离群值（通常反映某一片段落入错误的电子自旋态或电荷振荡）。

### 5. 分层统计与误差报告

- 按“逐帧 $\to$ 逐独立重复轨迹（replica）$\to$ 条件均值”分层汇报均值与自相关/重复误差；
- 若同时计算偶极、电荷转移等电子性质，逐帧对齐后再分析相关性，不将跨体系均值强相关直接当成单帧微观因果证明。

## 按需参考

- 四项/五项分解公式物理含义、带电片段补偿与统计口径：阅读 [能量组合与参考](references/decomposition.md)。

## 交付产物与验收

1. **`fragment_mapping.csv`**：`sample_id, fragment_type, natoms, formula, charge_or_nelect, task_dir`。
2. **`energies_by_fragment.csv`** 与 **`decomposition_results.csv`**：逐帧各片段能量、收敛状态与最终组合能差。
3. **`sampling.json`**：记录公式定义、几何来源类别、协议标识、有效样本数与缺帧统计。
