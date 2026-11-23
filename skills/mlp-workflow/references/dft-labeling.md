# 阶段 3 & 6：DFT 批量单点标注、试跑定参与回流并库

## 1. 上线前必须先跑小批量 `pilot` 对照试跑

切勿直接对上千帧盲目提交全量生产作业。先抽取少数代表帧（覆盖最大原子数体系检验内存上限，以及各主要组分/反应态，典型 6–8 帧）在不同规格计算节点/并行配置（如 `KPAR`/`NCORE`/`NSIM`）上跑一次 `pilot`：
- **内存与 OOM 安全线**：读取调度器 `cgroup` 实际内存峰值（注意单帧 `OUTCAR` 估测内存仅代表单个 MPI rank，往往大幅低估整体节点峰值），确认 `memory.peak / limit_bytes` 留足安全余量（典型 `< 85%`），确认无 OOM 事件；
- **跨配置数值一致性**：同一帧在不同节点规格上跑完后硬核比对：
  - 总能差 $|\Delta E| \le 1\ \text{meV}$
  - 最大原子受力向量差 $\max \|\Delta \mathbf{F}_i\| \le 0.01\ \text{eV/\AA}$
- **核定吞吐**：基于实测总耗时计算各体系的“帧 / 节点小时”，估算全量耗时再生成生产任务队列。

## 2. 科学协议锁定与 `POSCAR` 元素重排机制

- **冻结 `science` 摘要**：将 `INCAR` 物理参数、`KPOINTS` 网格、VASP 版本与各元素 `POTCAR` 的 SHA-256 共同编码进协议校验哈希；任何参数修改必须升版隔离，不能混标。
- **稳定排序与逆排还原**：
  - 将每帧按元素符号稳定排序后写入 `POSCAR`（便于同一组元素共用少数固定顺序的 `POTCAR`，校验每帧预期总价电子数 `nelect = sum(ZVAL)`）；
  - 在 `queue.json`（首批标注）或 `meta.json`（AL 第 6 步重标）中保存精确的 **`order` 索引数组**、`poscar_sha256`、`potcar_sha256`；
  - 回收 `REF_forces` 时通过逆排列把每个力向量精确还原到原始 `input.extxyz` 的原子序号上，再反算与 `input.extxyz` 坐标、`cell`、`pbc`、`move_mask` 的一致性（误差容限 `~5e-9`）。

## 3. 并发队列调度与容错目录设计

- **物理分离的尝试目录**：每帧目录（如 `frames/0001/`）内建独立的 `primary/`，失败或超时重跑建独立 `retry_v2/`，每次尝试都保有一套完整的自包含 `POSCAR`/`POTCAR`/`KPOINTS`/`INCAR` 与输出日志；**原始计算目录永不原地覆写**。
- **文件锁与防重复领取**：多节点/多作业并发 worker 采用基于 `flock` 的共享领取锁，若该帧目录已存在通过验收的 `accepted.json`，直接跳过；若某尝试异常退出，保留现场日志并按预置稳健参数（如切到 `ALGO = Normal` / `All`、调小 `AMIN`/`BMIX`、增大 `NELM`）进入独立重试通道。

## 4. 逐帧验收、原始 DFT 力与 SCF 质量审查

绝不仅凭作业退出码 `0` 判通过！必须逐帧检查：
1. **收敛与有限性硬条件**：正常走完、最终电子步数 `< NELM`（未撞电子步上限）、`REF_forces` 形状 `(N, 3)` 且所有能量与力有限（无 `NaN`/`Inf`）；
2. **能量与原始力口径（关键陷阱）**：
   - 在 Gaussian 展宽（如 `ISMEAR = 0`, `SIGMA = 0.05`）等金属/电化学体系中，**VASP 的解析力直接对应自由能（`TOTEN`），而不是外推零展宽能量 `energy(sigma->0)`**——主训练能量 `REF_energy` 与 `REF_forces` 必须保持热力学配对一致（可另行记录 `energy_sigma0_eV` 作参考）；
   - 使用 ASE 读取含 `Selective dynamics` 的 `OUTCAR` 时，**必须显式传入 `apply_constraint=False`** 获取全原子真实 DFT 受力（包括基底固定层铜原子等，绝不把被 `FixAtoms` 置 `0` 的约束力写进训练标签！）。
3. **软质量复核队列（`review.csv`）**：即使未撞 `NELM`，也应自动标记高风险帧以便人工/脚本抽查：
   - 电子步数偏高（如 `scf_steps >= 250`）；
   - 后期 SCF 出现能量突跳（如第 20 步之后单步能量上升超过 `0.10 eV`）。

## 5. 原子级导出校验与主动学习第 6 步并库

- 使用临时文件写完后先逐帧复读还原比对（核对 `dataset_index`、原子数、坐标、`move_mask`、`REF_energy`、`REF_forces`），通过后再原子替换目标 `labeled.extxyz` 并写出含全部帧哈希与待复核清单的 `verification.json`。
- **第 6 步主动学习帧回流**：使用与首批完全相同的 `science` 协议哈希与并网配置完成重标后，单独验证产出 `al_labeled.extxyz`、`al_results.csv`，随后与初始 `labeled.extxyz` 安全合并写出 `merged_labeled.extxyz`，投入下一代委员会模型训练。
