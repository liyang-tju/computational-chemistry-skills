---
name: vasp-calculations
description: "Prepare VASP geometry optimizations, single points and AIMD with explicit scientific settings and compatible restart inputs. Use for VASP input generation and result handoff, not installation or general queue management."
---
# VASP 计算准备

将结构与科学协议整理成可检查的优化、单点或 AIMD 输入。运行环境与并行配方从当前安装和集群配置获取。

## 工作流程

1. 确认任务模式、目标结构、功能性设置和已有结果。读取当前用户或项目明确的默认值，不能因为参考模板更严格就静默替换精度。
2. 列出泛函、赝势、截断、k 点、自旋、展宽、色散、溶剂/偶极处理、电子数和约束。区分科学参数与运行资源。
3. 检查 POSCAR 的元素顺序、计数、晶胞和选择性动力学约束。按明确的赝势选择组装 POTCAR，核对标识、顺序及适配关系；保护既有文件。
4. 根据模式生成 INCAR/KPOINTS。分阶段优化只在任务需要时使用，明确每一阶段改变的精度及进入下一阶段的规则。
5. 确认当前二进制支持所需功能，再根据版本、构建与已验证配方设置 GPU/MPI、KPAR、NCORE 等；不将某台机器的布局写死。
6. 对重启明确几何与电子文件来源、兼容性及读入选项。新输入和旧结果分目录，重新计算范围按用户要求执行。
7. 核对输入语义、必需文件和脚本语法。提交只在已授权时进行；报告时分别说明准备、启动、电子收敛、离子收敛或 MD 完成。

## 按需参考

- 单点、优化和 AIMD 的区别：读取 [计算模式](references/modes.md)。
- 赝势、k 点与并行设置：读取 [输入与运行适配](references/inputs-runtime.md)。

## 输出

POSCAR、INCAR、KPOINTS、必要的本地 POTCAR、作业脚本及参数说明。赝势文件不进入公开技能包；只有用户需要的计算目录才包含合法可用的赝势数据。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

