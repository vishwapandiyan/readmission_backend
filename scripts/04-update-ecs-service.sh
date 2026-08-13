#!/bin/bash
# =============================================================================
# Script 4: Update ECS Service with New Task Definition
# =============================================================================

set -e

echo "======================================================================"
echo "🔄 Step 4: Updating ECS Service"
echo "======================================================================"

cd "$(dirname "$0")/../terraform"

# Get values from Terraform
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

echo ""
echo "📝 Configuration:"
echo "   Cluster: $CLUSTER_NAME"
echo "   Service: $SERVICE_NAME"

# Force new deployment (pulls latest image)
echo ""
echo "🚀 Triggering new deployment..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment \
    --no-cli-pager

echo ""
echo "⏳ Waiting for service to stabilize (this may take 2-3 minutes)..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME

echo ""
echo "======================================================================"
echo "✅ ECS Service Updated Successfully!"
echo "======================================================================"
echo ""
echo "Next step: Run ./scripts/05-restore-database.sh"
echo ""
