#!/bin/bash
# Install FAIRChem with GPU support on S3DF.
# Run from iana node: bash scripts/setup_fairchem.sh
#
# This installs miniconda (if needed) and creates a fairchem environment
# with PyTorch + CUDA 12.1 and fairchem-core.

set -euo pipefail

CONDA_DIR="/sdf/group/ssrl/$USER/miniconda3"

echo "=== Step 1: Conda Installation ==="
if [ -d "$CONDA_DIR" ]; then
    echo "Conda already installed at $CONDA_DIR"
else
    echo "Downloading Miniconda..."
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    echo "Installing to $CONDA_DIR ..."
    bash /tmp/miniconda.sh -b -u -p "$CONDA_DIR"
    rm /tmp/miniconda.sh
    "$CONDA_DIR/bin/conda" init bash
    echo "Conda installed. You may need to 'source ~/.bashrc' or log out and back in."
fi

source "$CONDA_DIR/bin/activate"

echo ""
echo "=== Step 2: Create fairchem environment ==="
if conda env list | grep -q "fairchem"; then
    echo "fairchem env already exists. Activating..."
    conda activate fairchem
else
    echo "Creating fairchem env with Python 3.11..."
    conda create -y -n fairchem python=3.11
    conda activate fairchem
fi

echo ""
echo "=== Step 3: Install PyTorch with CUDA 12.1 ==="
# CUDA 12.2 is on the ada nodes; PyTorch CUDA 12.1 is compatible
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo ""
echo "=== Step 4: Install FAIRChem ==="
pip install fairchem-core

echo ""
echo "=== Step 5: Verify Installation ==="
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')

import fairchem
print(f'FAIRChem installed successfully')
"

echo ""
echo "=== Done! ==="
echo "To use: source $CONDA_DIR/bin/activate && conda activate fairchem"
