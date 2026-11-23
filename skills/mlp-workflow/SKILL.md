---
name: mlp-workflow
description: "End-to-end active-learning MLP workflow: (1) foundational-MLP pre-sampling with free MD and reaction-coordinate umbrella windows across compositions and cell sizes, (2) topology filtering, cooldown/hash deduplication, role-pooled SOAP/QUESTS/FPS selection and multivariate coverage auditing, (3) pilot-benchmarked DFT single-point labeling with POSCAR order provenance, raw forces and SCF review, (4) single or committee MACE/CP-MACE training and validation, and (5-6) committee uncertainty active learning (mobile-atom force disagreement, baseline-centered energy std, quarantine, SOAP pruning) feeding back to DFT relabeling and merged dataset updates."
---
# MLP 主动学习全流程

面向机器学习势（MLP）的六步主动学习闭环：**通用势预采样 $\rightarrow$ 构型筛选与覆盖审计 $\rightarrow$ DFT 试跑与批量单点标注 $\rightarrow$ 单模型/委员会训练与实测 $\rightarrow$ 委员会不确定帧采集与剪枝 $\rightarrow$ 回流 DFT 重标并库**。可从任意阶段切入，全程通过 `dataset_index`、输入哈希与原子顺序映射保持严格可追溯。

> **与恒电势体系的边界**：常规固定电子数/中性 DFT 单点与主动学习**不需要**做“电子态划分/去重”（前序选帧的时间冷却与几何去重已足够）；仅当处理变电荷/恒电势 `FermiMACE` 等同一几何对应不同 `NELECT`/`potential` 的体系时，按需结合 `$constant-potential-calculations` 区分电子状态。

## 1. 六步闭环总览与入口确认

| 阶段 | 核心动作 | 关键输入 / 产物 | 详细参考 |
|---|---|---|---|
| **1. 初始构型与预采样** | 用通用基础模型（如 `mace-mp`/`mace-mh`）跑自由 MD（多温度/组分/尺寸）及反应坐标伞窗，生成大候选池 | 初态结构、`manifest.csv` $\rightarrow$ 候选轨迹 `trajectory.extxyz` | [sampling-and-selection.md](references/sampling-and-selection.md) |
| **2. 构型选择与覆盖审计** | 拓扑过滤 + 冷却去重 + **分角色 SOAP**（或 QUESTS）+ 状态优先 FPS，再反查多变量覆盖率 | 候选池 $\rightarrow$ `selected.extxyz`、`frames.csv`、`coverage.csv` | [sampling-and-selection.md](references/sampling-and-selection.md) |
| **3. DFT 批量标注与验收** | 小批量跨节点/内存 `pilot` 试跑定参；按元素排序写 `POSCAR` 并保留 `order` 映射回原序；提取原始力与 `SCF` 复核 | `selected.extxyz` $\rightarrow$ `labeled.extxyz`、`review.csv`、`verification.json` | [dft-labeling.md](references/dft-labeling.md) |
| **4. 势函数训练与验证** | 并库去杂、锁定 `E0s`；多随机种子训练（`MACE` 委员会）；用导出 `.model` 实测与短程 NVE/NVT 验证 | `labeled.extxyz` $\rightarrow$ 独立种子 `.model`、评估与 MD 检查 | [training-and-validation.md](references/training-and-validation.md) |
| **5. 委员会不确定性采帧** | `AverageForceCalculator` 推进生产采样（MD/OPES 等），追踪**可动原子力分歧**与**去零偏能量分歧 `dE_cent`**；崩溃进 `quarantine`；超预算做 SOAP 二次剪枝 | 生产轨迹 + `uncertainty.csv` $\rightarrow$ 筛选帧 `frames/`、`quarantine/` | [active-learning.md](references/active-learning.md) |
| **6. 回流重标与并库** | 对筛选帧沿用冻结物理协议（`science` 哈希一致）重跑第 3 步 DFT，还原原序后合并入 `merged_labeled.extxyz` 进入下一轮 | `al_labeled.extxyz` + 初始 `labeled.extxyz` $\rightarrow$ `merged_labeled.extxyz` | [dft-labeling.md](references/dft-labeling.md) |

开始前只需先向用户确认两项：
1. **当前所处阶段与可用资源**：输入文件所在位置、目标模型/引擎（如 MACE 版本与 VASP 配置）以及涉及集群提交时**是否已获准提交**；
2. **科学协议边界**：能量/力口径（如 `TOTEN` + `apply_constraint=False` 保留固定层真实 DFT 力）、多尺寸体系共享元素组合，以及是否需要额外的独立泛化测试集。

## 2. 跨阶段共享铁律

- **旧力场标签必须清空**：阶段 2 输出 `selected.extxyz`、阶段 4 启动 NVE/NVT 测试前，以及阶段 5 回流 `input.extxyz` 时，一律置 `atoms.calc = None` 且 `write_results=False` 剥离旧预测 `energy`/`forces`/`stress`（仅保留 `dataset_index`、来源元信息与 `FixAtoms`/`move_mask`）。
- **原子顺序双态分离与还原**：DFT 计算前（如 VASP `POSCAR`）可按元素稳定排序以匹配固定 `POTCAR`，但必须将 `order` 映射写入每帧元数据并在收集 `REF_forces` 时精确逆排回原始 `input.extxyz` 顺序。
- **物理协议锁定（`science` 哈希）**：泛函、色散、`ENCUT`、`PREC`、`KPOINTS`、`EDIFF`、`ISPIN` 等物理协议必须生成校验摘要；主动学习第 6 步回流帧必须验证与首批 `labeled.extxyz` 协议完全一致，否则严禁静默合并。
- **不以崩溃帧污染训练集**：主动学习触发必须同时设**触发下限**与**合理性上限/最小原子间距筛查**，超限飞散构型转入 `quarantine/` 排查原因，绝不直接送去耗费 DFT 机时。

## 3. 按需参考与开源仓库

- **阶段 1–2（预采样、分角色选帧与覆盖审计）**：阅读 [sampling-and-selection.md](references/sampling-and-selection.md)
- **阶段 3 & 6（`pilot` 试跑、DFT 标注队列、原子逆序与并库核验）**：阅读 [dft-labeling.md](references/dft-labeling.md)
- **阶段 4（MACE 委员会训练、导出实测与 MD/泛化验证）**：阅读 [training-and-validation.md](references/training-and-validation.md)
- **阶段 5（委员会 `dE_cent`/力分歧、隔离区与 SOAP 二次剪枝）**：阅读 [active-learning.md](references/active-learning.md)

复用关键开源项目：

| 工具 / 方法 | GitHub 仓库 |
|---|---|
| MACE（等变机器学习力场训练、评估与多模型推理） | [ACEsuit/mace](https://github.com/ACEsuit/mace) |
| DScribe（分角色 SOAP 等局部原子环境描述符） | [SINGROUP/dscribe](https://github.com/SINGROUP/dscribe) |
| QUESTS（无模型局部环境信息熵覆盖与 MSC 压缩） | [dskoda/quests](https://github.com/dskoda/quests) |
| CP-MACE / FermiMACE（仅恒电势/变电子数扩展时配合） | [yuanyue-liu-group/CP-MACE](https://github.com/yuanyue-liu-group/CP-MACE) |
