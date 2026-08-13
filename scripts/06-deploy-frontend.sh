#!/bin/bash
# =============================================================================
# Script 6: Build and Deploy Frontend to S3/CloudFront
# =============================================================================

set -e

echo "======================================================================"
echo "🎨 Step 6: Deploying Frontend"
echo "======================================================================"

# Get infrastructure outputs
cd "$(dirname "$0")/../terraform"
S3_BUCKET=$(terraform output -raw s3_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_domain_name)

# Get EC2 instance public IP for API endpoint
echo ""
echo "🔍 Finding ECS instance public IP..."
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
INSTANCE_ID=$(aws ecs list-container-instances \
    --cluster $CLUSTER_NAME \
    --query 'containerInstanceArns[0]' \
    --output text | awk -F'/' '{print $NF}')

EC2_INSTANCE_ID=$(aws ecs describe-container-instances \
    --cluster $CLUSTER_NAME \
    --container-instances $INSTANCE_ID \
    --query 'containerInstances[0].ec2InstanceId' \
    --output text)

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $EC2_INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

API_URL="http://$PUBLIC_IP:8000"

echo ""
echo "📝 Configuration:"
echo "   S3 Bucket: $S3_BUCKET"
echo "   CloudFront: $CLOUDFRONT_URL"
echo "   API URL: $API_URL"

# Build frontend
cd ../../frontendread/care-insight-predict

echo ""
echo "📦 Installing frontend dependencies..."
npm install

# Create production environment file
echo ""
echo "🔧 Creating production environment file..."
cat > .env.production << EOF
VITE_API_BASE_URL=$API_URL
VITE_ENVIRONMENT=production
EOF

# Build
echo ""
echo "🔨 Building frontend..."
npm run build

# Deploy to S3
echo ""
echo "⬆️  Uploading to S3..."
aws s3 sync dist/ s3://$S3_BUCKET/ --delete

# Invalidate CloudFront cache
echo ""
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_ID \
    --paths "/*" \
    --no-cli-pager

echo ""
echo "======================================================================"
echo "✅ Frontend Deployed Successfully!"
echo "======================================================================"
echo ""
echo "🌐 Frontend URL: https://$CLOUDFRONT_URL"
echo "🔌 API URL: $API_URL"
echo ""
echo "🎉 Deployment Complete! Your application is now live!"
echo ""
echo "Default login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
