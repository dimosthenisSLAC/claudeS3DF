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

echo "=== MLIP GPU Test ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

# Activate environment
source /sdf/group/ssrl/$USER/miniconda3/bin/activate
conda activate fairchem

# Install CHGNet if not present (freely available universal MLIP from Microsoft)
pip install --quiet chgnet 2>/dev/null || true

python3 << 'PYEOF'
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Confirm FAIRChem is installed
import fairchem.core
print(f"\nFAIRChem core version: {fairchem.core.__version__}")
print("(FAIRChem pretrained models require HuggingFace gated access - pending approval)")

# Use CHGNet as a freely available universal MLIP
print("\n--- Loading CHGNet universal potential ---")
from chgnet.model.model import CHGNet
from chgnet.model.dynamics import CHGNetCalculator

model = CHGNet.load()
print(f"CHGNet loaded: {sum(p.numel() for p in model.parameters())/1e6:.1f}M parameters")
calc = CHGNetCalculator(model=model, use_device="cuda")
print("CHGNet calculator on GPU ready")

from ase.build import bulk, molecule

# Example 1: Bulk copper
print("\n--- Example 1: Bulk Copper (FCC) ---")
cu = bulk("Cu", "fcc", a=3.61)
cu.calc = calc
energy = cu.get_potential_energy()
forces = cu.get_forces()
print(f"Structure: {cu.get_chemical_formula()} ({len(cu)} atoms)")
print(f"Energy: {energy:.4f} eV")
print(f"Forces:\n{forces}")
print(f"Max force: {abs(forces).max():.6f} eV/Ang")

# Example 2: Water molecule (need periodic cell for CHGNet)
print("\n--- Example 2: Silicon Diamond ---")
si = bulk("Si", "diamond", a=5.43)
si.calc = calc
energy = si.get_potential_energy()
forces = si.get_forces()
print(f"Structure: {si.get_chemical_formula()} ({len(si)} atoms)")
print(f"Energy: {energy:.4f} eV")
print(f"Forces:\n{forces}")

# Example 3: Quick geometry optimization
print("\n--- Example 3: Geometry Optimization (Cu, a=3.70 -> relaxed) ---")
from ase.optimize import BFGS
cu2 = bulk("Cu", "fcc", a=3.70)  # start with wrong lattice constant
cu2.calc = calc
opt = BFGS(cu2, logfile=None)
opt.run(fmax=0.01, steps=50)
print(f"Optimized energy: {cu2.get_potential_energy():.4f} eV")
print(f"Final max force: {abs(cu2.get_forces()).max():.6f} eV/Ang")

print("\n=== MLIP GPU Test PASSED ===")
PYEOF

echo ""
echo "=== Done ==="
