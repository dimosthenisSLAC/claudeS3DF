#!/bin/bash
#SBATCH --job-name=cu_melting
#SBATCH --account=lcls:default
#SBATCH --partition=ampere
#SBATCH --qos=preemptable
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

echo "=== Cu Melting MD with CHGNet on GPU ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

# Activate environment
source /sdf/group/ssrl/$USER/miniconda3/bin/activate
conda activate fairchem

# Run on scratch for I/O
WORKDIR="/sdf/scratch/users/d/dsokaras/cu_melting_${SLURM_JOB_ID}"
mkdir -p "$WORKDIR"
cp scripts/cu_melting_md.py "$WORKDIR/"
cd "$WORKDIR"

echo "Working directory: $WORKDIR"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

python3 cu_melting_md.py

# Copy results back
mkdir -p ~/claudeS3DF/results/cu_melting
cp -v "$WORKDIR"/rdf_*.dat ~/claudeS3DF/results/cu_melting/ 2>/dev/null || true
cp -v "$WORKDIR"/cu_melting_final.xyz ~/claudeS3DF/results/cu_melting/ 2>/dev/null || true
cp -v "$WORKDIR"/cu_melting.traj ~/claudeS3DF/results/cu_melting/ 2>/dev/null || true

echo ""
echo "=== Done ==="
