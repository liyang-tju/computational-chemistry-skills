---
name: molecular-parameterization
description: "Prepare molecular quantum geometry/frequency checks, ESP/RESP charge fitting, atom typing and force-field topology assembly (including polymer head/monomer/tail templates) while preserving atom mapping and mixing-rule compatibility."
---
# Molecular Parameterization

Prepare quantum optimizations and frequency checks, fit ESP/RESP charges, assign force-field atom types, and assemble topologies for molecules, ions, or polymers. Track atom indices, charge constraints, 1–4 scaling, and mixing rules.

## Before You Start

- **Force field and engine.** Identify the force-field family, such as GAFF/GAFF2, OPLS-AA, or CHARMM, and the target format (LAMMPS `data`, GROMACS `.itp`/`.top`, or Amber `.mol2` plus `.frcmod`).
- **Chemical model and conformers.** Confirm connectivity (SMILES/MOL2/SDF), end groups, repeat-unit roles (head/internal/tail), total charge, spin multiplicity, and representative conformers.
- **Quantum and charge protocols.** Specify the optimization functional and basis, frequency requirements, ESP level such as B3LYP/6-31G* or a user-selected solvent protocol, RESP constraints and conformer treatment, and available tools (ORCA, Gaussian, Multiwfn, AmberTools `antechamber`/`parmchk2`, or `acpype`).

## Workflow

### 1. Verify Connectivity and Atom Mapping

- Start from explicit bond orders and hydrogen atoms, for example in `.mol2` or `.sdf`. Assign stable full-atom indices and names across quantum software reordering, cap removal, and linking.
- For **polymers**, identify capping groups and head/tail junctions, and record the atoms removed and covalent bonds added when joining units.

### 2. Prepare Separate Quantum Calculation Stages

1. **Geometry optimization (Opt).** Optimize the target conformer if needed under the specified protocol. Verify convergence and preserve the intended connectivity.
2. **Frequency verification (Freq).** Run frequencies when identifying a stationary point or obtaining thermochemical corrections. Before labeling a structure a minimum, check that all vibrational frequencies are positive. Preserve the supplied geometry for a requested fixed-geometry single point.
3. **Wavefunction or ESP single point (SP).** Export a file containing complete orbitals and basis information (`.fchk`, `.wfx`, or `.molden`), or use the grid ESP written by the quantum chemistry program.

### 3. Fit ESP or RESP Charges

Record the following for the selected fit. See [Charges and Topologies](references/charges-topology.md).
- The sampling grid or surface, such as MK, CHELPG, or Connolly shells, and the weights and atom equivalence groups for two-stage RESP. Methyl hydrogens are one example of an equivalence group.
- Check that the charges sum to the target at the required precision. For a polymer's **head, internal repeat unit, and tail** templates, record cap charge constraints and how any residual rounding correction was allocated.

### 4. Assign Atom Types and Build Topologies

- Use `antechamber` with `parmchk2`, `acpype`, or the target topology tools to assign atom types, bonds, angles, torsions, impropers, and Lennard-Jones parameters.
- Review high-penalty and missing parameters, including missing bonded terms or torsions flagged `ATTN, need revision` in `.frcmod`. Report terms requiring verification.
- Check that charges, 1–4 scaling (`special_bonds`, `fudgeLJ`, `fudgeQQ`), and combination rules (Lorentz–Berthelot `arithmetic` or `geometric`) follow the chosen force-field family.

### 5. Validate a Single Molecule

After converting the topology to the target MD engine, such as LAMMPS or GROMACS, run a single-molecule energy check or brief relaxation.
- Verify the atom count, total mass, and net charge.
- Compare with the quantum reference conformer for significant distortions in bond lengths or angles and unintended ring flips.

## References

- See [Charges and Topologies](references/charges-topology.md) for export formats, Multiwfn and RESP stages, polymer templates, and mixing rules.

## Deliverables and Validation

1. Quantum inputs, convergence records, and `charges.csv` with atom equivalences and constraints.
2. Target topology files such as `.mol2`, `.frcmod`, `.itp`, or `system.data`, and `atom_mapping.csv`.
3. **`parameterization.json`** with the quantum level, charge method, force-field family, 1–4 scaling, mixing rules, and known empirical or missing parameters.
