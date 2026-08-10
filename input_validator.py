"""
Input Validation Layer for Hospital Readmission Prediction Model
-----------------------------------------------------------------
Validates all inputs before passing to the model.
Catches invalid, illogical, and dangerous data.

Usage:
    from input_validator import validate_patient_data
    
    is_valid, errors = validate_patient_data(patient_df)
    if not is_valid:
        print("Validation errors:", errors)
    else:
        predictions = model.predict(patient_df)
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict

# ============================================================================
# VALIDATION RULES - Clinical and Logical Constraints
# ============================================================================

VALIDATION_RULES = {
    # Numeric ranges (min, max)
    'age': (0, 120, "Age must be between 0 and 120 years"),
    'bmi': (10, 100, "BMI must be between 10 and 100"),
    'comorbidity_index': (0, 37, "Charlson Comorbidity Index must be between 0 and 37"),
    'length_of_stay_days': (0, 365, "Length of stay must be between 0 and 365 days"),
    'medication_count_at_discharge': (0, 50, "Medication count must be between 0 and 50"),
    'previous_admissions_12m': (0, 100, "Previous admissions must be between 0 and 100"),
    'previous_er_visits_12m': (0, 200, "ER visits must be between 0 and 200"),
    'total_charges_index_stay': (0, 1000000, "Total charges must be between $0 and $1,000,000"),
    
    # Lab values (clinical ranges)
    'hemoglobin': (3, 25, "Hemoglobin must be between 3-25 g/dL"),
    'creatinine': (0.1, 30, "Creatinine must be between 0.1-30 mg/dL"),
    'glucose': (20, 1000, "Glucose must be between 20-1000 mg/dL"),
    'hbA1c': (3, 18, "HbA1c must be between 3-18%"),
    'wbc_count': (0.5, 100, "WBC count must be between 0.5-100 K/uL"),
    'total_bilirubin': (0.1, 50, "Bilirubin must be between 0.1-50 mg/dL"),
}

# Binary flags (must be 0 or 1)
BINARY_FLAGS = [
    'sex',
    'diabetes_flag',
    'heart_failure_flag',
    'copd_flag',
    'ckd_flag',
    'cancer_flag',
    'dementia_flag',
    'prior_30_day_readmission_flag',
    'icu_stay_flag',
    'polypharmacy_flag',
    'high_risk_medication_flag',
    'follow_up_within_7_days_flag'
]

# Categorical values
VALID_CATEGORIES = {
    'admission_type': ['elective', 'emergency', 'urgent'],
    'discharge_destination': ['home', 'nursing_home', 'rehab', 'other'],
    'insurance_type': ['Medicare', 'Medicaid', 'Private', 'Self-pay']
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_patient_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate patient data before model prediction.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Patient data with required features
        
    Returns:
    --------
    is_valid : bool
        True if all validation passes
    errors : List[str]
        List of validation error messages
    """
    errors = []
    
    # Make a copy to avoid modifying original
    data = df.copy()
    
    # Check 1: Missing data in critical features
    critical_features = ['age', 'comorbidity_index', 'medication_count_at_discharge']
    for feat in critical_features:
        if feat in data.columns:
            if data[feat].isna().any():
                errors.append(f"❌ CRITICAL: Missing values in {feat} (required feature)")
    
    # Check 2: Numeric range validation
    for col, (min_val, max_val, message) in VALIDATION_RULES.items():
        if col in data.columns:
            # Check for NaN first
            if data[col].isna().any():
                errors.append(f"❌ {col}: Contains missing values (NaN)")
                continue
            
            # Check range
            invalid_low = data[col] < min_val
            invalid_high = data[col] > max_val
            
            if invalid_low.any():
                bad_values = data.loc[invalid_low, col].tolist()
                errors.append(f"❌ {col}: Values below minimum {min_val}: {bad_values[:3]}... ({invalid_low.sum()} rows)")
            
            if invalid_high.any():
                bad_values = data.loc[invalid_high, col].tolist()
                errors.append(f"❌ {col}: Values above maximum {max_val}: {bad_values[:3]}... ({invalid_high.sum()} rows)")
    
    # Check 3: Binary flag validation
    for flag in BINARY_FLAGS:
        if flag in data.columns:
            if data[flag].isna().any():
                errors.append(f"❌ {flag}: Contains missing values (must be 0 or 1)")
                continue
            
            invalid = ~data[flag].isin([0, 1])
            if invalid.any():
                bad_values = data.loc[invalid, flag].unique().tolist()
                errors.append(f"❌ {flag}: Invalid values (must be 0 or 1): {bad_values} ({invalid.sum()} rows)")
    
    # Check 4: Categorical validation
    for col, valid_vals in VALID_CATEGORIES.items():
        if col in data.columns:
            if data[col].isna().any():
                errors.append(f"❌ {col}: Contains missing values")
                continue
            
            invalid = ~data[col].isin(valid_vals)
            if invalid.any():
                bad_values = data.loc[invalid, col].unique().tolist()
                errors.append(f"❌ {col}: Invalid categories {bad_values} (valid: {valid_vals})")
    
    # Check 5: Logical consistency checks
    consistency_errors = check_logical_consistency(data)
    errors.extend(consistency_errors)
    
    # Check 6: Extreme outliers (warnings, not hard errors)
    outlier_warnings = detect_outliers(data)
    if outlier_warnings:
        errors.append("\n⚠️  WARNINGS - Extreme values detected (may be valid but unusual):")
        errors.extend(outlier_warnings)
    
    is_valid = len([e for e in errors if e.startswith("❌")]) == 0
    
    return is_valid, errors


