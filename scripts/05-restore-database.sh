#!/bin/bash
# =============================================================================
# Script 5: Restore Database from Dump
# =============================================================================

set -e

echo "======================================================================"
echo "💾 Step 5: Restoring Database"
echo "======================================================================"

cd "$(dirname "$0")/../terraform"

# Get database credentials
DB_ENDPOINT=$(terraform output -raw rds_endpoint | sed 's/:5432//')
DB_NAME=$(terraform output -raw rds_database_name)
DB_USER=$(terraform output -raw rds_username)
SECRET_ARN=$(terraform output -raw rds_password_secret_arn)

echo ""
echo "📝 Database Configuration:"
echo "   Endpoint: $DB_ENDPOINT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"

# Get password from Secrets Manager
echo ""
echo "🔐 Retrieving database password from Secrets Manager..."
DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id $SECRET_ARN \
    --query SecretString \
    --output text | jq -r '.password')

# Check if dump file exists
cd ..
if [ ! -f "readmission_db_dump.sql.gz" ]; then
    echo "❌ Database dump file not found: readmission_db_dump.sql.gz"
    exit 1
fi

echo "✅ Found database dump: readmission_db_dump.sql.gz (2.2 MB)"

# Install PostgreSQL client if not present
if ! command -v psql &> /dev/null; then
    echo ""
    echo "📦 Installing PostgreSQL client..."
    brew install libpq
fi

# Add libpq to PATH
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# Restore database
echo ""
echo "📥 Restoring database (this will take 2-3 minutes)..."
gunzip -c readmission_db_dump.sql.gz | \
    PGPASSWORD=$DB_PASSWORD psql \
    -h $DB_ENDPOINT \
    -U $DB_USER \
    -d $DB_NAME \
    -q

# Verify restoration
echo ""
echo "🔍 Verifying database restoration..."
PATIENT_COUNT=$(PGPASSWORD=$DB_PASSWORD psql \
    -h $DB_ENDPOINT \
    -U $DB_USER \
    -d $DB_NAME \
    -t -c "SELECT COUNT(*) FROM patients;")

echo "✅ Patients in database: $PATIENT_COUNT"

if [ "$PATIENT_COUNT" -lt "40000" ]; then
    echo "⚠️  Warning: Expected ~40,000 patients, found $PATIENT_COUNT"
fi

echo ""
echo "======================================================================"
echo "✅ Database Restored Successfully!"
echo "======================================================================"
echo ""
echo "Next step: Run ./scripts/06-deploy-frontend.sh"
echo ""
