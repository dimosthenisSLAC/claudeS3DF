# VASP Calculation Skill for S3DF

You are an expert VASP calculation manager on S3DF at SLAC. Follow this decision tree when setting up, running, monitoring, or troubleshooting VASP calculations.

## Job Submission Rules

### Partition and GPU Selection
- **ampere (A100, 40GB)**: ALWAYS try first for VASP GPU. 2-3x faster FP64 than L40S.
- **ada (L40S, 46GB)**: Fallback only if ampere is full or unavailable.
- **NEVER use ampere for CPU VASP** -- binary mismatch causes crashes.
- GPU build: `/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/bin_ampere/vasp_std`
- CPU build: `/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/build/std/vasp`

### SLURM Account Spreading (CRITICAL)
When submitting **multiple concurrent jobs** to the same partition, use DIFFERENT accounts for each to avoid AssocGrpNodeLimit blocks:
- `lcls:prjisaac01` -- primary ISAAC account
- `lcls:mecl1016522`, `lcls:xcsl1004021`, `lcls:cxilr8416`
- `lcls:xcsl1030422`, `lcls:xcsx1000422`, `lcls:xpplx4919`
- All have normal QoS on ampere.

### GPU VASP Environment
```bash
NVHPC=/sdf/group/ssrl/dsokaras/sw/nvhpc/Linux_x86_64/24.1
HPCX=${NVHPC}/comm_libs/12.3/hpcx/hpcx-2.17.1
export LD_LIBRARY_PATH=${NVHPC}/compilers/extras/qd/lib:${NVHPC}/cuda/12.3/targets/x86_64-linux/lib:${NVHPC}/compilers/lib:${HPCX}/ompi/lib:${LD_LIBRARY_PATH:-}
export OPAL_PREFIX=${HPCX}/ompi
export OMP_NUM_THREADS=1
${HPCX}/ompi/bin/mpirun --bind-to none -np $SLURM_NTASKS vasp_std
```

### Using Custodian (preferred)
Instead of calling VASP directly, use the Custodian wrapper for automatic error handling:
```bash
source /sdf/group/ssrl/dsokaras/miniconda3/bin/activate && conda activate fairchem
cd $WORKDIR
python /sdf/home/d/dsokaras/claudeS3DF/scripts/run_vasp_custodian.py
```
This auto-detects partition, sets GPU env, and handles 38+ error types including restarts.

## Convergence Troubleshooting Decision Tree

### Electronic Convergence Failure (NELM reached)
1. Check ALGO: try ALGO = Normal, then All, then Damped (with TIME = 0.2)
2. Reduce EDIFF from 1E-4 to 1E-5
3. Increase NELM to 200
4. Try mixing: AMIX = 0.02, BMIX = 0.001, AMIX_MAG = 0.1, BMIX_MAG = 0.001
5. Check ISMEAR: metals need ISMEAR=1 or 2 (NOT -5)

### Ionic Convergence Failure (NSW reached)
1. Copy CONTCAR to POSCAR
2. If forces oscillate with CG (IBRION=2): switch to IBRION=1 (quasi-Newton)
3. If forces plateau near threshold: loosen EDIFFG (-0.02 to -0.04 for adsorbates)
4. If wild energy jumps: reduce POTIM (0.5 to 0.1) or try IBRION=3 (damped MD)
5. Clean WAVECAR/CHG/CHGCAR to save disk, VASP will regenerate

### CO/Adsorbate Force Oscillation (ZBRENT errors)
Most common issue for surface+adsorbate systems:
1. CO tilt/rock mode has flat PES, forces oscillate 0.03-0.05 eV/A indefinitely
2. Switch IBRION=2 to IBRION=1 (quasi-Newton handles floppy modes better)
3. If still oscillating: try IBRION=3 with POTIM=0.02 (damped MD)
4. For binding energies, EDIFFG=-0.04 is acceptable (energy converges before forces)
5. With Custodian: the zbrent handler does steps 1-4 automatically

### ZBRENT Fatal Internal Error
1. CONTCAR to POSCAR
2. Tighten EDIFF to 1E-6, set NELMIN=8
3. Switch to IBRION=1

### Disk Space Issues
- WAVECAR: ~500MB-2GB per calc. Delete after convergence or set LWAVE=.FALSE.
- CHG/CHGCAR: ~50-200MB. Delete unless needed for d-band or charge analysis
- Keep: CONTCAR, OUTCAR, OSZICAR, DOSCAR (small, needed for analysis)
- Home quota is 25-30 GB. Monitor with: du -sh ~/claudeS3DF/results/

## Monitoring Running Jobs

### Force Convergence Analysis
When checking convergence, ALWAYS analyze forces on FREE atoms only.
Parse selective dynamics from POSCAR to find frozen atoms (F F F), then extract forces from
TOTAL-FORCE block in OUTCAR and compute max force excluding frozen atom indices.
Frozen atoms have large residual forces that do NOT affect convergence -- VASP excludes
constrained DOFs from the EDIFFG check.

### Quick Status Check
```bash
grep 'F=' OSZICAR | tail -5          # Energy + dE per ionic step
grep 'reached required accuracy' OUTCAR  # Convergence flag
grep 'ZBRENT' OUTCAR | tail -3       # CG oscillation warnings
```

## Surface Slab Calculations

### Standard INCAR Settings (Cu-alloy surfaces)
```
ENCUT = 400
EDIFF = 1E-5
ISMEAR = 1
SIGMA = 0.1
LREAL = Auto
PREC = Normal
ALGO = Normal
IBRION = 2          # Start with CG, switch to 1 if oscillating
EDIFFG = -0.02      # Force criterion; loosen to -0.04 for adsorbates
ISIF = 2            # Relax ions only (not cell)
IVDW = 12           # D3 dispersion correction for adsorbates
ISPIN = 1           # Non-magnetic (Cu, Au, Ag)
LORBIT = 11         # For DOSCAR / d-band analysis
NCORE = 4
LWAVE = .TRUE.
LCHARG = .TRUE.
```

### Selective Dynamics
- Freeze bottom 2 slab layers (bulk-like), relax top 2 + adsorbate
- Use z-coordinate threshold: freeze all atoms with z_frac < 0.48
- Verify frozen/free assignment by checking T T T / F F F flags in POSCAR
- Common bug: atom reordering during slab construction can misassign T/F flags

### CO Binding Energy
```
E_bind = E(slab+CO) - E(slab) - E(CO_gas)
```
- Use same ENCUT, IVDW, PREC for all three calculations
- CO gas: use same box size (at least 15 A vacuum)
- Reference values: Cu(100) ~ -1.0 eV, Au-rich alloys ~ -0.3 to -0.8 eV
