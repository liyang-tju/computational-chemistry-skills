# 阶段 5：委员会不确定性采样、隔离区与 SOAP 二次剪枝

## 1. 委员会生产驱动与实时日志

在长时生产模拟（如自由 MD、伞形采样或 PLUMED `OPES_METAD_EXPLORE`）中，利用多随机种子委员会模型（如 4 个 `.model` 并行计算平均力推进轨迹），按固定步频原子地向 `uncertainty.csv` 写出一行记录（同时对齐输出 `trajectory.extxyz` 帧头中的 `step=` 与 `time_fs`）：
- 各模型总能预测：`energy_seed_<s1>_eV`, `energy_seed_<s2>_eV`, ...
- **仅统计可动原子（Mobile Atoms）的力分歧**：忽略 `FixAtoms` 固定基底原子（其力不参与动力学演化且外推噪点可能干扰判断），分别记录可动原子的最大原子力标准差 `force_std_max_atom_mobile_eV_A` 与均方根分歧 `force_std_rms_mobile_eV_A`：
  $$\sigma_{F, i} = \left\| \operatorname{std}_{m}\bigl(\mathbf{F}_i^{(m)}\bigr) \right\|_2, \quad \sigma_{F,\max}^{\text{mobile}} = \max_{i \in \text{mobile}} \sigma_{F,i}$$

## 2. 为什么相对能量分歧必须扣除“零点基线偏移”（`dE_cent`）

不同随机种子训练出的模型在绝对能量零点（及总和偏置）上往往存在毫电子伏至数十毫电子伏的**常数值漂移**。若直接对各模型总能求标准差 $\operatorname{std}_m(E^{(m)})$，即便所有模型势能面形状完全一致，也会误报极高的假能量不确定性。

**标准做法（Baseline-Centered Energy Std）**：
1. 在每条运行轨迹前段平稳区（例如平衡/早期 `step <= BASELINE_MAX_STEP`，至少几百至上千步样本）计算各模型相对于委员会均值的中位零偏向量：
   $$\mathbf{b} = \operatorname{median}_{t \in \text{phase1}} \Bigl(\mathbf{E}_t - \overline{E}_t\Bigr)$$
2. 随后每步计算扣除基线漂移后的中心化能量标准差：
   $$\sigma_{E,\text{cent}}(t) = \operatorname{std}_{m}\Bigl((E_t^{(m)} - \overline{E}_t) - b^{(m)}\Bigr)$$

## 3. 双端门槛控制、崩溃隔离区（`quarantine`）与冷却去重

不把全部高分歧帧都塞去算 DFT，必须建立四道闸门过滤无效数据与爆炸构型：

1. **多指标下限触发（OR 关系，示例典型量级）**：
   - $\sigma_{F,\max}^{\text{mobile}} \ge 0.30\ \text{eV/\AA}$ **或** $\sigma_{F,\text{rms}}^{\text{mobile}} \ge 0.060\ \text{eV/\AA}$ **或** $\sigma_{E,\text{cent}} \ge 0.070\ \text{eV}$；
   - 以上数值随体系与原子数标度应经验证集误差相关性预标定，不盲目硬套。
2. **非物理崩溃上限 $\rightarrow$ 进 `quarantine/` 隔离**：
   - 一旦满足 **极高分歧上限**（如 $\sigma_{F,\max}^{\text{mobile}} > 1.50\ \text{eV/\AA}$）**或** **原子过度靠近崩溃**（`min_mic_dist < 0.75 Å`），说明该构型已经严重外推崩溃或出现非物理碰撞；
   - **绝不送去算 DFT**（往往 SCF 不收敛且无训练价值），而是记录到 `quarantine/quarantine.csv` 与 `quarantine.extxyz` 供事后诊断体系哪处势能面缺壁垒，并持续推进筛选扫描。
3. **时间冷却（`MIN_COOLDOWN_FS`）**：同条运行轨迹连续两次采集间隔不少于冷却时间（如 `150 fs`），避免一个持续数皮秒的高能垒事件把同一个局部构象连抓几十帧。
4. **结构指纹全局去重与原子/长度自检**：通过与 `trajectory.extxyz` 及 `uncertainty.csv` 核对步号与时间一致（只解析以完整换行结尾的已落盘帧，防读写竞争），核对原子数与固定原子数，再与已收录集合校验对齐后的几何 SHA-256 指纹去重。

## 4. 预算受限时的 SOAP 二次剪枝（`soap_prune`）

当长时探索产生过多待标注 AL 候选帧（例如未被 DFT 领取的候选 `unclaimed_pending > SOAP_PRUNE_TRIGGER`，或逼近本轮总预算上限 `MAX_TOTAL_AL_FRAMES`）时，用与阶段 2 **完全一致的分角色 SOAP 描述符**执行二次 FPS 剪枝：

1. **构建参考种子集合**：把本轮**已经验收完成或已被 DFT 领取在算**的 AL 帧作为参考点 `ref_feats`（也可按需纳入初始库）；
2. **基于余弦距离 FPS 裁半保留**：对所有尚未领取的候选帧 `cand_feats` 计算到 `ref_feats` 的最近距离，再按贪心最远点选出目标保留比例（如保留 50%），优先保留既满足不确定性门槛又最远离已有探索空间的构型；
3. **非破坏式加锁标记**：使用 `claim.lock` 与总状态锁防止与 DFT worker 并发争抢，对被剪枝帧写 `pruned.json` 标记退出候选池并释放预算名额，原始结构与元数据保留可查；未触发剪枝阈值前先保留原始顺序等待分配。

完成筛选与（按需）剪枝后，在 `frames/<al_index>/` 下生成去标签的 `input.extxyz`、元素排序 `POSCAR`、`meta.json`（含 `order` 与 `science` 摘要）与 `manifest.csv`，随后无缝衔接阶段 3/6 的 DFT 重标与并库。