def check_logical_consistency(df: pd.DataFrame) -> List[str]:
    """Check for logically inconsistent combinations"""
    errors = []
    
    # Check 1: Polypharmacy flag consistency
    if 'polypharmacy_flag' in df.columns and 'medication_count_at_discharge' in df.columns:
        inconsistent = (df['polypharmacy_flag'] == 1) & (df['medication_count_at_discharge'] < 5)
        if inconsistent.any():
            errors.append(
                f"❌ INCONSISTENT: Polypharmacy flag=1 but medication count < 5 ({inconsistent.sum()} rows)"
            )
    
    # Check 2: ICU stay requires non-zero length of stay
    if 'icu_stay_flag' in df.columns and 'length_of_stay_days' in df.columns:
        inconsistent = (df['icu_stay_flag'] == 1) & (df['length_of_stay_days'] == 0)
        if inconsistent.any():
            errors.append(
                f"❌ INCONSISTENT: ICU stay flag=1 but length of stay = 0 ({inconsistent.sum()} rows)"
            )
    
    # Check 3: Medicare typically for elderly (soft check)
    if 'insurance_type' in df.columns and 'age' in df.columns:
        unusual = (df['insurance_type'] == 'Medicare') & (df['age'] < 18)
        if unusual.any():
            errors.append(
                f"⚠️  UNUSUAL: Medicare insurance for patients under 18 ({unusual.sum()} rows) - may be valid (disability)"
            )
    
    # Check 4: Very short ICU stays are unusual
    if 'icu_stay_flag' in df.columns and 'length_of_stay_days' in df.columns and 'discharge_destination' in df.columns:
        unusual = (df['icu_stay_flag'] == 1) & (df['length_of_stay_days'] == 1) & (df['discharge_destination'] == 'home')
        if unusual.any():
            errors.append(
                f"⚠️  UNUSUAL: ICU stay with 1-day length and discharged home ({unusual.sum()} rows)"
            )
    
    # Check 5: Infant with high comorbidities
    if 'age' in df.columns and 'comorbidity_index' in df.columns:
        unusual = (df['age'] < 5) & (df['comorbidity_index'] > 10)
        if unusual.any():
            errors.append(
                f"⚠️  UNUSUAL: Child under 5 with comorbidity index > 10 ({unusual.sum()} rows)"
            )
    
    return errors


def detect_outliers(df: pd.DataFrame) -> List[str]:
    """Detect extreme outliers (not errors, just warnings)"""
    warnings = []
    
    # Age outliers
    if 'age' in df.columns:
        extreme = df['age'] > 100
        if extreme.any():
            warnings.append(f"  • Age > 100: {extreme.sum()} patients (verify data quality)")
    
    # BMI outliers
    if 'bmi' in df.columns:
        extreme_low = df['bmi'] < 15
        extreme_high = df['bmi'] > 60
        if extreme_low.any():
            warnings.append(f"  • BMI < 15 (severe underweight): {extreme_low.sum()} patients")
        if extreme_high.any():
            warnings.append(f"  • BMI > 60 (severe obesity): {extreme_high.sum()} patients")
    
    # Lab value outliers (potentially lethal)
    if 'glucose' in df.columns:
        extreme = df['glucose'] > 600
        if extreme.any():
            warnings.append(f"  • Glucose > 600 (severe hyperglycemia): {extreme.sum()} patients")
    
    if 'creatinine' in df.columns:
        extreme = df['creatinine'] > 10
        if extreme.any():
            warnings.append(f"  • Creatinine > 10 (severe kidney failure): {extreme.sum()} patients")
    
    if 'hemoglobin' in df.columns:
        extreme_low = df['hemoglobin'] < 6
        if extreme_low.any():
            warnings.append(f"  • Hemoglobin < 6 (severe anemia): {extreme_low.sum()} patients")
    
    # High utilization
    if 'previous_admissions_12m' in df.columns:
        extreme = df['previous_admissions_12m'] > 50
        if extreme.any():
            warnings.append(f"  • Previous admissions > 50/year: {extreme.sum()} patients (verify data)")
    
    return warnings


