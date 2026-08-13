#!/bin/bash
# =============================================================================
# Restore Database from ECS Container (has network access to RDS)
# =============================================================================

set -e

echo "======================================================================"
echo "💾 Restoring Database from ECS Container"
echo "======================================================================"

cd "$(dirname "$0")/../terraform"

# Get ECS task info
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

# Get database info
DB_ENDPOINT=$(terraform output -raw rds_endpoint | sed 's/:5432//')
DB_NAME=$(terraform output -raw rds_database_name)
DB_USER=$(terraform output -raw rds_username)
SECRET_ARN=$(terraform output -raw rds_password_secret_arn)

echo ""
echo "📝 Configuration:"
echo "   Cluster: $CLUSTER_NAME"
echo "   Service: $SERVICE_NAME"
echo "   Database: $DB_ENDPOINT"

# Get password from Secrets Manager
echo ""
echo "🔐 Retrieving database password..."
DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id $SECRET_ARN \
    --query SecretString \
    --output text | jq -r '.password')

# Get running task ARN
echo ""
echo "🔍 Finding running ECS task..."
TASK_ARN=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --desired-status RUNNING \
    --query 'taskArns[0]' \
    --output text)

if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
    echo "❌ No running tasks found"
    exit 1
fi

echo "✅ Found task: ${TASK_ARN##*/}"

# Copy dump file to S3 temporarily
cd ..
S3_BUCKET="readmission-temp-$(date +%s)"
echo ""
echo "📤 Uploading dump to S3..."
aws s3 mb s3://$S3_BUCKET --region us-east-1
aws s3 cp readmission_db_dump.sql.gz s3://$S3_BUCKET/

# Execute restore command in container
echo ""
echo "📥 Restoring database from ECS container..."

aws ecs execute-command \
    --cluster $CLUSTER_NAME \
    --task $TASK_ARN \
    --container readmission-backend \
    --interactive \
    --command "/bin/bash -c 'apt-get update -qq && apt-get install -y -qq postgresql-client awscli && \
aws s3 cp s3://$S3_BUCKET/readmission_db_dump.sql.gz /tmp/ && \
gunzip -c /tmp/readmission_db_dump.sql.gz | PGPASSWORD=$DB_PASSWORD psql -h $DB_ENDPOINT -U $DB_USER -d $DB_NAME -q && \
echo Database restored successfully'"

# Clean up S3
echo ""
echo "🧹 Cleaning up..."
aws s3 rm s3://$S3_BUCKET/readmission_db_dump.sql.gz
aws s3 rb s3://$S3_BUCKET

echo ""
echo "======================================================================"
echo "✅ Database Restored Successfully!"
echo "======================================================================"
