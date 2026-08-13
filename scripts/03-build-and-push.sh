#!/bin/bash
# =============================================================================
# Script 3: Build Docker Image and Push to ECR
# =============================================================================

set -e

echo "======================================================================"
echo "🐳 Step 3: Building and Pushing Docker Image"
echo "======================================================================"

cd "$(dirname "$0")/.."

# Get ECR repository URL from Terraform
ECR_REPO=$(cd terraform && terraform output -raw ecr_repository_url)
AWS_REGION=$(cd terraform && terraform output -raw aws_region || echo "us-east-1")
IMAGE_TAG="v1.0.0"

echo ""
echo "📝 Configuration:"
echo "   ECR Repository: $ECR_REPO"
echo "   AWS Region: $AWS_REGION"
echo "   Image Tag: $IMAGE_TAG"

# Login to ECR
echo ""
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REPO

# Build Docker image
echo ""
echo "🔨 Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -t readmission-backend:$IMAGE_TAG -f Dockerfile .

# Tag image for ECR
echo ""
echo "🏷️  Tagging image..."
docker tag readmission-backend:$IMAGE_TAG $ECR_REPO:$IMAGE_TAG
docker tag readmission-backend:$IMAGE_TAG $ECR_REPO:latest

# Push to ECR
echo ""
echo "⬆️  Pushing image to ECR..."
docker push $ECR_REPO:$IMAGE_TAG
docker push $ECR_REPO:latest

echo ""
echo "======================================================================"
echo "✅ Docker Image Pushed Successfully!"
echo "======================================================================"
echo ""
echo "Image: $ECR_REPO:latest"
echo ""
echo "Next step: Run ./scripts/04-update-ecs-service.sh"
echo ""
