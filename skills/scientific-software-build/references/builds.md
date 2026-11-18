# 构建适配

## 1. VASP 与补丁构建

- **区分三个核心二进制**：每次按 `makefile.include` 编译都会在 `bin/` 下生成对应目标：
  - `vasp_std`（通用复数版）
  - `vasp_gam`（Gamma-only 实数加速版）
  - `vasp_ncl`（非共线自旋 / SOC 版）
  编译与验收时须逐一说明实际构建和通过测试的变体。
- **补丁与源码隔离**：原版、VTST、VASPsol、电化学/恒电势补丁各自使用独立源码副本或明确标签目录，记录补丁应用顺序与修改文件（如 `src/.objects` 与 `main.F`），不假定跨主版本（如 5.4.4 vs 6.4.x）补丁通用。
- **常见依赖坑**：
  - `makefile.include` 中的 `CPP_OPTIONS`、`FFTW` 路径、`QD`/`NCCL`/GPU `cc` 架构须与当前加载模块一致。
  - 若开启 OpenACC（NVHPC），确保 `mpif90 -show` 指向的确实是与 NVHPC 兼容的 MPI（如 OpenMPI + NVHPC），而非系统默认 GCC 的 `mpif90`。

## 2. LAMMPS 与可选 Package

使用 CMake 构建可清晰追踪启用模块：

```bash
cmake -S cmake -B build \
  -D CMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
  -D BUILD_MPI=ON \
  -D PKG_MOLECULE=ON \
  -D PKG_KSPACE=ON \
  -D PKG_RIGID=ON \
  -D PKG_EXTRA-FIX=ON \
  -D PKG_ELECTRODE=ON \
  -D PKG_PLUMED=ON
cmake --build build -j 8
cmake --install build
```

- 编译后运行 `lmp -h` 确认 `Installed packages` 与所需 `Pair styles` / `Fix styles` / `KSpace styles` 确实在列表中；若缺少某个包（如 `ELECTRODE` 或 `ML-MACE`），重复跑同一套默认编译不会凭空生成，必须显式开启对应 CMake `-D PKG_*=ON` 并确认其外部库依赖。

## 3. CP2K 与 PLUMED

- **PLUMED 自定义 Action**：如任务依赖自定义 `LOAD` 或外部扩展 action（如特定反应性 Voronoi CV），先在源码树和已编译 `plumed info --version` / `plumed kt` 中确认该 action 确实存在。
- **CP2K + PLUMED 联动**：确认 CP2K 编译时链接的是预期路径的 `libplumedKernel.so`，并检查 `PLUMED_KERNEL` 环境变量在运行时指向同一版本，避免加载错旧版系统 PLUMED。

## 4. MPI / GPU 运行时一致性检查

- **ABI 匹配**：编译阶段 `mpicc`/`mpif90` 与运行阶段 `mpirun`/`srun` 必须来自同一套 MPI 实现；混用 MPICH 与 OpenMPI 或跨主版本会导致段错误或静默降级为多份独立单进程（所有 rank 都在打印 `rank 0`）。
- **GPU 路径实测**：登录节点通常看不到 GPU，可在计算节点提交 10 秒冒烟测试，检查日志中是否确实输出设备名称和 GPU offload 统计，切勿仅凭链接了 `libcudart` 就认为运行走了 GPU 加速。
