#!/bin/bash
# =============================================================================
# Script 1: Setup AWS Credentials and Verify Configuration
# =============================================================================

set -e  # Exit on error

echo "======================================================================"
echo "🚀 Step 1: AWS Setup and Verification"
echo "======================================================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Installing..."
    brew install awscli
fi

echo "✅ AWS CLI found: $(aws --version)"

# Configure AWS credentials
echo ""
echo "📝 Configuring AWS credentials..."

aws configure set aws_access_key_id "AKIAVJHDQ2AV6INYN2F4"
aws configure set aws_secret_access_key "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"
aws configure set default.region "us-east-1"
aws configure set default.output "json"

echo "✅ AWS credentials configured"

# Verify credentials
echo ""
echo "🔍 Verifying AWS access..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "❌ Failed to verify AWS credentials"
    exit 1
fi

echo "✅ AWS Account ID: $AWS_ACCOUNT_ID"

# Check Terraform installation
echo ""
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Installing..."
    brew tap hashicorp/tap
    brew install hashicorp/tap/terraform
fi

echo "✅ Terraform found: $(terraform version | head -n 1)"

# Check Docker installation
echo ""
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker found: $(docker --version)"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is running"

echo ""
echo "======================================================================"
echo "✅ AWS Setup Complete!"
echo "======================================================================"
echo ""
echo "Next step: Run ./scripts/02-deploy-infrastructure.sh"
echo ""
