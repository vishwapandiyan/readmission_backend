#!/bin/bash
# =============================================================================
# Populate Database with Sample Patients via API
# =============================================================================

set -e

API_URL="https://readmission-alb-prod-380705514.us-east-1.elb.amazonaws.com"
USERNAME="admin"
PASSWORD="Admin123"

echo "======================================================================"
echo "📊 Populating Database with Sample Patients"
echo "======================================================================"

# Login and get token
echo ""
echo "🔐 Authenticating..."
TOKEN=$(curl -k -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
    | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✅ Authenticated successfully"

# Create sample patients
echo ""
echo "📝 Creating sample patients..."

# Patient 1: High Risk - Elderly with multiple comorbidities
echo "Creating Patient 1 (High Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "John Smith",
        "age": 78,
        "sex": 1,
        "insurance_type": "Medicare",
        "admission_type_id": 1,
        "discharge_disposition_id": 1,
        "admission_source_id": 7,
        "time_in_hospital": 7,
        "num_lab_procedures": 45,
        "num_procedures": 3,
        "num_medications": 15,
        "number_outpatient": 2,
        "number_emergency": 3,
        "number_inpatient": 1,
        "diag_1": 414,
        "diag_2": 250,
        "diag_3": 428,
        "number_diagnoses": 9,
        "max_glu_serum": 1,
        "A1Cresult": 1,
        "metformin": 1,
        "insulin": 1,
        "diabetesMed": 1,
        "change": 1,
        "readmitted": 1
    }' | jq -r '.patient_id' > /dev/null

# Patient 2: Moderate Risk
echo "Creating Patient 2 (Moderate Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "Mary Johnson",
        "age": 65,
        "sex": 0,
        "insurance_type": "Medicare",
        "admission_type_id": 2,
        "discharge_disposition_id": 1,
        "admission_source_id": 1,
        "time_in_hospital": 4,
        "num_lab_procedures": 30,
        "num_procedures": 1,
        "num_medications": 10,
        "number_outpatient": 1,
        "number_emergency": 1,
        "number_inpatient": 0,
        "diag_1": 250,
        "diag_2": 401,
        "diag_3": 272,
        "number_diagnoses": 7,
        "max_glu_serum": 1,
        "A1Cresult": 2,
        "metformin": 1,
        "insulin": 0,
        "diabetesMed": 1,
        "change": 1,
        "readmitted": 0
    }' | jq -r '.patient_id' > /dev/null

# Patient 3: Low Risk - Young and healthy
echo "Creating Patient 3 (Low Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "Sarah Williams",
        "age": 35,
        "sex": 0,
        "insurance_type": "Private",
        "admission_type_id": 3,
        "discharge_disposition_id": 1,
        "admission_source_id": 1,
        "time_in_hospital": 2,
        "num_lab_procedures": 15,
        "num_procedures": 0,
        "num_medications": 5,
        "number_outpatient": 0,
        "number_emergency": 0,
        "number_inpatient": 0,
        "diag_1": 250,
        "diag_2": 0,
        "diag_3": 0,
        "number_diagnoses": 3,
        "max_glu_serum": 0,
        "A1Cresult": 0,
        "metformin": 0,
        "insulin": 0,
        "diabetesMed": 1,
        "change": 0,
        "readmitted": 0
    }' | jq -r '.patient_id' > /dev/null

# Patient 4: High Risk - Multiple ER visits
echo "Creating Patient 4 (High Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "Robert Brown",
        "age": 72,
        "sex": 1,
        "insurance_type": "Medicare",
        "admission_type_id": 1,
        "discharge_disposition_id": 1,
        "admission_source_id": 7,
        "time_in_hospital": 10,
        "num_lab_procedures": 55,
        "num_procedures": 4,
        "num_medications": 20,
        "number_outpatient": 3,
        "number_emergency": 5,
        "number_inpatient": 2,
        "diag_1": 428,
        "diag_2": 414,
        "diag_3": 250,
        "number_diagnoses": 9,
        "max_glu_serum": 2,
        "A1Cresult": 2,
        "metformin": 1,
        "insulin": 1,
        "diabetesMed": 1,
        "change": 1,
        "readmitted": 1
    }' | jq -r '.patient_id' > /dev/null

