#!/bin/bash
#SBATCH --job-name=ocean310_iro2
#SBATCH --account=lcls:cxilr8416
#SBATCH --partition=milano
#SBATCH --ntasks=32
#SBATCH --nodes=1
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=256G
#SBATCH --time=12:00:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

echo "=== OCEAN 3.1.0: IrO2 Ir L-edge ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "SLURM_NTASKS: $SLURM_NTASKS"

export PATH="/sdf/sw/openmpi/v4.1.6/ompi/build/bin:/usr/bin:/bin:$PATH"
export OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="/sdf/group/ssrl/dsokaras/sw/openblas-0.3.28/lib:/sdf/sw/openmpi/v4.1.6/ompi/build/lib:/sdf/group/ssrl/dsokaras/sw/libxc-5.2.3-sys/lib64"

OCEAN_DIR="/sdf/group/ssrl/dsokaras/sw/ocean_3.1.0"

WORKDIR="/sdf/scratch/users/d/dsokaras/ocean310_iro2_${SLURM_JOB_ID}"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Copy input files
cp /sdf/home/d/dsokaras/IrO2_example/IrO2.in .
cp /sdf/home/d/dsokaras/IrO2_example/photon1 .
cp /sdf/home/d/dsokaras/IrO2_example/photon2 .
cp /sdf/home/d/dsokaras/IrO2_example/photon3 .

# Adapt for S3DF: change para_prefix from NERSC srun to our mpirun
# CRITICAL: -n must come BEFORE --mca flags!
# OCEAN's parse_para_prefix grabs the FIRST number in the string.
# "mpirun --mca pml ob1 -n 32" → OCEAN sees ncpus=1 (from ob1), NOT 32!
# "mpirun -n 32 --mca pml ob1" → OCEAN sees ncpus=32 ✓
sed -i "s|para_prefix{.*}|para_prefix{ mpirun -n $SLURM_NTASKS --mca btl self,vader --mca pml ob1 }|" IrO2.in

echo ""
echo "Key settings:"
grep -E "para_prefix|ecut |nkpt|nbands|edges|pp_database|dft.functional|screen.nkpt|cnbse.xmesh" IrO2.in
echo ""

echo "=========================================="
echo "  Running OCEAN 3.1.0 — IrO2 Ir L-edge"
echo "=========================================="
T0=$(date +%s)

perl $OCEAN_DIR/ocean.pl IrO2.in 2>&1

T1=$(date +%s)
echo ""
echo "Wall time: $((T1-T0)) seconds ($( echo "scale=1; ($T1-$T0)/60" | bc ) min)"

echo ""
echo "=========================================="
echo "  RESULTS"
echo "=========================================="

# Check for output spectra
if ls absspct_Ir* 1>/dev/null 2>&1; then
    echo "SUCCESS: absorption spectra produced"
    ls -la absspct_Ir*
    echo ""
    for f in absspct_Ir*; do
        echo "$f: $(wc -l < $f) lines"
        head -3 "$f"
        echo "..."
    done
else
    echo "NO spectra output. Checking pipeline stages..."
    grep "Entering\|Done\|Stage\|Failed\|ERROR" ocean.log 2>/dev/null || \
    grep "Entering\|Done\|Stage\|Failed" *.out 2>/dev/null | tail -20
fi

# Copy results
RESULT_DIR="$HOME/claudeS3DF/results/ocean_iro2_3.1.0"
mkdir -p "$RESULT_DIR"
cp absspct_Ir* "$RESULT_DIR/" 2>/dev/null
cp ocean.log "$RESULT_DIR/" 2>/dev/null

echo ""
echo "=== Done ==="
