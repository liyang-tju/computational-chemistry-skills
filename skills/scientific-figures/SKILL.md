---
name: scientific-figures
description: "Create reproducible publication-grade Matplotlib plots and offscreen atomistic renders (ASE/POV-Ray/OVITO) from established data. Deliver editable SVG/PDF vectors, PNG previews, plotting data and standalone scripts without altering scientific definitions."
---
# 科研绘图与结构渲染

将已经过分析核验的数值表与原子结构转化为可复现、可编辑的科研图表与结构渲染图。绘图层只负责准确表达既有数据，绝不在绘图脚本里私自剔除离群点、将缺失值 `NaN` 画成 `0` 或篡改符号/参考基准。

## 开始前确认

- **科学问题与图形选择**：明确每幅图要对比的物理量、单位、分组类别（如不同电势/温度/异构体）及误差棒定义（SD / SE / 95% CI / 重复极差）。
- **样式与输出格式**：项目或用户配置的 Matplotlib `.mplstyle` 路径（未指定时使用默认样式）、尺寸（单栏/双栏宽高）、目标格式（PNG 预览 + 可编辑 SVG/PDF）。
- **结构渲染需求**（如包含结构面板）：源结构帧索引、视角、是否显示晶胞边框、原子着色/半径方案、水分子透明或局部裁剪规则，以及本机实际可用的渲染器（ASE/POV-Ray、OVITO、VMD 等）。

## 工作流程

### 1. 读取数据与核查字段

- 直接读取上游分析输出的完整 CSV/JSON（如 `pmf.csv`, `test_metrics.csv`），在绘图前校验缺失值（保留为 `NaN` 以形成断线或空位，绝不 `fillna(0)`）和不同统计口径/参考类不可混画在同一无区分系列里。
- 若需在现有脚本上微调旧图，先完整读取原脚本与原数据，确认修改后另存新版本。

### 2. 配置 Matplotlib 样式与矢量可编辑性

在 `import matplotlib.pyplot as plt` 之后、创建画布 `plt.subplots()` 之前应用样式配置：
- 优先加载项目配置的样式文件（若未提供则使用 Matplotlib 默认循环色与清晰基线设置，不依赖特定主机私有样式名，也不用无关第三方主题库覆盖用户样式）；
- 仅设置确保**可编辑矢量输出**所必需的字体输出参数（见 [图件与渲染](references/figures-rendering.md)）：
  - `svg.fonttype = "none"`（保留 SVG 文本为真实文字对象而非转曲路径）；
  - `pdf.fonttype = 42`（PDF 嵌入 TrueType 字体）。

### 3. 绘制数据图与复合面板

- 横纵坐标必须同时写明**物理量名称与单位**（如 `Free Energy (eV)`、`z - z_surf (Å)`）；
- 误差棒/阴影带必须在图例或图注中写清含义；
- 仅在确实需要展示跨数量级变化或断轴对比时使用对数坐标、双 y 轴或截断坐标，并在图中明显标注。

### 4. 结构渲染与多面板合成（若适用）

- 按 [图件与渲染](references/figures-rendering.md) 使用可脚本化离屏渲染生成高分辨率透明/白底结构 PNG（记录相机视角、旋转角度、周期镜像扩展与透明度设置）；
- 复合图中嵌入结构面板时，保持矢量曲线/文字在 SVG/PDF 中完全可编辑，并在说明中注明结构面板为高分辨率嵌入位图。

### 5. 实查渲染结果并打包交付

生成图片后实际检查生成的 PNG（核对标签是否裁切、图例是否遮挡数据曲线、色条刻度与单位是否可读），修复排版问题后再交付独立脚本、绘图输入数据表与图像文件（除非用户明确要求交互网页，否则不额外创建网页应用）。

## 按需参考

- Matplotlib 可编辑矢量模板、POV-Ray/OVITO 离屏渲染脚本与裁剪原则：阅读 [图件与渲染](references/figures-rendering.md)。

## 交付产物与验收

1. **成图文件**：`*.png`（高 DPI 预览，如 300–600 dpi）及对应可编辑矢量 `*.svg` / `*.pdf`。
2. **`plot.py`**：顶部集中设置输入路径、样式配置、图幅与输出名，可单命令直接复现。
3. **绘图数据快照**：实际送入绘图的整理后 CSV 表（确保他人无需重跑上游长轨迹即可改图）。
