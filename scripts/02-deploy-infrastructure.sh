#!/bin/bash
# =============================================================================
# Script 2: Deploy AWS Infrastructure with Terraform
# =============================================================================

set -e

echo "======================================================================"
echo "🏗️  Step 2: Deploying AWS Infrastructure"
echo "======================================================================"

cd "$(dirname "$0")/../terraform"

# Initialize Terraform
echo ""
echo "📦 Initializing Terraform..."
terraform init

# Validate configuration
echo ""
echo "🔍 Validating Terraform configuration..."
terraform validate

if [ $? -ne 0 ]; then
    echo "❌ Terraform validation failed"
    exit 1
fi

echo "✅ Terraform configuration is valid"

# Plan deployment
echo ""
echo "📋 Creating deployment plan..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "🤔 Do you want to proceed with deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Apply infrastructure
echo ""
echo "🚀 Deploying infrastructure (this will take 10-15 minutes)..."
terraform apply tfplan

echo ""
echo "======================================================================"
echo "✅ Infrastructure Deployed Successfully!"
echo "======================================================================"
echo ""

# Display outputs
terraform output deployment_instructions

echo ""
echo "Next step: Run ./scripts/03-build-and-push.sh"
echo ""
