# 阶段 4：模型训练、实测评估与 MD 验证

核心仓库：[ACEsuit/mace](https://github.com/ACEsuit/mace)（变电荷/恒电势扩展见 [yuanyue-liu-group/CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE)）。

## 1. 训练数据集准备：直接并库 vs 独立测试防泄漏

- **精选数据与 AL 并库（无需重复重洗）**：若第 2 步已用时间冷却（如 `>= 0.15 ps`）、几何去重和分角色 FPS 筛选出离散代表帧，且第 5 步 AL 回采同样自带去重与冷却，则通过第 3 步 SCF 验收的 `labeled.extxyz` / `merged_labeled.extxyz` 可直接用于训练（重点核查孤立原子参考能 `E0s` 一致、所有帧 `REF_energy` / `REF_forces` 有限且已按 `apply_constraint=False` 统一）。
- **轻量 `train / val` 与“论文级独立泛化测试”区分**：
  - 主动学习生产迭代阶段，重点是最大化覆盖空间并跟踪 `val` 曲线收敛，可直接按比例切分 `train / val`；
  - 若需要评估模型对**未见轨迹、未见温度或未见尺寸体系**的严格外推精度，则应把对应的整条轨迹或整个条件分支按 `group_id` 单独隔离成锁定 `test.extxyz`（绝不让同源短时帧跨集混用）。
- **关于电子状态划分**：标准固定电子数/中性 DFT 体系无需按电子态拆分去重；仅当引入变 `NELECT`/`potential`（`CP-MACE` / `FermiMACE`）数据时，参见 `$constant-potential-calculations` 对齐 `potential` 与过剩电子数 $\Delta N_e$。

## 2. 委员会（Committee）独立训练与归档规范

主动学习依赖多个同架构、不同随机种子的模型构成委员会（典型 4 个种子如 `1, 2, 7, 42`）：
- **只读确认真实 CLI**：先运行 `mace_run_train --help` 核对当前安装版本参数（以及 CPU/GPU DDP 环境下的线程与节点绑定）；
- **种子间严格共享一致协议**：
  - 相同的 `--energy_key` / `--forces_key` / `--stress_key`（如 `REF_energy`、`REF_forces`）
  - 相同的 `E0s` 策略（显式 DFT 孤立原子字典或同一 `average` 口径）与损失权重（包括 Stage Two / SWA 配置）
- **目录隔离与汇总台账**：每个 `--seed` 使用完全独立的运行目录，严禁跨种子复制 `.pt` checkpoint 或旧模型权重；训练完成后生成统一 `training_summary.csv`（记录 `seed`、作业号、`epochs_completed`、最佳 `checkpoint_epoch`、`valid_energy_rmse_meV_per_atom`、`valid_force_rmse_meV_per_A`、导出 `.model` 路径与日志文件位置）。

## 3. 导出模型实测校验

勿仅因训练完成即直接部署，必须用**最终导出的 `.model` 推理文件**加载 `MACECalculator` 在代表帧或测试集上真实运行前向评估（并确认是否需要或支持 TorchScript / LAMMPS 接口导出）：

```python
import numpy as np
from ase.io import read
from mace.calculators import MACECalculator

calc = MACECalculator(model_paths="model_seed_1.model", device="cpu", default_dtype="float64")
frames = read("test_or_val.extxyz", index=":20")

e_errs, f_errs = [], []
for atoms in frames:
    ref_e = atoms.info["REF_energy"]
    ref_f = atoms.arrays["REF_forces"]
    probe = atoms.copy()
    probe.calc = calc
    pred_e = probe.get_potential_energy()
    pred_f = probe.get_forces()
    e_errs.append(abs(pred_e - ref_e) / len(atoms) * 1000.0)  # meV/atom
    f_errs.append(np.sqrt(np.mean((pred_f - ref_f) ** 2)) * 1000.0)  # meV/A

print(f"Check -> E_MAE: {np.mean(e_errs):.2f} meV/atom, F_RMSE: {np.mean(f_errs):.2f} meV/A")
```

若出现个别高力误差离群帧，优先回查是否来自第 3 步的 `review.csv` 软复核异常帧或尚未覆盖的罕见配位态。

## 4. 短程 NVE / NVT 稳定性体检（部署长时生产前）

在将委员会部署去跑 500 ps 级长时增强采样（如 OPES-Explore）前，取各代表尺寸/体系初态（先置 `atoms.calc = None` 清空旧缓存、保留 `FixAtoms`）做一次短程体检：
- **NVE 能量守恒（2–5 ps，小步长如 `0.5 fs`）**：检验总能无明显单调漂移或阶跃（存在 `FixAtoms` 时需剔除固定原子自由度，只按可动原子统计动能温度）；
- **NVT 物理检查**：检验表面、吸附物与溶剂保持结构完整、无非物理原子穿插（`min_mic_dist >= 0.75 Å`）。
