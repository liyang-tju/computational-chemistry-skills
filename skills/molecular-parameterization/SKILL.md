---
name: molecular-parameterization
description: "Prepare molecular quantum geometry/frequency checks, ESP/RESP charge fitting, atom typing and force-field topology assembly (including polymer head/monomer/tail templates) while preserving atom mapping and mixing-rule compatibility."
---
# 分子参数化

从分子、离子或聚合物结构出发，完成量化优化与频率校验、ESP/RESP 电荷拟合、力场原子类型匹配与拓扑组装，确保原子索引映射、电荷约束、1–4 缩放规则和混合规则可追溯且自洽。

## 开始前确认

- **目标力场家族与模拟引擎**：GAFF/GAFF2、OPLS-AA、CHARMM 等力场家族，以及最终运行引擎（LAMMPS `data` / GROMACS `.itp`/`.top` / Amber `.mol2`+`.frcmod`）。
- **化学模型与构象**：分子连接关系（SMILES/MOL2/SDF）、端基、聚合物重复单元（head/internal/tail）、净电荷、自旋多重度与代表性构象列表。
- **量化与电荷协议**：优化泛函/基组、是否需要频率校验、ESP 计算层级（如 B3LYP/6-31G* 或用户指定协议与溶剂条件）、RESP 约束方式（单构象还是多构象联合拟合）及可用工具（ORCA/Gaussian、Multiwfn、AmberTools `antechamber`/`parmchk2`、`acpype` 等）。

## 工作流程

### 1. 核对键连接与原子映射

- 从带有明确键级和氢原子的输入出发（如 `.mol2`/`.sdf`），为全原子建立稳定索引与原子名称，防止量化软件重排或脱帽连接时编号错乱。
- 对于**聚合物**：预先拆清**端帽（capping groups）**与**主链连接点（head/tail junctions）**，明确拼接时删除的原子和新增的共价键。

### 2. 分阶段准备量化计算（不混并阶段）

1. **构型优化（Opt）**：如目标构象尚未优化，在明确协议下优化并核对几何收敛与化学键未发生意外断裂。
2. **频率验证（Freq）**：仅当需要确认驻点或计算热力学修正时运行频率；**必须检查全部振动频率为正（无虚频）**才可标为极小点（仅存在频率输出文件不够）。若用户指定做固定构象单点，不私自重新优化几何。
3. **波函数/ESP 单点（SP）**：导出含完整轨道和基组的文件（`.fchk`/`.wfx`/`.molden`）或量化软件直接写出的格点 ESP 文件。

### 3. 执行 ESP / RESP 电荷拟合

按所选拟合协议记录（详见 [电荷与拓扑](references/charges-topology.md)）：
- 静电势采样网格/表面定义（如 MK / CHELPG / Connolly 壳层）、双阶段 RESP 约束权重与等价原子组（如甲基三个氢原子强制等价）；
- 检查总电荷精确闭合（整数或指定小数精度）；对聚合物提取**头部、中间重复单元、尾部**电荷模板时，需显式说明端帽电荷约束和余数微调去向。

### 4. 生成力场原子类型与拓扑文件

- 使用 `antechamber` + `parmchk2` / `acpype` / 目标拓扑工具生成原子类型、键、角、二面角、非正常二面角（impropers）及 Lennard-Jones 参数。
- 检查是否存在高惩罚值或缺失的二面角/键合项（如 `.frcmod` 中的 `ATTN, need revision` 标记），明确报告待校验参数，不可无声忽略。
- 严格核对**力场家族一致性**：不同力场的 1–4 缩放因子（`special_bonds` / `fudgeLJ`、`fudgeQQ`）和组合规则（Lorentz-Berthelot `arithmetic` vs `geometric`）不同，不能把某套电荷直接硬塞进另一力场框架而声称标准兼容。

### 5. 单分子一致性校验

将最终生成的力场拓扑转换到目标 MD 引擎（如 LAMMPS / GROMACS）后，跑一次单分子能量/短程优化检验：
- 核对原子总数、总质量、净电荷总和；
- 检查与量化参考构象相比是否发生键长/键角剧烈畸变或环翻转错误。

## 按需参考

- 量化导出格式、Multiwfn/RESP 拟合阶段区分、聚合物模板处理与力场混合规则核对表：阅读 [电荷与拓扑](references/charges-topology.md)。

## 交付产物与验收

1. 量化输入与收敛核验记录、`charges.csv`（含等价组与约束说明）。
2. 目标引擎拓扑文件（如 `.mol2`/`.frcmod`/`.itp`/`system.data`）及 `atom_mapping.csv`。
3. **`parameterization.json`**：记录量子层级、电荷方法、力场家族、1–4 缩放规则、混合规则与已知缺失/经验参数提示。
