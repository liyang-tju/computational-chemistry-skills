# 通用计算化学与材料模拟 Skills

这套技能按任务组织，包含 20 个独立技能。每个目录提供 SKILL.md、按需参考文档和界面元数据；可以单独复制使用，不要求其他技能目录同时存在。

技能正文使用中文，自动匹配描述保留软件与方法的英文名称。内容采用通用化流程，不包含个人身份、组织、实际主机、项目路径、历史任务编号或私有数据。软件、算法和标准格式名称保留。

## 技能目录

| 编号 | 技能 | 调用名称 |
|---|---|---|
| 1 | [集群作业管理](skills/hpc-job-management/SKILL.md) | hpc-job-management |
| 2 | [计算审计与续算](skills/simulation-audit-restart/SKILL.md) | simulation-audit-restart |
| 3 | [轨迹整理与转换](skills/trajectory-tools/SKILL.md) | trajectory-tools |
| 4 | [科学软件构建](skills/scientific-software-build/SKILL.md) | scientific-software-build |
| 5 | [原子模型构建](skills/atomistic-model-builder/SKILL.md) | atomistic-model-builder |
| 6 | [分子参数化](skills/molecular-parameterization/SKILL.md) | molecular-parameterization |
| 7 | [VASP 计算准备](skills/vasp-calculations/SKILL.md) | vasp-calculations |
| 8 | [CP2K 计算准备](skills/cp2k-calculations/SKILL.md) | cp2k-calculations |
| 9 | [LAMMPS 模拟准备](skills/lammps-md/SKILL.md) | lammps-md |
| 10 | [增强采样准备](skills/enhanced-sampling/SKILL.md) | enhanced-sampling |
| 11 | [自由能分析](skills/free-energy-analysis/SKILL.md) | free-energy-analysis |
| 12 | [代表性构型选择](skills/representative-selection/SKILL.md) | representative-selection |
| 13 | [DFT 批量标注](skills/dft-labeling/SKILL.md) | dft-labeling |
| 14 | [MLP 数据集整理](skills/mlp-dataset-curation/SKILL.md) | mlp-dataset-curation |
| 15 | [MLP 训练与验证](skills/mlp-training-validation/SKILL.md) | mlp-training-validation |
| 16 | [轨迹统计分析](skills/trajectory-analysis/SKILL.md) | trajectory-analysis |
| 17 | [溶剂化能分量分析](skills/solvation-energy/SKILL.md) | solvation-energy |
| 18 | [电子结构与波函数分析](skills/electronic-properties/SKILL.md) | electronic-properties |
| 19 | [描述符与统计建模](skills/descriptor-modeling/SKILL.md) | descriptor-modeling |
| 20 | [科研绘图与结构渲染](skills/scientific-figures/SKILL.md) | scientific-figures |

## 使用

以 $trajectory-analysis 等名称调用，并给出本次数据位置、目标、关键科学参数与输出要求。技能也可依据请求自动匹配；明确指定的任务范围和用户指令始终优先。

例如：

- “使用 $simulation-audit-restart 检查这组计算是否达到目标，列出有效重启点，先准备续算输入。”
- “使用 $trajectory-analysis 比较两组轨迹的氢键，用相同时间窗口和判据。”
- “使用 $dft-labeling 为这些已选构型准备单点标注，保留逐帧来源。”

## 本地安装

在本包目录执行 python install_skills.py，将技能复制到当前 CODEX_HOME 下的 skills；未设置 CODEX_HOME 时使用 ~/.codex/skills。脚本只添加不存在的目录，遇到同名项保留并报告。安装后的技能为独立副本，不依赖本包保留在原位置。

安装位置必须是目标客户端实际支持的技能发现目录；其他客户端或管理员配置使用不同位置时，在 install_skills.py 顶部修改 INSTALL_ROOT。若当前会话仍只显示旧目录，开始新会话或重新加载客户端。

## 环境与任务配置

environment.example.toml 仅展示环境配置的组织方式，不是 Codex 自动加载配置，也不是可直接提交的作业模板。可以复制到本次任务目录、填入真实环境，并在请求中明确该配置位置。

- 环境层：程序命令、环境加载、调度器、资源与软件数据位置。
- 任务层：体系、温度、电势、CV、采样窗口、种子、标签协议等，写入当前任务配置。
- 技能层：工作流程、科学判据、方法选择和输出约定。
- 运行产物：本次实际路径、作业标识和日志，只留在本地任务中。

不将环境配置值回写到可分发技能。不强制统一 conda 环境名、GPU 型号、队列、路径或科学数值。个别软件需要特定依赖时，使用该软件的适配参考。

## 组合与边界

- 建模 → 计算输入 → 作业执行 → 计算审计 → 轨迹整理 → 统计分析 → 图件。
- 候选池 → 代表性选择 → DFT 标注 → 数据集整理 → 模型训练与验证。
- 增强采样准备 → 采样完成检查 → 自由能分析。

各环节通过普通结构文件、CSV、JSON 和明确单位衔接，不要求安装额外工作流框架。相邻技能按请求组合，不能据此自动扩大计算或提交范围。

## 实现方式

技能为操作指导和方法参考，不附带与某个项目绑定的旧脚本、旧输入或旧结果。执行任务时，优先复用用户提供且适用的脚本，或生成最小必要脚本。具体计算、软件版本及数值结果须由当次运行验证；技能安装不表示已完成这些科学验证。
