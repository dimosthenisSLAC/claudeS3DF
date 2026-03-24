#!/bin/bash
#SBATCH --job-name=Ag_clean_amp
#SBATCH --account=lcls:cxilr8416
#SBATCH --partition=ampere
#SBATCH --gres=gpu:a100:1
#SBATCH --qos=normal
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00

NVHPC="/sdf/group/ssrl/dsokaras/sw/nvhpc/Linux_x86_64/24.1"
export PATH="${NVHPC}/compilers/bin:${NVHPC}/comm_libs/12.3/hpcx/hpcx-2.17.1/ompi/bin:${PATH}"
export LD_LIBRARY_PATH="${NVHPC}/compilers/lib:${NVHPC}/compilers/extras/qd/lib:${NVHPC}/comm_libs/12.3/hpcx/hpcx-2.17.1/ompi/lib:${NVHPC}/math_libs/12.3/lib64:${NVHPC}/cuda/12.3/targets/x86_64-linux/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=1

echo "Running on $(hostname) with $(nvidia-smi --query-gpu=name --format=csv,noheader)"
mpirun -np 1 /sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/build_ampere/std/vasp_gpu 2>&1
echo "Final energy:"
grep "energy  without entropy" OUTCAR 2>/dev/null | tail -1
