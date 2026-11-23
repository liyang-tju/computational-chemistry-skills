# 动力学与重启

## 1. 常用输入骨架（NVT AIMD 示例）

```text
&GLOBAL
  PROJECT water_slab_nvt
  RUN_TYPE MD
  PRINT_LEVEL LOW
&END GLOBAL

&FORCE_EVAL
  METHOD Quickstep
  &DFT
    BASIS_SET_FILE_NAME  BASIS_MOLOPT
    POTENTIAL_FILE_NAME  GTH_POTENTIALS
    &MGRID
      CUTOFF 500
      REL_CUTOFF 60
    &END MGRID
    &QS
      EPS_DEFAULT 1.0E-12
      EXTRAPOLATION ASPC
      EXTRAPOLATION_ORDER 3
    &END QS
    &SCF
      SCF_GUESS RESTART
      EPS_SCF 1.0E-6
      MAX_SCF 30
      &OT
        MINIMIZER DIIS
        PRECONDITIONER FULL_SINGLE_INVERSE
      &END OT
      &OUTER_SCF
        EPS_SCF 1.0E-6
        MAX_SCF 10
      &END OUTER_SCF
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
      &VDW_POTENTIAL
        POTENTIAL_TYPE PAIR_POTENTIAL
        &PAIR_POTENTIAL
          TYPE DFTD3(BJ)
          PARAMETER_FILE_NAME dftd3.dat
          REFERENCE_FUNCTIONAL PBE
        &END PAIR_POTENTIAL
      &END VDW_POTENTIAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 15.0 15.0 30.0
      PERIODIC XY
    &END CELL
    &TOPOLOGY
      COORD_FILE_NAME init.xyz
      COORD_FILE_FORMAT XYZ
    &END TOPOLOGY
    &KIND O
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-SR-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL

&MOTION
  &MD
    ENSEMBLE NVT
    STEPS 5000
    TIMESTEP 0.5
    TEMPERATURE 300.0
    &THERMOSTAT
      TYPE CSVR
      &CSVR
        TIMECON 50.0
      &END CSVR
    &END THERMOSTAT
  &END MD
  &PRINT
    &TRAJECTORY
      &EACH
        MD 1
      &END EACH
    &END TRAJECTORY
    &CELL
      &EACH
        MD 1
      &END EACH
    &END CELL
    &RESTART
      BACKUP_COPIES 1
      &EACH
        MD 100
      &END EACH
    &END RESTART
  &END PRINT
&END MOTION
```

## 2. 系综、步长与约束要点

- **步长与氢质量**：常规全氢体系建议 `TIMESTEP 0.5` fs；若协议采用重氢质量（如在 `&KIND H` 下设 `MASS 2.014`）配合 `TIMESTEP 1.0` fs，必须在任务说明中显式记录并验证能量/温度稳定性。
- **NPT 与表面体系**：`ENSEMBLE NPT_I` 或 `NPT_F` 适用于三维均匀块体或液体；含真空层的二维 slab 直接使用各向同性/全自由度 NPT 会导致真空层塌缩，除非有明确变胞协议并配合受限自由度。
- **金属电极/导体体系**：需在 `&SCF` 中去掉 `&OT`，改用 `&DIAGONALIZATION` + `&SMEAR` + `&MIXING`（如 `ALPHA 0.2`）+ `ADDED_MOS`。注意金属体系若同时需要 `&OT` 无法进行部分占据。

## 3. `&EXT_RESTART` 语义与状态切换

从前段 `*-1.restart` 续算时，CP2K 的 `STEPS` 在配合 `RESTART_COUNTERS .TRUE.` 时为**累计总步数上限**还是剩余步数需结合 `STEP_START_VAL` 确认（CP2K 中 `&EXT_RESTART` 读取 `STEP_START_VAL` 后，实际运行直到当前步号达到 `STEPS`，即若前段跑到第 2000 步、想再跑 3000 步，则 `STEPS` 应设为 `5000`）。

| 场景 | `RESTART_POS/VEL` | `RESTART_CELL` | `RESTART_THERMOSTAT` | `RESTART_COUNTERS` | `SCF_GUESS` |
|---|---|---|---|---|---|
| 同协议无缝续算 | `.TRUE.` | `.TRUE.`（NPT 时） | `.TRUE.` | `.TRUE.` | `RESTART`（配合 `.wfn`） |
| 切换目标温度/热浴 | `.TRUE.` | 视系综定 | `.FALSE.` | 建议重记新段 | `RESTART`（体系未变时） |
| 换用新初始结构重启 | `.FALSE.` | `.FALSE.` | `.FALSE.` | `.FALSE.` | `ATOMIC`（不可复用旧 `.wfn`） |

## 4. 步号、时间与文件对齐检查

CP2K 的 `*-pos-1.xyz`、`*-1.cell` 和 `*-1.ener` 可能因各自 `&EACH` 频率不同或异常中断留下长度不一致的尾部，**禁止按行号对齐**：

```python
# 核对 pos-1.xyz 与 1.ener / 1.cell 的 step 与 time 是否匹配
import re
steps_xyz = []
with open("proj-pos-1.xyz") as f:
    for line in f:
        m = re.search(r"i\s*=\s*(\d+),\s*time\s*=\s*([0-9.eEdD+-]+)", line)
        if m:
            t_val = float(m.group(2).replace("D", "E").replace("d", "e"))
            steps_xyz.append((int(m.group(1)), t_val))
print("xyz frames:", len(steps_xyz), "first/last:", steps_xyz[0], steps_xyz[-1])
```

- 比较浮点时间请用容差（如 `abs(t1 - t2) < 1e-4`），不要用精确字符串或 `==` 比较。
- 仅对数值字段做 `D -> E` 替换，切勿对整行或含元素 `Dy` 的行做全局替换。
- 异常中断后，若 `*-pos-1.xyz` 末尾存在半帧（行数不足 `natoms + 2`），合并或续算前须丢弃半帧；若能量/结构在崩溃前已发生畸变，应回退到崩溃前的健康备份 `*-1.restart.bak-*` 并核对 `STEP_START_VAL` 与 `*-1.ener` 一致。
- 验收标准：检查输出末尾是否存在 `PROGRAM ENDED AT`、能量/温度无剧烈跳变、`MAX_SCF` 未持续饱和，且末尾 `.restart` 与最后一帧完整轨迹步号一致。
