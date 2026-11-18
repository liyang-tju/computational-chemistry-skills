# 波函数与 Multiwfn

## 1. 输入格式选择与转换核对

Multiwfn 需要包含**波函数轨道系数、基组与占据数**的文件才能算真实电子密度、ESP、轨道、键级或弱相互作用；仅有 `.xyz`/`.pdb` 几何只能做近似的原子密度叠加（promolecular）。

| 量化软件 | 推荐导出格式 | 常见生成与核对要点 |
|---|---|---|
| **Gaussian** | `.fchk` / `.wfx` | `formchk job.chk job.fchk`；注意 `.wfx` 对赝势核电荷（ECP）记录更明确 |
| **ORCA** | `.molden.input` / `.wfx` | `orca_2mkl job -molden`；部分版本或泛函转 Molden 需注意球谐/笛卡尔基组标记及 Multiwfn 加载提示 |
| **CP2K** | `.molden` | 确认打印了完整 MO 与基组信息，且加载后检查总电子数与多重度 |

- 每次转换后先在终端查看 Multiwfn 载入文件开头的打印摘要：核对**原子数、总电子数、$\alpha/\beta$ 电子数与基函数总数**是否与原量化输出一致；若出现影响当前分析的警告（如缺少基组或占据异常），停止批处理并排查格式转换。

## 2. 无界面（noGUI）批处理模板

Multiwfn 版本更新偶尔会调整子菜单编号，**批量前务必先用 1 个小样本实测确认当前版本的交互按键序列**：

```bash
# 1. 复制一份局部 settings.ini 到当前工作目录（不改动软件安装目录的全局配置）
# 常见调整：设置 nthreads、isilent=1（关闭多余交互提示）等

# 2. 将验证通过的交互按键写入 answers.txt，例如（菜单编号以实测版本为准）：
cat <<'EOF' > answers.txt
7      # 例：Population / atomic charge 模块（请按实际版本菜单核实）
12     # 例：RESP 等具体子菜单
0
q
EOF

# 3. 无交互执行并保留完整日志
Multiwfn mol.fchk < answers.txt > multiwfn.log 2>&1
```

## 3. 常用分子性质的定义边界

- **电荷方案不可直接混比**：Mulliken、NBO、Hirshfeld、CM5、ADCH、CHELPG、MK-ESP 与 RESP 基于不同物理划分与拟合策略，绝对数值不可跨方法混入同一张对比表。
- **分子体积**：区分电子密度等值面体积（如 $\rho = 0.001\,\text{a.u.}$ 等值面包裹体积，Multiwfn 常用 Monte Carlo 积分或网格法，需注明网格间距/采样点数及单位 $\text{Bohr}^3$ vs $\text{\AA}^3$）与基于固定原子半径的 vdW/溶剂空腔体积。
- **弱相互作用（RDG / NCI / IGMH）**：分别保留三维格点 `.cub` 输出（供 VMD/PyMOL 渲染）与散点图数值表 `output.txt`，大网格任务在计算节点申请充足内存与线程。