# Patient 5: Moderate Risk
echo "Creating Patient 5 (Moderate Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "Patricia Davis",
        "age": 58,
        "sex": 0,
        "insurance_type": "Private",
        "admission_type_id": 2,
        "discharge_disposition_id": 1,
        "admission_source_id": 1,
        "time_in_hospital": 5,
        "num_lab_procedures": 35,
        "num_procedures": 2,
        "num_medications": 12,
        "number_outpatient": 2,
        "number_emergency": 2,
        "number_inpatient": 1,
        "diag_1": 250,
        "diag_2": 428,
        "diag_3": 401,
        "number_diagnoses": 8,
        "max_glu_serum": 1,
        "A1Cresult": 1,
        "metformin": 1,
        "insulin": 1,
        "diabetesMed": 1,
        "change": 1,
        "readmitted": 0
    }' | jq -r '.patient_id' > /dev/null

# Patient 6: Low Risk
echo "Creating Patient 6 (Low Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "Michael Wilson",
        "age": 42,
        "sex": 1,
        "insurance_type": "Private",
        "admission_type_id": 3,
        "discharge_disposition_id": 1,
        "admission_source_id": 1,
        "time_in_hospital": 3,
        "num_lab_procedures": 20,
        "num_procedures": 1,
        "num_medications": 7,
        "number_outpatient": 0,
        "number_emergency": 0,
        "number_inpatient": 0,
        "diag_1": 250,
        "diag_2": 401,
        "diag_3": 0,
        "number_diagnoses": 4,
        "max_glu_serum": 0,
        "A1Cresult": 0,
        "metformin": 1,
        "insulin": 0,
        "diabetesMed": 1,
        "change": 0,
        "readmitted": 0
    }' | jq -r '.patient_id' > /dev/null

# Patient 7: High Risk - Long hospital stay
echo "Creating Patient 7 (High Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "Linda Martinez",
        "age": 81,
        "sex": 0,
        "insurance_type": "Medicare",
        "admission_type_id": 1,
        "discharge_disposition_id": 2,
        "admission_source_id": 7,
        "time_in_hospital": 14,
        "num_lab_procedures": 65,
        "num_procedures": 5,
        "num_medications": 22,
        "number_outpatient": 4,
        "number_emergency": 4,
        "number_inpatient": 3,
        "diag_1": 414,
        "diag_2": 428,
        "diag_3": 250,
        "number_diagnoses": 9,
        "max_glu_serum": 2,
        "A1Cresult": 2,
        "metformin": 1,
        "insulin": 1,
        "diabetesMed": 1,
        "change": 1,
        "readmitted": 1
    }' | jq -r '.patient_id' > /dev/null

# Patient 8: Low Risk
echo "Creating Patient 8 (Low Risk)..."
curl -k -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "James Anderson",
        "age": 39,
        "sex": 1,
        "insurance_type": "Private",
        "admission_type_id": 3,
        "discharge_disposition_id": 1,
        "admission_source_id": 1,
        "time_in_hospital": 2,
        "num_lab_procedures": 18,
        "num_procedures": 0,
        "num_medications": 6,
        "number_outpatient": 0,
        "number_emergency": 0,
        "number_inpatient": 0,
        "diag_1": 250,
        "diag_2": 272,
        "diag_3": 0,
        "number_diagnoses": 3,
        "max_glu_serum": 0,
        "A1Cresult": 0,
        "metformin": 1,
        "insulin": 0,
        "diabetesMed": 1,
        "change": 0,
        "readmitted": 0
    }' | jq -r '.patient_id' > /dev/null

echo ""
echo "✅ Created 8 sample patients"

# Verify
echo ""
echo "🔍 Verifying database..."
STATS=$(curl -k -s -X GET "$API_URL/api/v1/patients/stats/summary" \
    -H "Authorization: Bearer $TOKEN")

echo "$STATS" | jq '.'

echo ""
echo "======================================================================"
echo "✅ Database Population Complete!"
echo "======================================================================"
echo ""
echo "You can now view patients in the frontend:"
echo "https://d578gwwut8r88.cloudfront.net"
echo ""
