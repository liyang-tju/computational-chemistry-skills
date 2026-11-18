---
name: scientific-software-build
description: "Inspect compiler, MPI and GPU toolchains, prepare isolated builds or patched variants of VASP, CP2K, LAMMPS and PLUMED, and validate actual runtime execution. Use for build/link issues; routine simulation setup is separate."
---
# 科学软件构建与运行验证

为 VASP、CP2K、LAMMPS、PLUMED 等计算化学软件构建可追溯的编译与运行环境，明确源码版本、补丁来源、工具链配置及目标计算节点上的实际功能验证。

## 开始前确认

- **目标软件与功能**：软件名称与版本、需要启用的模块/补丁（如 VTST、VASPsol、LAMMPS `ELECTRODE`/`PLUMED`/`KOKKOS`、CUDA/OpenACC 加速）。
- **源码与权限**：源码包所在位置（受许可限制的商业源码如 VASP 由用户合法提供，严禁将源码或授权信息写入可分享技能仓库）。
- **目标硬件架构**：编译节点与运行节点的 CPU 架构（如 AVX2 / AVX-512）及 GPU 型号与驱动（登录节点无 GPU 时需通过作业在计算节点验证运行）。

## 工作流程

### 1. 只读探测工具链与现有安装

先检查当前已加载模块、编译器、MPI 包装器、数学库和 GPU 工具链是否版本一致（避免把 GCC 的 MPI 包装器混配 Intel/NVHPC 运行库）：

```bash
module list 2>&1 || true
which gcc g++ ifort ifx nvcc mpirun || true
mpicc -show || true
nvcc --version || true
```

### 2. 隔离源码、构建与安装目录

保留现有已验证版本，新建独立标签目录进行编译，避免原地覆盖导致全组任务瘫痪：
- `src/`：只读原始源码（补丁版本另建副本或打补丁分支，记录 patch 清单与顺序）。
- `build-<version>-<variant>/`：本次构建工作目录。
- `install-<version>-<variant>/`：独立安装前缀与对应的 `env.sh` 环境加载脚本。

### 3. 配置编译选项与补丁

按软件与目标变体选择匹配的配置（VASP / LAMMPS / CP2K / PLUMED 细节见 [构建适配](references/builds.md)）：
- 编译前核对编译器 flags（如 `-march=...` 与计算节点 CPU 指令集交集）、CUDA compute capability（如 `cc80`/`cc90`）以及 FFTW/MKL/ScaLAPACK/BLAS 接口位数（LP64 vs ILP64）。
- 大型编译（如 CP2K 全依赖编译、VASP 全编译）在受限登录节点上建议转为交互计算节点或提交编译作业。

### 4. 检查动态链接库与二进制能力

编译完成后先检查动态库依赖无 `not found`，再查程序自报编译特性：

```bash
ldd <binary_path> | grep -E "not found|mpi|cuda|mkl|fftw"
```

### 5. 在目标架构做最小冒烟验证（Smoke Test）

仅生成可执行文件或通过链接不代表功能可用（尤其 GPU / OpenACC / Kokkos / 自定义 PLUMED action）：
- 在实际目标架构（计算节点）用**微型算例**（几步 SCF 或 10 步 MD）验证：
  1. 所需功能开关实际生效（例如打印了 GPU 加速信息、VASP 识别了补丁参数、LAMMPS `lmp -h` 列出目标 style）；
  2. 能量、力、温度等基础物理量有限且与 CPU 参考或预期量级一致。
- 若用户明确需要对比性能缩放，按 [受控性能测试](references/benchmarking.md) 设计独立目录对照。

## 按需参考

- VASP 变体与补丁、LAMMPS CMake 包检查、MPI/GPU ABI 陷阱：阅读 [构建适配](references/builds.md)。
- 固定协议的并行加速与吞吐量评测方法：阅读 [受控性能测试](references/benchmarking.md)。

## 交付产物与验收

1. 独立安装目录与干净的 `env.sh`（显式配置 `PATH`、`LD_LIBRARY_PATH` 或 `module load`）。
2. `build-report.json`：记录源码版本、补丁列表、编译器/MPI/CUDA 版本、构建命令、`ldd` 检查结果及目标节点冒烟算例通过情况（未在目标节点跑通前明确标记为“未运行验证”）。
