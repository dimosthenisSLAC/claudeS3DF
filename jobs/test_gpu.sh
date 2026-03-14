#!/bin/bash
#SBATCH --job-name=test_gpu
#SBATCH --account=ssrl
#SBATCH --partition=ada
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=output-%j.txt
#SBATCH --error=error-%j.txt

set -euo pipefail

echo "=== GPU Smoke Test ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "User: $USER"
echo "Job ID: $SLURM_JOB_ID"
echo ""

echo "=== nvidia-smi ==="
nvidia-smi
echo ""

echo "=== GPU Details ==="
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv
echo ""

echo "=== CUDA Devices ==="
ls /dev/nvidia* 2>/dev/null || echo "No /dev/nvidia* devices found"
echo ""

echo "=== Environment ==="
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "SLURM_GPUS_ON_NODE=${SLURM_GPUS_ON_NODE:-unset}"
echo ""

echo "=== Test Complete ==="
