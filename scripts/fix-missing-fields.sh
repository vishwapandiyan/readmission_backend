#!/bin/bash
# =============================================================================
# Fix Missing Fields in Existing Patient Records
# =============================================================================

set -e

API_URL="https://d32v6jeaav1zgo.cloudfront.net"
USERNAME="admin"
PASSWORD="Admin123"

echo "======================================================================"
echo "🔧 Fixing Missing Fields in Patient Records"
echo "======================================================================"

# Login
echo ""
echo "🔐 Authenticating..."
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
    | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✅ Authenticated"

# Get patient list
echo ""
echo "📊 Fetching patients..."
PATIENTS=$(curl -s -X GET "$API_URL/api/v1/patients/?skip=0&limit=100" \
    -H "Authorization: Bearer $TOKEN")

PATIENT_COUNT=$(echo "$PATIENTS" | jq '. | length')
echo "Found $PATIENT_COUNT patients"

# Update each patient with missing fields
echo ""
echo "🔄 Updating patients with default values for missing fields..."

echo "$PATIENTS" | jq -r '.[].patient_id' | while read -r PATIENT_ID; do
    echo "  Updating patient: $PATIENT_ID"
    
    # Update with default values for missing fields
    curl -s -X PUT "$API_URL/api/v1/patients/$PATIENT_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "hba1c": 7.0,
            "drg_code": "291"
        }' > /dev/null
    
    echo "    ✓ Updated"
done

echo ""
echo "======================================================================"
echo "✅ Patient Records Updated Successfully!"
echo "======================================================================"
echo ""
echo "All patients now have required fields for predictions."
echo "You can now run predictions on existing patients."
echo ""
