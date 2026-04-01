# Project Context

## User
- **Name:** Dimosthenis Sokaras (dsokaras)
- **Role:** Leader of ISAAC repo at SSRL facility, SLAC
- **GitHub:** dimosthenisSLAC
- All work must be pushed to `dimosthenisSLAC/claudeS3DF`

## S3DF Cluster Access
- **Username:** dsokaras
- **SLURM account:** `ssrl:isaac`
- **GPU partition:** `ada` (NVIDIA L40S, 10 GPUs/node, 46 GB VRAM each, CUDA 12.2)
- **CPU partition:** also has Turin cores
- **QoS:** `normal` and `preemptable` available on ada
- **Max wall time:** 10 days on ada
- **Reservations:** may have `ssrl:isaac-<window>` reservations at times

## SSH
- Bastion: `s3dflogin.slac.stanford.edu` (MFA required)
- Interactive node: `ssh iana` from bastion (SLURM/storage access here)
- Do NOT run compute on iana — use `sbatch` or `srun`

## File System
- Home: `/sdf/home/d/dsokaras` (25-30 GB quota, backed up)
- Scratch: `/sdf/scratch/users/d/dsokaras` (temporary, purged)
- Group: `/sdf/group/ssrl/` (conda envs go here)
- Conda: `/sdf/group/ssrl/dsokaras/miniconda3`
- This repo on S3DF: `~/claudeS3DF`

## Software Environment
- Conda env: `fairchem` (Python 3.11, PyTorch + CUDA 12.1, fairchem-core)
- Activate: `source /sdf/group/ssrl/dsokaras/miniconda3/bin/activate && conda activate fairchem`
- Module system: Lmod (`module avail`, `module load`)

## SLURM Job Template
```bash
#SBATCH --account=ssrl:isaac
#SBATCH --partition=ada
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
```

## ORCA Setup
- **ORCA 6.1.1 (preferred):** `/sdf/group/ssrl/dsokaras/sw/orca611/orca_6_1_1_linux_x86-64_shared_openmpi418_avx2/orca`
- **OpenMPI:** system `/sdf/sw/openmpi/v4.1.6/ompi/build` (v4.1.6 — works with SLURM natively)
- **Old ORCA 6.0.1:** `/sdf/group/ssrl/sarangi/sw/orca601/orca_6_0_1/orca` (needs OpenMPI 5.x hacks)
- Use `--ntasks=N` in SLURM for ORCA MPI parallelism
- `%pal nprocs N end` in ORCA input must match SLURM `--ntasks`
- ORCA env setup:
  ```bash
  ORCA_DIR="/sdf/group/ssrl/dsokaras/sw/orca611/orca_6_1_1_linux_x86-64_shared_openmpi418_avx2"
  OMPI_DIR="/sdf/sw/openmpi/v4.1.6/ompi/build"
  export PATH="${ORCA_DIR}:${OMPI_DIR}/bin:${PATH}"
  export LD_LIBRARY_PATH="${ORCA_DIR}:${ORCA_DIR}/lib:${OMPI_DIR}/lib:${LD_LIBRARY_PATH:-}"
  ```

## Additional Partitions
- **ampere:** A100 GPUs (40 GB), via `lcls:default` account, `preemptable` QoS
- **milano/roma:** CPU-only, via `ssrl:default` or `lcls:*` accounts

## FAIRChem Models
- All HuggingFace gated models now accessible (UMA, eSEN, OC25, OMol25, ODAC25)
- PyTorch 2.8 fix needed: `torch.serialization.add_safe_globals([slice])`
- Best for CO2RR: UMA-s-1p2 (general), eSEN-conserving-OC25 (periodic surfaces only)

## VASP Setup
- **VASP 6.5.1 (CPU):** `/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/build/std/vasp`
- Built with GCC 12.4 from conda `vasp_build` env + OpenBLAS + ScaLAPACK + FFTW
- Three binaries: `std` (standard), `gam` (gamma-point), `ncl` (non-collinear/SOC)
- PAW potentials: `/sdf/group/ssrl/dsokaras/sw/vasp6/VASP Source 6/VASP 6.5.1/potpaw_PBE.64.tgz`
- VASP env setup:
  ```bash
  source /sdf/group/ssrl/dsokaras/miniconda3/bin/activate && conda activate vasp_build
  export PATH="/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/build/std:$PATH"
  ```
- **MPI runtime (CRITICAL):** Must set these for VASP MPI to work:
  ```bash
  source /sdf/group/ssrl/dsokaras/miniconda3/bin/activate && conda activate vasp_build
  export OMP_NUM_THREADS=1
  mpirun --mca btl self,vader --mca pml ob1 -np $SLURM_NTASKS vasp
  ```
- GPU build pending (NVIDIA HPC SDK downloaded to `/sdf/group/ssrl/dsokaras/sw/nvhpc_2026_261_Linux_x86_64_cuda_13.1/`)

## QE Setup
- **QE 7.5:** `/sdf/group/ssrl/dsokaras/sw/qe/qe-7.5/build/` (building)
- Built with GCC + system OpenMPI 4.1.6 + OpenBLAS + FFTW

## Key Results So Far
- GPU smoke test passed: L40S on ada, A100 on ampere
- CHGNet: working, good all-round accuracy for molecules + bulk
- FAIRChem: all 10 pretrained models loaded and tested
- ORCA 6.0.1: AIMD completed (Na+ in 10 H2O, 500 steps), MPI parallelism working
- Cu melting MD: 108 atoms, 300-2500K, melting detected at 1800-2000K

## Workflow
- Edit code locally or on S3DF → commit → push to GitHub
- `git pull` on the other side to sync
- Submit jobs with `sbatch jobs/<script>.sh`
- Check output: `cat <jobname>-*.out` and `cat <jobname>-*.err`
