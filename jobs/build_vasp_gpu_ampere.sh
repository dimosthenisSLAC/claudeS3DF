#!/bin/bash
#SBATCH --job-name=build_vasp_amp
#SBATCH --account=lcls:cxilr8416
#SBATCH --partition=ampere
#SBATCH --gres=gpu:a100:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

echo "=== Building VASP 6.5.1 GPU for Ampere (A100) ==="
echo "Date: $(date)"
echo "Node: $(hostname)"
echo "CPU: $(lscpu | grep 'Model name')"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"

# NVIDIA HPC SDK
NVHPC="/sdf/group/ssrl/dsokaras/sw/nvhpc/Linux_x86_64/24.1"
export PATH="${NVHPC}/compilers/bin:${NVHPC}/comm_libs/12.3/hpcx/hpcx-2.17.1/ompi/bin:${PATH}"
export LD_LIBRARY_PATH="${NVHPC}/compilers/lib:${NVHPC}/compilers/extras/qd/lib:${NVHPC}/comm_libs/12.3/hpcx/hpcx-2.17.1/ompi/lib:${NVHPC}/math_libs/12.3/lib64:${NVHPC}/cuda/12.3/targets/x86_64-linux/lib:${LD_LIBRARY_PATH:-}"

VASP_SRC="/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1"
# Build in a separate copy so we don't destroy the ada build
BUILD_BASE="/sdf/group/ssrl/dsokaras/sw/vasp6/vasp_ampere_build"

echo "Copying VASP source to $BUILD_BASE ..."
rm -rf "$BUILD_BASE"
cp -a "$VASP_SRC" "$BUILD_BASE"

cd "$BUILD_BASE"

# Use the GPU makefile
cp makefile.include.gpu makefile.include

# Clean everything to force full recompile on this CPU
make veryclean 2>&1 | tail -3

echo ""
echo "Compiler: $(nvfortran --version | head -1)"
echo ""

echo "Building std (full recompile on AMD Rome / Zen2)..."
T0=$(date +%s)
make DEPS=1 -j16 std 2>&1 | tail -10
T1=$(date +%s)
echo "Build time: $((T1-T0)) seconds"

# GPU makefile produces 'vasp', not 'vasp_gpu'
if [ -f build/std/vasp ]; then
    DEST="/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/build_ampere/std"
    mkdir -p "$DEST"
    cp build/std/vasp "$DEST/vasp_gpu"
    echo "Installed: $DEST/vasp_gpu"
    ls -la "$DEST/vasp_gpu"

    # Smoke test
    echo ""
    echo "=== Smoke test on A100 ==="
    TMPDIR=$(mktemp -d)
    cd "$TMPDIR"

    cat > POSCAR << 'EOF'
Si
5.43
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
Si
2
Direct
0.0 0.0 0.0
0.25 0.25 0.25
EOF
    cat > INCAR << 'EOF'
ENCUT = 200
ISMEAR = 0
SIGMA = 0.1
NSW = 0
ALGO = Normal
EOF
    cat > KPOINTS << 'EOF'
Auto
0
Gamma
2 2 2
0 0 0
EOF
    cat /sdf/group/ssrl/dsokaras/sw/vasp6/potpaw_PBE64/Si/POTCAR > POTCAR

    mpirun -np 1 "$DEST/vasp_gpu" 2>&1 | tail -10

    if grep -q "energy  without entropy" OUTCAR 2>/dev/null; then
        energy=$(grep "energy  without entropy" OUTCAR | tail -1 | awk '{print $NF}')
        echo ""
        echo "SMOKE TEST PASSED: Si energy = $energy eV"
    else
        echo ""
        echo "SMOKE TEST FAILED"
        cat OUTCAR 2>/dev/null | tail -20
    fi

    rm -rf "$TMPDIR"
else
    echo "BUILD FAILED: build/std/vasp not found"
    ls -la build/std/ 2>/dev/null | tail -10
fi

# Clean up build copy (keep only the binary)
echo ""
echo "Cleaning up build directory..."
rm -rf "$BUILD_BASE"

echo ""
echo "=== Done: $(date) ==="
