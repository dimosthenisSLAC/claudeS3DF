#!/bin/bash
#SBATCH --job-name=ocean321_120c
#SBATCH --account=lcls:cxilr8416
#SBATCH --partition=milano
#SBATCH --ntasks=120
#SBATCH --nodes=1
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=460G
#SBATCH --time=12:00:00
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

echo "=== OCEAN 3.2.0.1: IrO2 Ir L-edge — 120 cores scaling test ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "SLURM_NTASKS: $SLURM_NTASKS"

export PATH="/sdf/sw/openmpi/v4.1.6/ompi/build/bin:/usr/bin:/bin:$PATH"
export OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="/sdf/group/ssrl/dsokaras/sw/openblas-0.3.28/lib:/sdf/sw/openmpi/v4.1.6/ompi/build/lib:/sdf/group/ssrl/dsokaras/sw/libxc-5.2.3-sys/lib64"

OCEAN_DIR="/sdf/group/ssrl/dsokaras/sw/ocean_3.2.0.1"

WORKDIR="/sdf/scratch/users/d/dsokaras/ocean321_128c_${SLURM_JOB_ID}"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Copy input files
cp /sdf/home/d/dsokaras/IrO2_example/IrO2.in .
cp /sdf/home/d/dsokaras/IrO2_example/photon1 .
cp /sdf/home/d/dsokaras/IrO2_example/photon2 .
cp /sdf/home/d/dsokaras/IrO2_example/photon3 .

# CRITICAL: -n must come BEFORE --mca flags (OCEAN regex grabs first number)
sed -i "s|para_prefix{.*}|para_prefix{ mpirun -n $SLURM_NTASKS --mca btl self,vader --mca pml ob1 }|" IrO2.in

echo ""
echo "Key settings:"
grep -E "para_prefix|ecut |nkpt|nbands|edges|pp_database|dft.functional|screen.nkpt|cnbse.xmesh" IrO2.in
echo ""

# Instrument each OCEAN stage with timestamps
echo "=========================================="
echo "  Running OCEAN 3.2.0.1 — 120 cores"
echo "=========================================="
T0=$(date +%s)

perl $OCEAN_DIR/ocean.pl IrO2.in 2>&1

T1=$(date +%s)
TOTAL=$((T1-T0))
echo ""
echo "=========================================="
echo "  TIMING SUMMARY"
echo "=========================================="
echo "Total wall time: $TOTAL seconds ($( echo "scale=1; $TOTAL/60" | bc ) min)"
echo "Cores: $SLURM_NTASKS"
echo "Core-hours: $( echo "scale=2; $TOTAL * $SLURM_NTASKS / 3600" | bc )"

echo ""
echo "=========================================="
echo "  RESULTS"
echo "=========================================="

# Check for output spectra — look in CNBSE/ too
if ls CNBSE/absspct_Ir* 1>/dev/null 2>&1; then
    echo "SUCCESS: absorption spectra produced"
    ls -la CNBSE/absspct_Ir*
elif ls absspct_Ir* 1>/dev/null 2>&1; then
    echo "SUCCESS: absorption spectra produced"
    ls -la absspct_Ir*
else
    echo "NO spectra output. Checking pipeline stages..."
    grep "Entering\|Done\|Stage\|Failed\|ERROR" ocean.log 2>/dev/null || \
    grep "Entering\|Done\|Stage\|Failed" *.out 2>/dev/null | tail -20
fi

# Copy results to a separate dir for the scaling comparison
RESULT_DIR="$HOME/claudeS3DF/results/ocean_iro2_scaling/120cores"
mkdir -p "$RESULT_DIR"
cp CNBSE/absspct_Ir* "$RESULT_DIR/" 2>/dev/null
cp absspct_Ir* "$RESULT_DIR/" 2>/dev/null

echo ""
echo "=== Done ==="
