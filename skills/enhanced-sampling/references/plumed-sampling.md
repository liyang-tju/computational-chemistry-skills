# PLUMED 与 ASE/MD 增强采样配置（Umbrella / WT-Metad / OPES / OPES Explore）

核心开源仓库：[plumed/plumed2](https://github.com/plumed/plumed2)、[i-pi/i-pi](https://github.com/i-pi/i-pi)。

## 1. PLUMED 通用基础与易错陷阱

1. **显式单位声明 `UNITS`**：PLUMED 默认采用 `nm / ps / kJ/mol`。凡与 ASE、VASP 或 eV/Å 力场联用时，**文件第一行必须显式声明**，并确认传给偏置动作的 `BARRIER`、`HEIGHT`、`KAPPA`、`TEMP` 与该单位制严格匹配：
   ```plumed
   UNITS LENGTH=A TIME=fs ENERGY=eV
   ```
2. **原子序号与 PBC 处理**：
   - `ATOMS=...` 一律使用 **1-based 编号**；若先用 ASE 筛选原子再写 `plumed.dat`，必须全部 `idx + 1`。
   - 跨周期边界的大分子或吸附质内部键距、质心/配位组合，必要时先用 `WHOLEMOLECULES` 拼接，或谨慎排查 PBC 截断；不要无条件盲目加 `NOPBC`。

## 2. 伞形采样（Umbrella Sampling）与 `MOVINGRESTRAINT`

PLUMED `RESTRAINT` 施加如下谐波偏置（注意其采用 $\frac{1}{2}\kappa$ 约定）：

$$V(s) = \frac{1}{2}\kappa (s - s_0)^2$$

```plumed
UNITS LENGTH=A TIME=fs ENERGY=eV
d: DISTANCE ATOMS=46,48
umb: RESTRAINT ARG=d AT=2.00 KAPPA=15.0
PRINT ARG=d,umb.bias FILE=COLVAR STRIDE=20
FLUSH STRIDE=100
```

- **窗口与弹性常数估算**：单窗口热涨落宽度约为 $\sigma_{\text{harm}} \approx \sqrt{k_B T / \kappa}$。若需相邻窗口明显重叠，窗口间距 $\Delta s_0 \lesssim (1.0\text{–}1.5)\,\sigma_{\text{harm}}$；高能垒区可加密窗口或增大 $\kappa$。
- **拉伸 MD（SMD）**：用 `MOVINGRESTRAINT` 随 `STEP` 线性移动 `AT`，与缓慢牵引（需检查正反向耗散与 Jarzynski 平均适用性）区分开静态平衡窗口。

## 3. Metadynamics 与温和元动力学（`METAD` / WT-Metadynamics）

在长时采样与可控制偏置收敛场景下，优先选用带 **`BIASFACTOR` + 网格加速 + `CALC_RCT`** 的 Well-Tempered Metadynamics：

```plumed
UNITS LENGTH=A TIME=fs ENERGY=eV
cv: DISTANCE ATOMS=46,48

metad: METAD ARG=cv ...
  PACE=200
  HEIGHT=0.02
  SIGMA=0.05
  BIASFACTOR=10.0
  TEMP=300
  GRID_MIN=1.0 GRID_MAX=5.0 GRID_BIN=400
  CALC_RCT
  FILE=HILLS
  RESTART=NO
...

PRINT ARG=cv,metad.bias,metad.rct FILE=COLVAR STRIDE=50
FLUSH STRIDE=100
```

- **参数与陷阱**：
  - `BIASFACTOR`（$\gamma = (T + \Delta T)/T$）：未指定则退化为非温和（standard）Metadynamics（山丘高度不衰减，易过填或漂移）。催化/溶液反应常见 $\gamma \approx 6\text{–}20$，使 $\gamma k_B T$ 接近预估能垒量级。
  - `SIGMA`：略小于未偏置势阱内 CV 的标准差（如 $\sim 0.3\text{–}0.5\,\sigma_{\text{well}}$）。
  - `GRID_MIN` / `GRID_MAX`：必须设置且与墙势留出余量，否则长时间后逐高斯求和拖慢每步动力学且易越界报错。
  - `CALC_RCT`：输出 `metad.rct`（$c(t)$），是后续进行时间依赖重加权的必需量（详见 [estimators.md](estimators.md)）。
  - **续算**：改为 `RESTART=YES` 并保留 `HILLS`，确认与上一阶段末步步数衔接。

## 4. `OPES_METAD` 与 `OPES_METAD_EXPLORE` 选型与配置

PLUMED 2.8+ OPES 模块通过核密度自适应估算目标分布，显著减少高维空间参数调优负担；两类变体核心差异如下：

| 特性 | `OPES_METAD` | `OPES_METAD_EXPLORE` |
|---|---|---|
| **内部估算量** | 在线估算**无偏分布 $P(s)$**，再映射至目标分布 | 直接在线估算**温和目标分布 $p^{\text{WT}}(s)$** |
| **偏置行为** | 进入准稳态后偏置平滑收敛 | 偏置起伏更显著，类似传统/温和 Metadynamics |
| **适用场景** | 能垒量级已知、CV 区分度良好，追求快速收敛自由能曲线 | **未知能垒**、初步探索多条路径或测试尝试性/可能退化的 CV |
| **重加权收敛** | 快；`opes.rct`/`opes.zed` 很快进入稳态 | 较慢；需丢弃更长的初始探索瞬态后方可用于重加权 |

**标准模板（以 `eV / A / fs` 为例）：**

```plumed
UNITS LENGTH=A TIME=fs ENERGY=eV
cc: DISTANCE ATOMS=46,48
co1: DISTANCE ATOMS=46,47

# 需要保守收敛 FES 时用 OPES_METAD；探索未知能垒/多路径时可换 OPES_METAD_EXPLORE
opes: OPES_METAD_EXPLORE ...
  ARG=cc
  TEMP=300
  PACE=400
  BARRIER=0.6
  # BIASFACTOR=15.0        ! 可选：不写则按 BARRIER/(k_B*T) 自动设定
  SIGMA_MIN=0.05
  EXCLUDED_REGION=step(cc-4.5)
  FILE=KERNELS
  STATE_WFILE=OPES_STATE
  STATE_WSTRIDE=4000
  RESTART=NO
...

PRINT ARG=cc,co1,opes.bias,opes.rct,opes.zed,opes.neff,opes.nker FILE=COLVAR STRIDE=50
FLUSH STRIDE=100
```

关键注意事项：
1. **`BARRIER` 单位陷阱**：`BARRIER` 按 `UNITS` 的 `ENERGY` 解释。若设为 `ENERGY=eV`，`0.6` 代表 `0.6 eV`（约 `58 kJ/mol`）；若错误按 `kJ/mol` 填入 `60.0`，则等于施加了 `60 eV` 的极强偏置并立刻炸飞体系！
2. **`EXCLUDED_REGION` vs `UPPER_WALLS`/`LOWER_WALLS`**：
   - `OPES` 家族内置 `EXCLUDED_REGION` 可阻止在该区域放置压缩核，同时不干扰边界附近的概率归一估计；需要硬性限制物理构型范围（防止溶剂扩散过远或断键解离）时仍应配合 `UPPER_WALLS` / `LOWER_WALLS`（注意重加权前扣除或避开高墙势区）。
   - `METAD` 与 `RESTRAINT` 使用 `LOWER_WALLS` / `UPPER_WALLS`。
3. **重启与状态对齐**：续算除保留 `KERNELS`、`COLVAR` 并设 `RESTART=YES` 外，OPES 建议同时用 `STATE_WFILE=OPES_STATE` 与 `STATE_RFILE=OPES_STATE` 恢复压缩核与 $Z_n$ 状态；续算前校验 `COLVAR`、`KERNELS`、`OPES_STATE` 时间戳与步数完全同步。

## 5. 各引擎接口与提交前离线验收

- **ASE**：`ase.calculators.plumed.Plumed(calc, plumed_lines, timestep=dt_fs*units.fs, atoms=atoms, kT=T*units.kB, log=...)`。
  - **多行语法坑**：传给 ASE 的 `plumed_lines` **严禁包含尾随空白的 `...` 续行符**，也避免与 ASE 不一致的换行片段；每条指令尽量写成单行或干净的多行块。
  - **模块支持**：运行前检查环境变量 `PLUMED_KERNEL` 所指共享库是否已编译 `opes` 模块（较老 PLUMED 版本缺省未带 OPES）。
- **GROMACS**：`gmx mdrun -s topol.tpr -plumed plumed.dat`。
- **LAMMPS**：`fix pl all plumed plumedfile plumed.dat outfile plumed.log`（确认已编译 `PLUMED` 包与单位一致）。
- **CP2K**：`&MOTION -> &FREE_ENERGY -> &METADYN -> USE_PLUMED .TRUE.` + `PLUMED_INPUT_FILE ./plumed.dat`（注意 CP2K 与 PLUMED 单位默认换算，仍建议检查首帧 `COLVAR` 与 `driver` 一致性）。
- **提交前 `plumed driver` 离线自检**：
  1. 用静态结构或短轨迹运行 `plumed driver --plumed plumed.dat --ixyz init.xyz`，确认无语法报错、无未知关键字、首帧 CV 数值与预期几何一致。
  2. 对 `METAD` / `OPES_METAD` / `OPES_METAD_EXPLORE`、`RESTRAINT` 与墙势做 `kT` / 导数与作用力方向检查（参见 [reactive-cv.md](reactive-cv.md) 的有限差分验证）。