def get_validation_summary(errors: List[str]) -> Dict:
    """Generate summary statistics from validation errors"""
    critical_errors = [e for e in errors if e.startswith("❌")]
    warnings = [e for e in errors if e.startswith("⚠️")]
    
    return {
        'total_issues': len(errors),
        'critical_errors': len(critical_errors),
        'warnings': len(warnings),
        'is_valid': len(critical_errors) == 0,
        'details': errors
    }


# ============================================================================
# SAFE PREDICTION WRAPPER
# ============================================================================

def safe_predict(model, patient_data: pd.DataFrame, return_proba: bool = True):
    """
    Safely make predictions with input validation.
    
    Parameters:
    -----------
    model : sklearn model
        Trained model
    patient_data : pd.DataFrame
        Patient features
    return_proba : bool
        If True, return probabilities; if False, return binary predictions
        
    Returns:
    --------
    predictions : np.array or None
        Model predictions if valid, None if validation fails
    validation_errors : List[str]
        List of validation errors (empty if valid)
    """
    # Validate input
    is_valid, errors = validate_patient_data(patient_data)
    
    if not is_valid:
        print("❌ VALIDATION FAILED - Cannot make predictions")
        print("\nErrors found:")
        for error in errors:
            print(f"  {error}")
        return None, errors
    
    # Check for warnings
    warnings = [e for e in errors if e.startswith("⚠️")]
    if warnings:
        print("⚠️  Validation passed with warnings:")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    # Make predictions
    try:
        if return_proba:
            predictions = model.predict_proba(patient_data)[:, 1]
        else:
            predictions = model.predict(patient_data)
        
        return predictions, errors
    
    except Exception as e:
        error_msg = f"❌ PREDICTION ERROR: {type(e).__name__}: {str(e)}"
        return None, [error_msg]


# ============================================================================
# COMMAND-LINE TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("INPUT VALIDATOR - DEMO")
    print("="*80 + "\n")
    
    # Load sample data
    df = pd.read_csv("patient_data_final.csv")
    sample = df.drop(columns=['patient_id', 'readmitted_30_days', 'drg_code']).iloc[0:5]
    
    print("Test 1: Valid data")
    print("-" * 80)
    is_valid, errors = validate_patient_data(sample)
    if is_valid:
        print("✅ PASSED - All validation checks passed")
    else:
        print("❌ FAILED")
        for error in errors:
            print(f"  {error}")
    print()
    
    print("Test 2: Invalid data (negative age)")
    print("-" * 80)
    invalid_sample = sample.copy()
    invalid_sample['age'] = -25
    is_valid, errors = validate_patient_data(invalid_sample)
    if is_valid:
        print("✅ PASSED")
    else:
        print("❌ FAILED (as expected)")
        for error in errors:
            print(f"  {error}")
    print()
    
    print("Test 3: Invalid data (extreme BMI)")
    print("-" * 80)
    invalid_sample = sample.copy()
    invalid_sample['bmi'] = 250
    is_valid, errors = validate_patient_data(invalid_sample)
    if is_valid:
        print("✅ PASSED")
    else:
        print("❌ FAILED (as expected)")
        for error in errors:
            print(f"  {error}")
    print()
    
    print("Test 4: Inconsistent data (polypharmacy flag)")
    print("-" * 80)
    invalid_sample = sample.copy()
    invalid_sample['polypharmacy_flag'] = 1
    invalid_sample['medication_count_at_discharge'] = 2
    is_valid, errors = validate_patient_data(invalid_sample)
    if is_valid:
        print("✅ PASSED")
    else:
        print("❌ FAILED (as expected)")
        for error in errors:
            print(f"  {error}")
    print()
    
    print("Test 5: Missing critical data")
    print("-" * 80)
    invalid_sample = sample.copy()
    invalid_sample['age'] = np.nan
    is_valid, errors = validate_patient_data(invalid_sample)
    if is_valid:
        print("✅ PASSED")
    else:
        print("❌ FAILED (as expected)")
        for error in errors:
            print(f"  {error}")
    print()
    
    print("="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nUsage in production:")
    print("  from input_validator import safe_predict")
    print("  predictions, errors = safe_predict(model, patient_data)")
    print()
