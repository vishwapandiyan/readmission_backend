"""
Patient Management Models
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class InsuranceType(str, Enum):
    """Insurance type options"""
    MEDICARE = "Medicare"
    MEDICAID = "Medicaid"
    PRIVATE = "Private"
    SELF_PAY = "Self-pay"


class AdmissionType(str, Enum):
    """Admission type options"""
    ELECTIVE = "elective"
    EMERGENCY = "emergency"
    URGENT = "urgent"


class DischargeDestination(str, Enum):
    """Discharge destination options"""
    HOME = "home"
    NURSING_HOME = "nursing_home"
    REHAB = "rehab"
    OTHER = "other"


class PatientCreate(BaseModel):
    """Create patient with all details for prediction"""
    
    # Demographics
    patient_id: Optional[str] = Field(None, description="Patient ID (auto-generated if not provided)")
    age: int = Field(..., ge=18, le=120, description="Patient age")
    sex: Literal[0, 1] = Field(..., description="Sex: 0=Female, 1=Male")
    bmi: float = Field(..., ge=10, le=80, description="Body Mass Index")
    
    # Insurance & Admission
    insurance_type: InsuranceType = Field(..., description="Insurance type")
    admission_type: AdmissionType = Field(..., description="Type of admission")
    discharge_destination: DischargeDestination = Field(..., description="Discharge destination")
    
    # Clinical Conditions
    comorbidity_index: int = Field(..., ge=0, le=37, description="Charlson Comorbidity Index")
    diabetes_flag: Literal[0, 1] = Field(..., description="Diabetes: 0=No, 1=Yes")
    heart_failure_flag: Literal[0, 1] = Field(..., description="Heart Failure: 0=No, 1=Yes")
    copd_flag: Literal[0, 1] = Field(..., description="COPD: 0=No, 1=Yes")
    ckd_flag: Literal[0, 1] = Field(..., description="Chronic Kidney Disease: 0=No, 1=Yes")
    cancer_flag: Literal[0, 1] = Field(..., description="Cancer: 0=No, 1=Yes")
    dementia_flag: Literal[0, 1] = Field(..., description="Dementia: 0=No, 1=Yes")
    
    # Utilization History
    previous_admissions_12m: int = Field(..., ge=0, le=50, description="Admissions in past 12 months")
    previous_er_visits_12m: int = Field(..., ge=0, le=50, description="ER visits in past 12 months")
    prior_30_day_readmission_flag: Literal[0, 1] = Field(..., description="Prior 30-day readmission: 0=No, 1=Yes")
    
    # Current Hospitalization
    length_of_stay_days: int = Field(..., ge=1, le=365, description="Length of stay in days")
    icu_stay_flag: Literal[0, 1] = Field(..., description="ICU stay: 0=No, 1=Yes")
    
    # Medications
    medication_count_at_discharge: int = Field(..., ge=0, le=50, description="Number of medications")
    polypharmacy_flag: Literal[0, 1] = Field(..., description="Polypharmacy (5+ meds): 0=No, 1=Yes")
    high_risk_medication_flag: Literal[0, 1] = Field(..., description="High-risk medications: 0=No, 1=Yes")
    
    # Lab Values
    hemoglobin: float = Field(..., ge=3.0, le=20.0, description="Hemoglobin (g/dL)")
    creatinine: float = Field(..., ge=0.1, le=15.0, description="Creatinine (mg/dL)")
    glucose: int = Field(..., ge=30, le=600, description="Glucose (mg/dL)")
    hba1c: float = Field(..., ge=3.0, le=20.0, description="HbA1c (%)")
    wbc_count: float = Field(..., ge=0.1, le=50.0, description="WBC count (K/uL)")
    total_bilirubin: float = Field(..., ge=0.1, le=30.0, description="Total bilirubin (mg/dL)")
    
    # Follow-up & Charges
    follow_up_within_7_days_flag: Literal[0, 1] = Field(..., description="Follow-up scheduled: 0=No, 1=Yes")
    total_charges_index_stay: float = Field(..., ge=0, description="Total charges ($)")
    
    # DRG Code
    drg_code: Optional[str] = Field(None, description="DRG code")
    
    # Optional metadata
    full_name: Optional[str] = Field(None, max_length=200, description="Patient full name")
    contact_number: Optional[str] = Field(None, description="Contact phone number")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Auto-trigger prediction
    auto_predict: bool = Field(default=True, description="Automatically run prediction")
    auto_generate_interventions: bool = Field(default=True, description="Auto-generate care interventions")
    use_llm_personalization: bool = Field(default=False, description="Use LLM for personalized care plans")
    
    class Config:
        json_schema_extra = {
            "example": {
                "age": 75,
                "sex": 1,
                "bmi": 28.5,
                "insurance_type": "Medicare",
                "admission_type": "emergency",
                "discharge_destination": "home",
                "comorbidity_index": 8,
                "diabetes_flag": 1,
                "heart_failure_flag": 1,
                "copd_flag": 1,
                "ckd_flag": 1,
                "cancer_flag": 0,
                "dementia_flag": 0,
                "previous_admissions_12m": 3,
                "previous_er_visits_12m": 5,
                "prior_30_day_readmission_flag": 1,
                "length_of_stay_days": 7,
                "icu_stay_flag": 1,
                "medication_count_at_discharge": 12,
                "polypharmacy_flag": 1,
                "high_risk_medication_flag": 1,
                "hemoglobin": 10.5,
                "creatinine": 2.3,
                "glucose": 180,
                "hba1c": 8.5,
                "wbc_count": 9.2,
                "total_bilirubin": 1.1,
                "follow_up_within_7_days_flag": 1,
                "total_charges_index_stay": 45000,
                "drg_code": "291",
                "full_name": "John Smith",
                "auto_predict": True,
                "auto_generate_interventions": True,
                "use_llm_personalization": True
            }
        }


class PatientUpdate(BaseModel):
    """Update patient information (partial updates allowed)"""
    # All fields optional for updates
    age: Optional[int] = Field(None, ge=18, le=120)
    sex: Optional[Literal[0, 1]] = None
    bmi: Optional[float] = Field(None, ge=10, le=80)
    insurance_type: Optional[InsuranceType] = None
    admission_type: Optional[AdmissionType] = None
    discharge_destination: Optional[DischargeDestination] = None
    comorbidity_index: Optional[int] = Field(None, ge=0, le=37)
    diabetes_flag: Optional[Literal[0, 1]] = None
    heart_failure_flag: Optional[Literal[0, 1]] = None
    copd_flag: Optional[Literal[0, 1]] = None
    ckd_flag: Optional[Literal[0, 1]] = None
    cancer_flag: Optional[Literal[0, 1]] = None
    dementia_flag: Optional[Literal[0, 1]] = None
    previous_admissions_12m: Optional[int] = Field(None, ge=0, le=50)
    previous_er_visits_12m: Optional[int] = Field(None, ge=0, le=50)
    prior_30_day_readmission_flag: Optional[Literal[0, 1]] = None
    length_of_stay_days: Optional[int] = Field(None, ge=1, le=365)
    icu_stay_flag: Optional[Literal[0, 1]] = None
    medication_count_at_discharge: Optional[int] = Field(None, ge=0, le=50)
    polypharmacy_flag: Optional[Literal[0, 1]] = None
    high_risk_medication_flag: Optional[Literal[0, 1]] = None
    hemoglobin: Optional[float] = Field(None, ge=3.0, le=20.0)
    creatinine: Optional[float] = Field(None, ge=0.1, le=15.0)
    glucose: Optional[int] = Field(None, ge=30, le=600)
    hba1c: Optional[float] = Field(None, ge=3.0, le=20.0)
    wbc_count: Optional[float] = Field(None, ge=0.1, le=50.0)
    total_bilirubin: Optional[float] = Field(None, ge=0.1, le=30.0)
    follow_up_within_7_days_flag: Optional[Literal[0, 1]] = None
    total_charges_index_stay: Optional[float] = Field(None, ge=0)
    drg_code: Optional[str] = None
    full_name: Optional[str] = Field(None, max_length=200)
    contact_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    """Patient information response - COMPLETE with all fields"""
    patient_id: str
    age: int
    sex: int
    bmi: float
    insurance_type: str
    admission_type: str
    discharge_destination: str
    comorbidity_index: int
    full_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    
    # Prediction results (if available)
    has_prediction: bool = False
    readmission_probability: Optional[float] = None
    risk_level: Optional[str] = None
    
    # ALL Clinical fields (added to fix undefined display issue)
    diabetes_flag: int
    heart_failure_flag: int
    copd_flag: int
    ckd_flag: int
    cancer_flag: int
    dementia_flag: int
    previous_admissions_12m: int
    previous_er_visits_12m: int
    prior_30_day_readmission_flag: int
    length_of_stay_days: int
    icu_stay_flag: int
    medication_count_at_discharge: int
    polypharmacy_flag: int
    high_risk_medication_flag: int
    hemoglobin: float
    creatinine: float
    glucose: int
    hba1c: float
    wbc_count: float
    total_bilirubin: float
    follow_up_within_7_days_flag: int
    total_charges_index_stay: float
    drg_code: Optional[str]
    contact_number: Optional[str]
    emergency_contact: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class PatientWithPrediction(PatientResponse):
    """Patient with full prediction and intervention details"""
    prediction: Optional[dict] = None
    interventions: Optional[dict] = None
    
    class Config:
        from_attributes = True


class Patient(BaseModel):
    """Internal patient model (for storage)"""
    patient_id: str
    age: int
    sex: int
    bmi: float
    insurance_type: str
    admission_type: str
    discharge_destination: str
    comorbidity_index: int
    diabetes_flag: int
    heart_failure_flag: int
    copd_flag: int
    ckd_flag: int
    cancer_flag: int
    dementia_flag: int
    previous_admissions_12m: int
    previous_er_visits_12m: int
    prior_30_day_readmission_flag: int
    length_of_stay_days: int
    icu_stay_flag: int
    medication_count_at_discharge: int
    polypharmacy_flag: int
    high_risk_medication_flag: int
    hemoglobin: float
    creatinine: float
    glucose: int
    hba1c: float
    wbc_count: float
    total_bilirubin: float
    follow_up_within_7_days_flag: int
    total_charges_index_stay: float
    drg_code: Optional[str]
    full_name: Optional[str]
    contact_number: Optional[str]
    emergency_contact: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    
    # Prediction cache
    prediction_result: Optional[dict] = None
    intervention_result: Optional[dict] = None
