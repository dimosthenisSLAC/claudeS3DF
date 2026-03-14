#!/bin/bash
#SBATCH --job-name=test_pytorch
#SBATCH --account=ssrl
#SBATCH --partition=ada
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=output-pytorch-%j.txt
#SBATCH --error=error-pytorch-%j.txt

set -euo pipefail

echo "=== PyTorch GPU Test ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo ""

# Activate conda env (adjust path if needed)
source /sdf/group/ssrl/$USER/miniconda3/bin/activate
conda activate gpu_env

python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
print(f'GPU count: {torch.cuda.device_count()}')

if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')
        print(f'    Memory: {torch.cuda.get_device_properties(i).total_mem / 1e9:.1f} GB')

    # Quick compute test
    device = torch.device('cuda:0')
    a = torch.randn(1000, 1000, device=device)
    b = torch.randn(1000, 1000, device=device)

    import time
    start = time.time()
    for _ in range(100):
        c = torch.matmul(a, b)
    torch.cuda.synchronize()
    elapsed = time.time() - start

    print(f'\nMatrix multiply benchmark (1000x1000, 100 iters): {elapsed:.3f}s')
    print('GPU compute test PASSED')
else:
    print('ERROR: No CUDA GPU available!')
    exit(1)
"

echo ""
echo "=== Test Complete ==="
