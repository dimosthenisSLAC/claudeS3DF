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

## Key Results So Far
- GPU smoke test passed (job 23324272): L40S on sdfada004, nvidia-smi working
- FAIRChem environment setup in progress

## Workflow
- Edit code locally or on S3DF → commit → push to GitHub
- `git pull` on the other side to sync
- Submit jobs with `sbatch jobs/<script>.sh`
- Check output: `cat <jobname>-*.out` and `cat <jobname>-*.err`
