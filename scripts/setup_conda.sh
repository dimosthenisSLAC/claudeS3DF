#!/bin/bash
# Run this ONCE on S3DF (from iana node) to set up your conda environment.
# Usage: bash scripts/setup_conda.sh

set -euo pipefail

CONDA_DIR="/sdf/group/ssrl/$USER/miniconda3"

echo "=== Setting up Conda at $CONDA_DIR ==="

if [ -d "$CONDA_DIR" ]; then
    echo "Conda already installed at $CONDA_DIR"
else
    echo "Downloading Miniconda..."
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    echo "Installing..."
    bash /tmp/miniconda.sh -b -u -p "$CONDA_DIR"
    rm /tmp/miniconda.sh
    echo "Initializing conda for bash..."
    "$CONDA_DIR/bin/conda" init bash
fi

echo ""
echo "=== Creating gpu_env environment ==="
source "$CONDA_DIR/bin/activate"

if conda env list | grep -q "gpu_env"; then
    echo "gpu_env already exists, updating..."
    conda activate gpu_env
    conda install -y pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia
else
    echo "Creating gpu_env..."
    conda create -y -n gpu_env python=3.11
    conda activate gpu_env
    conda install -y pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia
fi

echo ""
echo "=== Verifying ==="
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.version.cuda}')"

echo ""
echo "=== Done! ==="
echo "To use: source $CONDA_DIR/bin/activate && conda activate gpu_env"
