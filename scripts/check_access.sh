#!/bin/bash
# Run this on S3DF (iana node) to verify your SLURM access and find reservations.
# Usage: bash scripts/check_access.sh

echo "=== Your SLURM Associations ==="
sacctmgr show assoc user=$USER format=Account%20,Partition%12,QOS%20,MaxJobs,MaxSubmit

echo ""
echo "=== Available Reservations (isaac) ==="
scontrol show reservations | grep -A 10 "isaac" || echo "No isaac reservations currently active"

echo ""
echo "=== Ada Partition Status ==="
sinfo -p ada --format="%P %a %l %D %T %G"

echo ""
echo "=== Your Current Jobs ==="
squeue -u $USER || echo "No jobs running"

echo ""
echo "=== Disk Quotas ==="
echo "Home:"
df -h /sdf/home/${USER:0:1}/$USER 2>/dev/null || echo "  Could not check home quota"
echo "Scratch:"
df -h /sdf/scratch/users/${USER:0:1}/$USER 2>/dev/null || echo "  Could not check scratch quota"

echo ""
echo "=== Group Space ==="
ls -la /sdf/group/ssrl/ 2>/dev/null | head -20 || echo "  /sdf/group/ssrl/ not accessible"
