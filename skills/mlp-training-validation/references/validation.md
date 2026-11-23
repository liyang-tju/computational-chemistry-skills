# 模型验证与部署

## 1. 训练配置核对清单

启动前在配置文件或命令行核实以下核心项：
- **数据键名对齐**：`--energy_key`、`--forces_key`、`--stress_key` 与 `train.extxyz` 中的字段名严格一致（例如 `REF_energy` vs `energy`，错配时可能静默读错或报错）。
- **参考能量 `E0s`**：使用 `average` 或显式 DFT 孤立原子能量字典 `"{1: -1.11, 8: -1.56}"`，且保证同一委员会或对比实验完全一致。
- **SWA（Stage Two）切换**：若开启两阶段损失加权（如后期提高能量权重），分别记录 Stage 1 与 Stage 2 各自的最佳验证检查点，使用对应最终导出模型做评测。

## 2. 导出模型实测校验（不可省略）

作业结束后，必须用最终部署时实际调用的 Calculator 加载导出文件验证一次前向计算：

```python
import numpy as np
from ase.io import read
from mace.calculators import MACECalculator

calc = MACECalculator(model_paths="model_compiled.model", device="cpu", default_dtype="float64")
frames = read("test.extxyz", index=":10")

e_errs, f_errs = [], []
for atoms in frames:
    ref_e = atoms.info["REF_energy"]
    ref_f = atoms.arrays["REF_forces"]
    test_atoms = atoms.copy()
    test_atoms.calc = calc
    pred_e = test_atoms.get_potential_energy()
    pred_f = test_atoms.get_forces()
    e_errs.append(abs(pred_e - ref_e) / len(atoms) * 1000.0)  # meV/atom
    f_errs.append(np.sqrt(np.mean((pred_f - ref_f) ** 2)) * 1000.0)  # meV/A

print(f"Sample check -> E_MAE: {np.mean(e_errs):.2f} meV/atom, F_RMSE: {np.mean(f_errs):.2f} meV/A")
```

- 对 CP-MACE 等带额外输入（如电势/电荷/费米能）的变体，额外检查预测电子量与能量对电子变量导数的自洽性。

## 3. 短程 MD 验证（NVE 与 NVT）

- **NVE 能量守恒测试**（验证势能面与力场导数平滑度）：
  - 在无恒温器、小步长（如 `0.5 fs`）下运行短程 NVE（如 2–5 ps），检查总能相对漂移 $|\Delta E_{\text{tot}}| / N_{\text{atoms}}$ 是否保持在合理范围内且无阶跃跳变。
  - 若体系存在 `FixAtoms` 约束，注意约束下的自由度与温度定义，不能把被固定原子的“零动能”混入自由原子自由度。
- **NVT 稳定性检查**：检查轨迹中是否出现非物理靠近（`min_mic_dist < 0.8 Å`）、键长畸变或原子飞散。短程稳定仅证明无明显漏洞，正式长时采样仍需配合不确定性监测。

## 4. 委员会不确定性（Committee Disagreement）

加载多个独立种子的模型计算逐原子力标准差：

```python
# forces_by_model shape: (n_models, natoms, 3)
std_per_component = np.std(forces_by_model, axis=0)          # (natoms, 3)
sigma_f_atom = np.linalg.norm(std_per_component, axis=1)     # 每原子力不确定性 (eV/A)
max_sigma_f = float(np.max(sigma_f_atom))
```

- **解读边界**：委员会分歧反映的是“训练数据分布之外的认知不确定性”，并非精确预测误差；需在验证集上校准 $\sigma_F$ 与真实力误差的相关性后再设定主动学习采集阈值（如 `0.15–0.30 eV/Å`）。
- 采集到高不确定性候选帧后，**先检查其几何是否已经发生崩溃**，确认有效后再送交 `$mlp-dataset-pipeline` 或 `$dft-labeling`（采集本身不自动触发 DFT 提交）。
