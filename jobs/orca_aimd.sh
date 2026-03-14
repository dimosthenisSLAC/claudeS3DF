#!/bin/bash
#SBATCH --job-name=orca_aimd
#SBATCH --account=ssrl:isaac
#SBATCH --partition=ada
#SBATCH --gres=gpu:0
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

echo "=== ORCA AIMD: Na+ in 10 H2O ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

# ORCA setup
ORCA_DIR="/sdf/group/ssrl/sarangi/sw/orca601/orca_6_0_1"
export PATH="${ORCA_DIR}:${PATH}"
export LD_LIBRARY_PATH="${ORCA_DIR}:${ORCA_DIR}/lib:${LD_LIBRARY_PATH:-}"

# OpenMPI matching ORCA's build
export PATH="/sdf/group/ssrl/sarangi/sw/openmpi/bin:${PATH}"
export LD_LIBRARY_PATH="/sdf/group/ssrl/sarangi/sw/openmpi/lib:${LD_LIBRARY_PATH}"

# Working directory on scratch
WORKDIR="/sdf/scratch/users/d/dsokaras/orca_aimd_${SLURM_JOB_ID}"
mkdir -p "$WORKDIR"
cp jobs/na_water_aimd.inp "$WORKDIR/"
cd "$WORKDIR"

echo "Working directory: $WORKDIR"
echo "ORCA: $(which orca)"
echo "MPI: $(which mpirun 2>/dev/null || echo 'not found')"
echo ""

# Run ORCA (output goes directly to stdout/stderr for debugging)
echo "Starting ORCA at $(date)"
echo "=========================================="
${ORCA_DIR}/orca na_water_aimd.inp
ORCA_EXIT=$?
echo "=========================================="
echo "ORCA finished at $(date) with exit code $ORCA_EXIT"

# Copy key results back
for f in na_water_aimd_trj.xyz na_water_aimd.md.log na_water_aimd.xyz; do
    cp -v "$WORKDIR/$f" ~/claudeS3DF/ 2>/dev/null || true
done

echo ""
echo "=== Done ==="
