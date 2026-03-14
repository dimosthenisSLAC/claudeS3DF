# claudeS3DF

GPU job submission and management for S3DF at SLAC.

## S3DF Access

- **Username:** dsokaras
- **Facility account:** ssrl
- **GPU partition:** ada (NVIDIA L40S, 10 GPUs/node, 72 cores, 702 GB RAM)
- **Login:** Two-hop SSH — bastion then interactive node

## Quick Start

```bash
# 1. SSH into S3DF
ssh s3df          # hits bastion (MFA required)
ssh iana          # hop to interactive node

# 2. Check your SLURM associations
sacctmgr show assoc user=dsokaras format=Account,Partition,QOS

# 3. Submit the GPU test job
sbatch jobs/test_gpu.sh

# 4. Monitor
squeue -u dsokaras
```

## Directory Structure

```
├── ssh_config          # SSH config snippet for ~/.ssh/config
├── jobs/
│   ├── test_gpu.sh     # Basic GPU smoke test (nvidia-smi)
│   └── test_pytorch.sh # PyTorch GPU verification
├── scripts/
│   ├── setup_conda.sh  # One-time conda environment setup
│   └── sync_to_s3df.sh # Rsync project files to S3DF
```
