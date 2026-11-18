# 图件与结构渲染

## 1. Matplotlib 可编辑科研绘图骨架

```python
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

# 配置区（按当前项目填入）
DATA_CSV = Path("pmf.csv")
MPL_STYLE = ""          # 若无项目样式文件，留空使用默认样式
OUT_PREFIX = Path("fig_pmf")

# 在创建画布前应用样式，且保留 SVG/PDF 文本可编辑性
if MPL_STYLE:
    plt.style.use(MPL_STYLE)
mpl.rcParams["svg.fonttype"] = "none"
mpl.rcParams["pdf.fonttype"] = 42

df = pd.read_csv(DATA_CSV)
fig, ax = plt.subplots(figsize=(5.5, 4.0), constrained_layout=True)

for label, grp in df.groupby("condition", sort=False):
    ax.errorbar(
        grp["cv_A"], grp["pmf_eV"], yerr=grp["se_eV"],
        marker="o", markersize=4, capsize=2.5, label=label
    )

ax.set_xlabel(r"Reaction Coordinate $\xi$ ($\mathrm{\AA}$)")
ax.set_ylabel(r"Free Energy $\Delta F$ (eV)")
ax.legend(frameon=False)

fig.savefig(f"{OUT_PREFIX}.png", dpi=400)
fig.savefig(f"{OUT_PREFIX}.svg")
fig.savefig(f"{OUT_PREFIX}.pdf")
plt.close(fig)
```

- 仅当当前系统字体支持时使用指定字体；禁止自动从个人目录打包有版权限制的商业字体到可分享技能包。
- 避免通过手动堆叠几十行 `rcParams` 去覆盖用户已经提供的 `.mplstyle`。

## 2. 原子结构离屏渲染要点

在无图形界面的服务器/计算节点上，使用可脚本化工具（ASE/POV-Ray、OVITO Python、VMD `-dispdev text`）进行离屏渲染：

### ASE + POV-Ray 固定视角示例
```python
from ase.io import read, write

atoms = read("snapshot.extxyz")
# 显式固定旋转角、画布宽与投影，保证多图对比视角严格一致
write(
    "render.pov",
    atoms,
    rotation="-75x,15y,0z",
    show_unit_cell=2,
    radii=0.85,
    povray_settings=dict(
        canvas_width=1200,
        transparent=True,
        display=False,
    ),
)
# 若环境已安装 povray，ASE 也可直接输出 .png（视 ASE 版本或调用 povray +W1200 +H... +UA）
```

- **水分子与遮挡处理**：为了看清界面活性位点，可以对前层无关水分子设置半透明或仅显示距吸附物指定半径内的局域水壳层，但**必须在图注中如实说明“隐藏/半透明了远离反应位点的体相溶剂”**，严禁为追求美观而偷偷删掉关键配体、反离子或改变周期重复显示比例。
- **报告范围**：在无显示器的离屏环境生成图片后，用图片查看/读取检查确认内容、裁切、颜色和透明度真实正确，不要只凭渲染进程退出码为 0 就断言图像完美。
