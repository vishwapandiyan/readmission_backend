#!/bin/bash
# Create a test patient with all fields populated

API_URL="https://d32v6jeaav1zgo.cloudfront.net"

echo "Creating test patient with complete data..."

# Login
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"Admin123"}' \
    | jq -r '.access_token')

# Create patient
RESULT=$(curl -s -X POST "$API_URL/api/v1/patients/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "full_name": "Jane Anderson",
        "age": 72,
        "sex": 0,
        "bmi": 29.5,
        "insurance_type": "Medicare",
        "admission_type": "emergency",
        "discharge_destination": "home",
        "comorbidity_index": 5,
        "diabetes_flag": 1,
        "heart_failure_flag": 1,
        "copd_flag": 0,
        "ckd_flag": 1,
        "cancer_flag": 0,
        "dementia_flag": 0,
        "previous_admissions_12m": 2,
        "previous_er_visits_12m": 3,
        "prior_30_day_readmission_flag": 0,
        "length_of_stay_days": 6,
        "icu_stay_flag": 1,
        "medication_count_at_discharge": 12,
        "polypharmacy_flag": 1,
        "high_risk_medication_flag": 1,
        "hemoglobin": 11.2,
        "creatinine": 1.8,
        "glucose": 165,
        "hba1c": 8.2,
        "wbc_count": 9.5,
        "total_bilirubin": 1.1,
        "follow_up_within_7_days_flag": 1,
        "total_charges_index_stay": 45000,
        "drg_code": "291",
        "contact_number": "+1 (555) 234-5678",
        "emergency_contact": "John Anderson - +1 (555) 234-9999",
        "auto_predict": true
    }')

PATIENT_ID=$(echo "$RESULT" | jq -r '.patient_id')
RISK=$(echo "$RESULT" | jq -r '.prediction.layer1_prediction.probability')

echo "✅ Patient created:"
echo "   ID: $PATIENT_ID"
echo "   Name: Jane Anderson"
echo "   Risk: $(echo "$RISK * 100" | bc -l | cut -c1-5)%"
echo ""
echo "View at: https://d578gwwut8r88.cloudfront.net/app/patients/$PATIENT_ID"
