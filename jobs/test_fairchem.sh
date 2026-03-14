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
from fairchem.core import OCPCalculator
from fairchem.core.models import model_name_to_local_file
print("\nFAIRChem core imported successfully")
print(f"OCPCalculator available: {OCPCalculator is not None}")

# List available pretrained models
from fairchem.core.common.registry import registry
print("\nAvailable model architectures:")
for name in sorted(registry.get_registry("model").keys()):
    print(f"  - {name}")

print("\n=== FAIRChem GPU Test PASSED ===")
PYEOF

echo ""
echo "=== Done ==="
