---
name: electronic-properties
description: "Analyze work functions, dipoles, electrostatic profiles, charge differences, Bader and Multiwfn quantities. Select inputs with sufficient electronic information and record units, signs and reference conventions."
---
# 电子结构与波函数分析

先判断所求物理量需要哪些电子信息，再选择数据与工具。几何文件不能代替含轨道或电子密度的输入。

## 工作流程

1. 明确性质、输入阶段、几何、电荷、自旋、周期性和电子收敛情况。确认所需波函数、势场或密度确实属于目标计算。
2. 对周期体系根据 [周期电子性质](references/periodic.md) 处理功函数、偶极、电势剖面、电荷差分和 Bader。
3. 对分子或 Multiwfn 根据 [波函数分析](references/wavefunction.md) 选择文件、功能与当前版本实际交互。
4. 明确符号、单位、坐标方向和参考零点。带电体系偶极、势能参考与不同程序定义需特别区分。
5. 在独立输出目录操作，不覆盖源波函数或全局设置。大网格、拓扑分析和批量计算使用合适资源。
6. 保存可重复的命令或输入序列、参数与数值输出；只有在实际输出有效后报告完成。
7. 比较不同结构或条件时保留几何来源、计算协议和采样类别。性质相关性不自动代表因果关系。

## 输出

性质表、必要的 profile/cube 文件、分析日志及可复用脚本或交互输入。原始授权软件文件、个人路径和认证信息不加入可分享技能。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

