#!/bin/bash
# =============================================================================
# Master Deployment Script - Deploy Everything in One Go
# =============================================================================

set -e

echo ""
echo "======================================================================"
echo "🚀 Hospital Readmission System - Complete AWS Deployment"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Setup AWS credentials"
echo "  2. Deploy infrastructure (VPC, RDS, ECS, S3, CloudFront)"
echo "  3. Build and push Docker image"
echo "  4. Update ECS service"
echo "  5. Restore database (40,000 patients)"
echo "  6. Deploy frontend"
echo ""
echo "Estimated time: 25-30 minutes"
echo ""

read -p "🤔 Ready to start deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Step 1: Setup
echo ""
bash "$SCRIPT_DIR/01-setup-aws.sh"

# Step 2: Deploy Infrastructure
echo ""
bash "$SCRIPT_DIR/02-deploy-infrastructure.sh"

# Step 3: Build and Push
echo ""
bash "$SCRIPT_DIR/03-build-and-push.sh"

# Step 4: Update ECS
echo ""
bash "$SCRIPT_DIR/04-update-ecs-service.sh"

# Step 5: Restore Database
echo ""
bash "$SCRIPT_DIR/05-restore-database.sh"

# Step 6: Deploy Frontend
echo ""
bash "$SCRIPT_DIR/06-deploy-frontend.sh"

echo ""
echo "======================================================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================================================================"
echo ""
echo "Your application is now live and running on AWS!"
echo ""
echo "📊 View your deployment:"
cd "$SCRIPT_DIR/../terraform"
terraform output frontend_url
echo ""
