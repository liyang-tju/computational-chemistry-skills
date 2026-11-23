# Computational Chemistry and Materials Simulation Skills

This repository contains 14 standalone skills for atomistic modeling, electronic structure calculations, molecular dynamics, free-energy analysis, and machine-learning potentials. Each skill describes its workflow, parameter choices, and result validation.

## Structure Modeling

| Skill | Invocation name | What it does |
|---|---|---|
| [Atomistic Model Building](skills/atomistic-model-builder/SKILL.md) | `atomistic-model-builder` | Build molecules, crystals, surfaces, adsorption structures, and simulation cells with solvent and ions. |
| [Molecular Parameterization](skills/molecular-parameterization/SKILL.md) | `molecular-parameterization` | Fit ESP/RESP charges, assign atom types, and assemble force-field topologies. |

## DFT Calculations

| Skill | Invocation name | What it does |
|---|---|---|
| [VASP Calculations](skills/vasp-calculations/SKILL.md) | `vasp-calculations` | Prepare single points, relaxations, AIMD, NEB, dimer searches, and frequencies. Extract Bader charges and work functions. |
| [CP2K Calculations](skills/cp2k-calculations/SKILL.md) | `cp2k-calculations` | Prepare single points, optimizations, and AIMD. Choose Poisson solvers, SCF methods, and restart settings. |
| [ORCA Molecular Calculations](skills/orca-calculations/SKILL.md) | `orca-calculations` | Prepare molecular optimizations, frequencies, and single points. Diagnose imaginary modes and export wavefunctions for ESP/RESP fitting. |

## Classical Molecular Dynamics

| Skill | Invocation name | What it does |
|---|---|---|
| [LAMMPS Simulations](skills/lammps-md/SKILL.md) | `lammps-md` | Verify topology and units. Prepare classical MD, electrode simulations, independent replicas, and continuations. |
| [GROMACS Molecular Dynamics](skills/gromacs-md/SKILL.md) | `gromacs-md` | Check topology and inputs. Prepare minimization, NVT/NPT, production runs, and checkpoint continuations. |

## Machine-Learning Potentials

| Skill | Invocation name | What it does |
|---|---|---|
| [Active Learning for Machine-Learning Potentials](skills/mlp-workflow/SKILL.md) | `mlp-workflow` | Connect presampling, representative structure selection, DFT labeling, committee training, and uncertainty-driven relabeling. |

## Electrochemistry and Free Energy

| Skill | Invocation name | What it does |
|---|---|---|
| [Computational Hydrogen Electrode](skills/che-calculation/SKILL.md) | `che-calculation` | Calculate vibrational corrections, convert between RHE and SHE, and determine reaction free energies and limiting potentials. |
| [Constant-Potential Calculations](skills/constant-potential-calculations/SKILL.md) | `constant-potential-calculations` | Set up charge scans and constant-potential simulations. Align potential references and compute grand potentials. |
| [Enhanced Sampling and Free-Energy Analysis](skills/enhanced-sampling/SKILL.md) | `enhanced-sampling` | Set up reaction coordinates and biases. Reconstruct PMFs using Blue Moon, WHAM, MBAR, or reweighting. |

## Trajectory and Solvation Analysis

| Skill | Invocation name | What it does |
|---|---|---|
| [Trajectory Processing and Conversion](skills/trajectory-tools/SKILL.md) | `trajectory-tools` | Convert, extract, and join trajectories while preserving cells, step numbers, and atom mappings. |
| [Trajectory Analysis](skills/trajectory-analysis/SKILL.md) | `trajectory-analysis` | Calculate density, orientation, RDFs, coordination, hydrogen bonding, and RMSD. Analyze reaction events and sampling uncertainty. |
| [Solvation Energy Decomposition](skills/solvation-energy/SKILL.md) | `solvation-energy` | Extract frozen fragments, combine their single-point energies, and quantify how solvent affects adsorption energies. |
