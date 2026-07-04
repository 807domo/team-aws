#!/bin/bash
# ==============================================================================
# EhimeAI2026 デプロイスクリプト
# 
# Usage:
#   ./deploy/deploy.sh [staging|prod]
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - AWS SAM CLI installed
#   - Docker running (for building the Lambda image)
# ==============================================================================

set -euo pipefail

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
STACK_NAME="EhimeAI2026"
REGION="${AWS_REGION:-ap-northeast-1}"
ENVIRONMENT="${1:-prod}"
S3_DEPLOY_BUCKET="${S3_DEPLOY_BUCKET:-ehimeai2026-deploy-artifacts}"

echo "=============================================="
echo " EhimeAI2026 Deploy"
echo " Environment: ${ENVIRONMENT}"
echo " Region: ${REGION}"
echo " Stack: ${STACK_NAME}"
echo "=============================================="

# --------------------------------------------------------------------------
# Validate environment
# --------------------------------------------------------------------------
if [[ "${ENVIRONMENT}" != "prod" && "${ENVIRONMENT}" != "staging" ]]; then
    echo "ERROR: Environment must be 'prod' or 'staging'"
    exit 1
fi

# Check prerequisites
command -v sam >/dev/null 2>&1 || { echo "ERROR: AWS SAM CLI is required"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "ERROR: AWS CLI is required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker is required"; exit 1; }

# --------------------------------------------------------------------------
# Step 1: Build the SAM application
# --------------------------------------------------------------------------
echo ""
echo "[1/3] Building SAM application..."
sam build \
    --template-file "${SCRIPT_DIR}/template.yaml" \
    --build-dir "${PROJECT_ROOT}/.aws-sam/build" \
    --use-container

# --------------------------------------------------------------------------
# Step 2: Deploy with SAM
# --------------------------------------------------------------------------
echo ""
echo "[2/3] Deploying to AWS..."
sam deploy \
    --template-file "${PROJECT_ROOT}/.aws-sam/build/template.yaml" \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides "Environment=${ENVIRONMENT}" \
    --tags "Project=EhimeAI2026" \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset \
    --resolve-s3 \
    --resolve-image-repos

# --------------------------------------------------------------------------
# Step 3: Upload static files to S3
# --------------------------------------------------------------------------
echo ""
echo "[3/3] Uploading static files to S3..."

# Get the S3 bucket name from CloudFormation outputs
STATIC_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='StaticBucketName'].OutputValue" \
    --output text)

if [[ -n "${STATIC_BUCKET}" && "${STATIC_BUCKET}" != "None" ]]; then
    aws s3 sync "${PROJECT_ROOT}/app/static/" "s3://${STATIC_BUCKET}/static/" \
        --delete \
        --cache-control "public, max-age=86400" \
        --region "${REGION}"
    echo "Static files uploaded to: s3://${STATIC_BUCKET}/static/"
else
    echo "WARNING: Could not find static files bucket. Skipping upload."
fi

# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
echo ""
echo "=============================================="
echo " Deploy Complete!"
echo "=============================================="

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

echo " API URL: ${API_URL}"
echo " Static Bucket: ${STATIC_BUCKET:-N/A}"
echo "=============================================="
