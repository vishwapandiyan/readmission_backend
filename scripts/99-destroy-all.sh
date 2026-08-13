#!/bin/bash
# =============================================================================
# Cleanup Script - Destroy All AWS Resources
# =============================================================================

set -e

echo ""
echo "======================================================================"
echo "⚠️  WARNING: DESTROY ALL RESOURCES"
echo "======================================================================"
echo ""
echo "This will DELETE:"
echo "  • RDS Database (including all patient data)"
echo "  • ECS Cluster and Service"
echo "  • EC2 Instances"
echo "  • ECR Repository (Docker images)"
echo "  • S3 Bucket (frontend files)"
echo "  • CloudFront Distribution"
echo "  • VPC and all networking"
echo "  • All data will be PERMANENTLY LOST"
echo ""

read -p "⚠️  Type 'DELETE' to confirm: " confirm

if [ "$confirm" != "DELETE" ]; then
    echo "❌ Destruction cancelled"
    exit 0
fi

cd "$(dirname "$0")/../terraform"

echo ""
echo "🗑️  Destroying infrastructure..."
terraform destroy -auto-approve

echo ""
echo "======================================================================"
echo "✅ All Resources Destroyed"
echo "======================================================================"
echo ""
