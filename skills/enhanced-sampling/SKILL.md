---
name: enhanced-sampling
description: "Design and prepare CVs, constraints, umbrella windows and PLUMED OPES inputs for supported MD engines. Use for sampling setup and bias troubleshooting; PMF reconstruction belongs to free-energy analysis."
---
# 增强采样准备

把明确的反应问题转为可执行的 CV、约束或偏置采样方案。采样输入准备与自由能重建分别处理。

## 工作流程

1. 明确反应物、产物、潜在中间态、希望采样的变化及需要保持的物理条件。识别 CV 无法区分的构象或旁路反应。
2. 从实际初始结构生成原子组，记录索引基数、周期边界、单位和选择规则。发生质子交换时考虑固定原子身份是否仍适合目标 CV。
3. 根据任务选择约束动力学、umbrella 或 OPES 等方法，记录方法特有参数。不要由一个通用模板自动决定壁势、窗口宽度或 barrier。
4. 对窗口或重复目录保留共同协议与各自起点。拉伸得到的初态是否需预优化、平衡由具体协议决定。
5. 检查 CV 数值与极限行为；力相关的自定义 CV 还需核对导数与连续性。只解析语法不能证明施加的偏置力正确。
6. 按所用接口验证输入，必要时在独立临时目录进行获准的小型初始化。单独的 PLUMED 检查与 ASE/引擎接口检查分别记录。
7. 新采样与恢复采样明确分开。恢复时匹配 MD 步号、温度、CV 定义和偏置历史；新采样不继承旧核或旧状态文件。
8. 输出预期观察量与失败判据，提交依当前授权。不要把采样方案准备完成说成已得到收敛自由能。

## 按需参考

- PLUMED、OPES 与接口：读取 [偏置语义](references/plumed-opes.md)。
- 质子/离子 Voronoi CV：仅相关任务读取 [反应性 CV](references/reactive-cv.md)。

## 输出

plumed.dat 或引擎约束输入、CV 定义、窗口/重复清单、初态映射和 bias-protocol.json。

## 使用约定

- 依赖路径、环境名称、调度资源和科学参数从当前请求、项目文件或运行配置获取；只读探测缺失的环境信息，关键科学选择不明确时再询问。
- 保留源数据与既有结果，使用新的输出位置；提交、取消作业或破坏性操作须在当前授权范围内进行。准备输入本身不等于授权提交。
- 生成的脚本采用顶部配置、清楚的输入输出和相对资源引用。当前运行的本机路径可以记录在运行产物中，不回写到可分享的技能文件。

