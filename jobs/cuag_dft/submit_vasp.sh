#!/bin/bash
#SBATCH --job-name=cuag_co
#SBATCH --account=ssrl:isaac
#SBATCH --partition=ada
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

echo "Job started: $(date)"
echo "Node: $(hostname)"
echo "Directory: $(pwd)"
echo "POSCAR:"
head -8 POSCAR
echo ""

# VASP 6.5.1 GPU build (NVIDIA HPC SDK + OpenACC, targets L40S cc89)
VASP_GPU="/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/build/std/vasp_gpu"

# NVIDIA HPC SDK runtime
NVHPC="/sdf/group/ssrl/dsokaras/sw/nvhpc/Linux_x86_64/24.1"
export PATH="${NVHPC}/compilers/bin:${NVHPC}/comm_libs/mpi/bin:${PATH}"
export LD_LIBRARY_PATH="${NVHPC}/compilers/lib:${NVHPC}/compilers/extras/qd/lib:${NVHPC}/comm_libs/mpi/lib:${NVHPC}/comm_libs/nccl/lib:${NVHPC}/math_libs/lib64:${NVHPC}/cuda/12.3/targets/x86_64-linux/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=1

echo "GPU:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "nvidia-smi not available"
echo ""

mpirun -np 1 $VASP_GPU 2>&1

echo ""
echo "Job finished: $(date)"
echo "Final energy:"
grep "energy  without entropy" OUTCAR 2>/dev/null | tail -1
grep "F=" OSZICAR 2>/dev/null | tail -1
