#!/bin/bash
#SBATCH --job-name=cuag_co
#SBATCH --account=ssrl:isaac
#SBATCH --partition=ada
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

# Load VASP module (adjust based on what's available)
# Run: module avail vasp  to find the correct module name
# module load vasp/6.x.x

echo "Job started: $(date)"
echo "Node: $(hostname)"
echo "Directory: $(pwd)"
echo "POSCAR contents:"
head -8 POSCAR

# Run VASP (adjust path/command as needed)
# For GPU VASP:
#   srun vasp_std
# For CPU VASP:
#   mpirun -np $SLURM_CPUS_PER_TASK vasp_std

echo "Job finished: $(date)"
