#!/bin/bash
#SBATCH --job-name=test_fairchem
#SBATCH --account=ssrl:isaac
#SBATCH --partition=ada
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

set -euo pipefail

echo "=== FAIRChem GPU Test ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

# Activate environment
source /sdf/group/ssrl/$USER/miniconda3/bin/activate
conda activate fairchem

python3 << 'PYEOF'
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Test FAIRChem imports
import fairchem.core
print(f"\nFAIRChem core version: {fairchem.core.__version__}")

from fairchem.core import FAIRChemCalculator, pretrained_mlip
print("FAIRChemCalculator imported successfully")

# Show what's available in fairchem.core
print("\nFAIRChem core contents:")
print([x for x in dir(fairchem.core) if not x.startswith("_")])

# Quick GPU tensor test
x = torch.randn(100, 100, device="cuda")
y = torch.matmul(x, x.T)
print(f"\nGPU tensor test: {y.shape} on {y.device}")

print("\n=== FAIRChem GPU Test PASSED ===")
PYEOF

echo ""
echo "=== Done ==="
