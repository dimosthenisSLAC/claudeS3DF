#!/bin/bash
# Sync this project to your S3DF home directory.
# Usage: bash scripts/sync_to_s3df.sh

set -euo pipefail

REMOTE="s3df-iana"
REMOTE_DIR="/sdf/home/d/dsokaras/claudeS3DF"

echo "Syncing to $REMOTE:$REMOTE_DIR ..."

rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
    -e ssh \
    "$(dirname "$(dirname "$0")")/" \
    "$REMOTE:$REMOTE_DIR/"

echo "Done. Files synced to $REMOTE:$REMOTE_DIR"
echo ""
echo "Next steps on S3DF:"
echo "  ssh s3df-iana"
echo "  cd $REMOTE_DIR"
echo "  sbatch jobs/test_gpu.sh"
