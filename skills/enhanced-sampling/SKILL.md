---
name: enhanced-sampling
description: "Design and verify CVs, restraints, umbrella windows and PLUMED OPES/Metadynamics inputs for MD engines or ASE. Use for sampling setup and bias troubleshooting; PMF reconstruction belongs to free-energy-analysis."
---
# 增强采样准备

将反应路径或自由能采样需求转化为可执行的集体变量（CV）、约束、伞形采样（Umbrella Sampling）窗口或 PLUMED OPES/Metadynamics 输入，并完成语法、单位、极限行为与导数/作用力验证。自由能重建与重加权属于 `$free-energy-analysis`。

## 开始前确认

- **反应问题与目标边界**：反应物、产物、潜在中间态、目标温度与压力/体积条件，以及需防止哪些非目标旁路反应（如溶质飞离界面、溶剂分解）。
- **引擎与接口**：MD 引擎（LAMMPS / CP2K / GROMACS / ASE `Plumed` 计算器）及当前已安装的 PLUMED 版本与扩展模块（先用 `plumed info --version` 探测）。
- **采样方法**：约束动力学（Blue Moon）、伞形采样（多窗口 `RESTRAINT`）、还是自适应偏置（`OPES_METAD` / `METAD`）。

## 工作流程

### 1. 基于真实初始结构生成原子组与索引

- 检查 PLUMED（**1-based** 索引）与 Python/ASE（**0-based** 索引）的编号转换，切勿错位 1 号原子！
- 若体系发生质子转移（Grotthuss 跳跃）或溶剂分子交换，不可只绑死单个固定 O-H 原子对来追踪水合氢离子/羟基，改用连续反应坐标或 Voronoi/配位数中心（详见 [反应性 CV](references/reactive-cv.md)）。

### 2. 显式声明单位与选择采样参数

PLUMED 默认单位为 `nm`、`kJ/mol`、`ps`，**与 ASE/VASP/LAMMPS `metal`（Å, eV）或 `real`（Å, kcal/mol）不同**。必须在 `plumed.dat` 首行显式写出 `UNITS`：

```text
UNITS LENGTH=A ENERGY=eV TIME=ps
```

- **`PACE` 与时间换算**：`PACE` 的单位是 **MD 步数**而非皮秒；改变 `timestep` 时必须同步核对实际沉积时间间隔（`PACE * dt`）。
- **限制壁势（`LOWER_WALLS`/`UPPER_WALLS`）与 `EXCLUDED_REGION`**：`EXCLUDED_REGION` 仅阻止在该区间内沉积核函数，**不提供排斥力**；需要限制采样范围时必须加 `LOWER_WALLS` / `UPPER_WALLS`，并记录壁势位置。

### 3. 编写窗口或偏置输入并区分 Fresh vs Restart

- **伞形采样窗口**：所有窗口共享统一协议（单位、力常数 `KAPPA`、温度），并为每个窗口记录明确的中心 `AT` 与初态来源（若初态由拉伸 SMD 产生，注明是否做了窗口预平衡）。
- **Fresh vs Restart 语义**：全新采样使用空状态（不读旧 `KERNELS`/`STATE`）；续算必须在 `plumed.dat` 中显式设置 `RESTART=YES` 并匹配与 MD 检查点同一时刻的 `STATE_RFILE`/`KERNELS`（详见 [偏置语义](references/plumed-opes.md)）。

### 4. 解析校验、导数检验与短程试跑

不能仅凭 `plumed driver` 不报语法错误就认为施加的偏置力正确，必须依次完成三层验证：
1. **静态解析**：`plumed driver --plumed plumed.dat --mf_xyz init.xyz` 检查无未知关键字与原子索引越界。
2. **极限与导数核对**：对自定义 `CUSTOM`/`MATHEVAL` 或反应性 CV，构造已知端态构型检查 CV 数值范围，并用微小坐标扰动 $\pm \delta$ 做**有限差分检验**，核对解析导数施加的偏置力符号和量级正确。
3. **引擎接口实测**：在独立测试目录跑 5–20 步短程 MD，检查输出 `COLVAR` 数值、偏置势及原子受力均有限且稳定（若使用 ASE `Plumed` 包装器，核实多行块文本转换方式）。

## 按需参考

- PLUMED `UNITS`、`OPES_METAD` 参数、ASE 多行输入坑与 `plumed driver` 检查命令：阅读 [偏置语义](references/plumed-opes.md)。
- 质子转移、Voronoi CV 连续性导数检查与自定义 Action 探测：阅读 [反应性 CV](references/reactive-cv.md)。

## 交付产物与验收

1. `plumed.dat`（或引擎约束输入如 `ICONST`）、窗口清单 `windows.csv`（伞形采样时）与 `bias-protocol.json`。
2. **验收标准**：`plumed driver` 实测 `COLVAR` 数值符合初态化学预期、无 `NaN`/跳变、短程试跑受力有限（注意：输入准备通过不代表自由能已收敛）。
