# 逐帧结果验收

## 1. 逐帧状态定义（`label_status.csv`）

每条 `sample_id` 在 `label_status.csv` 中必须有明确状态，禁止仅靠“存在 `OUTCAR` 文件”判定成功：

| 状态 | 判定依据 | 下游处理 |
|---|---|---|
| `not_prepared` | 输入目录未生成或缺少必需文件 | 补齐输入 |
| `pending` / `running` | 已生成/已提交，尚未出现正常结束日志 | 等待完成 |
| `failed_scf` | 正常结束或超步退出，但最后电子步触及 `NELM`/`MAX_SCF` 未收敛 | **不收录**，需调 SCF 策略后重试 |
| `failed_runtime` | 进程崩溃、文件截断或能量/力含 `NaN` | **不收录**，保留日志排查 |
| `passed` | 正常结束、电子步收敛、力矩阵形状与有限性通过校验 | 写入 `labeled.extxyz` |

## 2. 原始 DFT 力 vs `FixAtoms` 约束力陷阱

在 ASE 中读取带 `Selective dynamics` 的 VASP `OUTCAR`/`vasprun.xml` 时：
- `atoms.get_forces()` **默认会应用 `FixAtoms` 约束**，将固定层原子的受力强行置 `0.0`！
- 而机器学习势（如 MACE）通常在全原子真实物理力上训练（或需要显式知道哪些原子力被置零）。读取标签时务必明确并统一使用：

```python
# 读取不被 ASE 约束清零的原始 DFT 力
raw_forces = atoms.get_forces(apply_constraint=False)
```

切勿在同一训练集中混用“一部分被 ASE 清零、另一部分保留真实受力”的标签。

## 3. 能量口径、应力与额外字段

- **VASP 能量提取检查**：
  - `atoms.get_potential_energy()` 在 ASE 默认通常读取 `free energy TOTEN`（部分读取器或参数可取 `energy(sigma->0)`）。批量解析脚本应直接明确提取目标字段并写入 `atoms.info["energy"]`，避免混淆自由能与零展宽外推能。
- **应力张量单位与符号**：
  - ASE `extxyz` 约定 `stress` 为 **eV/Å³**（Voigt 6 分量或 3×3 矩阵），而 VASP `OUTCAR` 打印的 `in kB` 需经单位转换且注意正负号约定（压力 vs 应力，ASE 读取 `OUTCAR` 会自动处理为 eV/Å³ 的应力约定，建议用参考单帧核实）。
- **电化学额外字段**：若采集 `NELECT`、`Fermi` 能、静电势参考值或净电荷，应在 `protocol.json` 中注明具体参考零点（如真空能级 vs 内层平均势）与符号。

## 4. 失败帧重试与去重

- 对失败帧建立单独重试目录（如 `retry_01/`），记录 `retry_of_attempt` 和调整后的 SCF 参数（如 `ALGO = All`、`BMIX` 调小），切勿在同一汇总文件中把同一个 `sample_id` 收集两遍。
- 跨集群传输回收结果后，验证每个输出文件行数完整、结构总数与 `sample_map.csv` 核对无误后再进入 `$mlp-dataset-curation`。
