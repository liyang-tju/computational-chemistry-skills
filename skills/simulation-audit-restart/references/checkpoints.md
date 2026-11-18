# 检查点与时间衔接

## 1. VASP 检查点核对

- **几何与速度（`CONTCAR`）**：
  - 确认 `CONTCAR` 非空且能被 ASE 完整读入；核对原子数、晶胞及 `Selective dynamics` 标志未丢失。
  - MD 续算时检查 `CONTCAR` 坐标块下方是否存在完整速度块；若速度缺失，重新生成温度必须明确标记为新初始化段（不能宣称延续原相空间轨迹）。
- **电子波函数与电荷（`WAVECAR` / `CHGCAR`）**：
  - 仅在原子数、晶胞、`ENCUT`、k 点、`ISPIN` 和 `LNONCOLLINEAR` 兼容时才用 `ISTART = 1` / `ICHARG = 1`。更换体系或明显改变电子协议时请设 `ISTART = 0`。
- **安全停止（`STOPCAR`）**：
  - 需提前优雅结束运行中的作业时，写入 `LSTOP = .TRUE.` 使当前离子步完成后写出完整 `CONTCAR`/`WAVECAR`；随后仍需验证实际退出日志和末结构完整性。

```bash
# 快速检查 VASP 计算目录健康状态
python3 - <<'EOF'
from pathlib import Path
from ase.io import read

outcar = Path("OUTCAR")
contcar = Path("CONTCAR")
text = outcar.read_text(errors="ignore") if outcar.exists() else ""
print("Normal finish:", "General timing" in text)
print("Ionic converged:", "reached required accuracy" in text)
if contcar.exists() and contcar.stat().st_size > 0:
    a = read(contcar)
    print("CONTCAR natoms:", len(a))
else:
    print("CONTCAR empty or missing")
EOF
```

## 2. CP2K 检查点核对

- **匹配文件**：确认最新的 `*-1.restart`（或指定备份 `*-1.restart.bak-*`）与 `*-RESTART.wfn` 完整可读。
- **步数与时间语义**：
  - 检查 `*-1.restart` 中 `&MD / STEP_START_VAL` 与 `&GLOBAL / RUN_TYPE`、以及 `*-1.ener` 和 `*-pos-1.xyz` 的最后完整步号。
  - 在新目录使用 `&EXT_RESTART` 时：延续同一轨迹保持 `RESTART_POS .TRUE.`、`RESTART_VEL .TRUE.`、`RESTART_THERMOSTAT .TRUE.`、`RESTART_COUNTERS .TRUE.`（如为 NPT 再加 `RESTART_CELL .TRUE.` 和 `RESTART_BAROSTAT .TRUE.`）；若切换温度或热浴协议，关闭对应 `RESTART_THERMOSTAT` 并另记新段。
- **容差匹配与尾帧清理**：CP2K 各输出文件写出的浮点时间可能略有舍入，比较时间时用容差（如 `abs(t1 - t2) < 1e-4`）。父段崩溃后 `pos-1.xyz` 末尾若有半帧（行数不足 `natoms + 2`），应在解析合并时丢弃该半帧，保留到最近一个完整 `restart` 步号为止。

## 3. LAMMPS 检查点核对

- **二进制 `restart` vs `data`**：
  - `read_restart` 可恢复原子坐标、速度、image flags、当前 `timestep` 及部分 `fix` 状态（如 `nvt`/`npt` 积分器变量，视具体 LAMMPS 版本文档而定）。
  - `write_data`/`read_data` 不保存多数 `fix` 的内部累积状态与偏置历史。
- **必须重新声明的命令**：即使使用 `read_restart`，输入脚本中仍须重新指定 `fix`（如 `shake`、`nvt`/`npt`、`setforce`、`electrode`）、`dump`、`thermo` 以及不写入 restart 的势函数参数。
- **步数目标**：检查 `log.lammps` 的最后有效步号 $S_0$；使用 `run <S_target> upto` 可避免手算剩余步数出错。

## 4. 增强采样联合续算

对于 MD + PLUMED（如 OPES/Metadynamics）续算，**MD 检查点与偏置状态必须严格对齐**：
- 确认 `COLVAR`、`KERNELS`/`HILLS` 及 OPES `STATE` 文件最后写入的 `time` 与 MD 检查点一致。
- 续算时必须在 `plumed.dat` 中启用 `RESTART=YES`（OPES 配合 `STATE_RFILE=...`），保持相同的 `UNITS`、CV 原子索引和参数；开启全新采样则务必移除旧 `KERNELS`/`STATE` 并关闭 `RESTART`。
