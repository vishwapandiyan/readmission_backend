"""
EHR Integration Models for HL7 v2 ADT and SMART on FHIR
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from app.models.schemas import PatientFeatures, ComprehensivePrediction


# ============================================================================
# HL7 v2 ADT Models
# ============================================================================

class HL7MessageType(str, Enum):
    """Supported HL7 v2 ADT Message Types"""
    ADT_A01 = "ADT^A01"  # Patient Admission
    ADT_A02 = "ADT^A02"  # Patient Transfer
    ADT_A03 = "ADT^A03"  # Patient Discharge
    ADT_A08 = "ADT^A08"  # Patient Information Update


class HL7ADTMessageRequest(BaseModel):
    """Raw HL7 v2 ADT Message Request"""
    raw_message: str = Field(
        ...,
        description="Raw HL7 v2 pipe-delimited message string containing MSH, PID, PV1, DG1, OBX segments"
    )
    auto_predict: bool = Field(
        default=True,
        description="Automatically execute 30-day readmission prediction upon parsing"
    )
    save_to_database: bool = Field(
        default=False,
        description="Save parsed patient record into database"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "raw_message": (
                    "MSH|^~\\&|EPIC_EHR|HOSPITAL_A|READMISSION_AI|HOSPITAL_SYS|20260813120000||ADT^A03|MSG0001|P|2.5\r"
                    "PID|1||P89421^^^MRN||DOE^JOHN^||19580415|M|||123 MAIN ST^^BOSTON^MA^02115||(555)123-4567\r"
                    "PV1|1|I|MED^301^1||||1234^SMITH^SARAH|||||||||||EMERGENCY|V1001|||||||||||||||||||||||||20260806080000|20260813120000\r"
                    "DG1|1|I10|E11.9^Type 2 diabetes mellitus^I10\r"
                    "DG1|2|I10|I50.9^Heart failure unspecified^I10\r"
                    "DG1|3|I10|J44.9^COPD unspecified^I10\r"
                    "OBX|1|NM|718-7^Hemoglobin^LN||11.2|g/dL|12.0-17.5|L|||F\r"
                    "OBX|2|NM|2160-0^Creatinine^LN||1.8|mg/dL|0.6-1.3|H|||F\r"
                    "OBX|3|NM|2345-7^Glucose^LN||165|mg/dL|70-99|H|||F\r"
                    "OBX|4|NM|4548-4^Hemoglobin A1c^LN||8.2|%|4.0-5.6|H|||F\r"
                    "OBX|5|NM|6690-2^WBC^LN||9.4|10*3/uL|4.0-11.0|N|||F\r"
                    "OBX|6|NM|1975-2^Total Bilirubin^LN||0.9|mg/dL|0.2-1.2|N|||F\r"
                    "OBX|7|NM|39156-5^BMI^LN||29.4|kg/m2|18.5-24.9|H|||F\r"
                ),
                "auto_predict": True,
                "save_to_database": False
            }
        }


class HL7ParsedData(BaseModel):
    """Extracted data from HL7 v2 message"""
    message_type: str
    message_control_id: str
    sending_application: str
    sending_facility: str
    patient_id: str
    full_name: Optional[str] = None
    age: int
    sex: int
    admission_type: str
    discharge_destination: str
    length_of_stay_days: int
    diagnoses: List[str] = []
    labs: Dict[str, float] = {}
    medication_count: int = 5
    polypharmacy: bool = False
    high_risk_medications: bool = False
    icu_stay: bool = False


class HL7ADTResponse(BaseModel):
    """Response returned from HL7 ADT ingestion"""
    success: bool
    message: str
    ack_message: str = Field(..., description="HL7 v2 ACK acknowledgement message for EHR MLLP/TCP bridge")
    parsed_patient: HL7ParsedData
    mapped_features: PatientFeatures
    prediction: Optional[ComprehensivePrediction] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# SMART on FHIR Models
# ============================================================================

class SmartConfigurationResponse(BaseModel):
    """SMART on FHIR Discovery Configuration (.well-known/smart-configuration)"""
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    token_endpoint_auth_methods_supported: List[str] = ["client_secret_basic", "client_secret_post", "none"]
    grant_types_supported: List[str] = ["authorization_code", "client_credentials"]
    registration_endpoint: Optional[str] = None
    scopes_supported: List[str] = [
        "openid",
        "profile",
        "launch",
        "launch/patient",
        "patient/*.read",
        "patient/Patient.read",
        "patient/Encounter.read",
        "patient/Condition.read",
        "patient/Observation.read",
        "patient/MedicationRequest.read",
        "patient/RiskAssessment.write"
    ]
    response_types_supported: List[str] = ["code"]
    capabilities: List[str] = [
        "launch-ehr",
        "launch-standalone",
        "client-confidential-symmetric",
        "client-public",
        "context-ehr-patient",
        "context-standalone-patient",
        "permission-patient",
        "permission-user"
    ]
    code_challenge_methods_supported: List[str] = ["S256"]


class FHIRSyncPatientRequest(BaseModel):
    """Request to fetch and predict on a patient from an external FHIR server"""
    fhir_server_url: str = Field(
        default="https://launch.smarthealthit.org/v/r4/fhir",
        description="Base URL of target FHIR R4 server"
    )
    patient_id: str = Field(
        ...,
        description="Target Patient resource ID in the FHIR server"
    )
    access_token: Optional[str] = Field(
        None,
        description="OAuth2 Bearer token if FHIR server requires authentication"
    )
    auto_save: bool = Field(
        default=False,
        description="Save patient record to database"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "fhir_server_url": "https://launch.smarthealthit.org/v/r4/fhir",
                "patient_id": "smart-1032702",
                "access_token": None,
                "auto_save": False
            }
        }


class FHIRBundleRequest(BaseModel):
    """Direct FHIR R4 Bundle Ingestion"""
    resourceType: str = "Bundle"
    entry: List[Dict[str, Any]] = Field(..., description="FHIR Resources (Patient, Encounter, Condition, Observation, MedicationRequest)")
    auto_save: bool = Field(default=False)


class FHIRSyncResponse(BaseModel):
    """Response containing extracted FHIR features and generated FHIR RiskAssessment"""
    success: bool
    patient_id: str
    extracted_features: PatientFeatures
    prediction: ComprehensivePrediction
    fhir_risk_assessment: Dict[str, Any] = Field(
        ...,
        description="Standard FHIR R4 RiskAssessment resource suitable to POST back to EHR FHIR server"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# CDS Hooks Models (Epic / Cerner EHR Clinical Decision Support)
# ============================================================================

class CDSHookRequest(BaseModel):
    """CDS Hook Request (patient-discharge or encounter-discharge)"""
    hook: str = Field(..., description="Hook identifier (e.g. 'patient-discharge')")
    hookInstance: str = Field(..., description="Unique UUID for this invocation")
    fhirServer: Optional[str] = None
    fhirAuthorization: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = Field(
        ...,
        description="Context variables (patientId, encounterId, userId)"
    )
    prefetch: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Prefetched FHIR resources (patient, encounter, conditions, etc.)"
    )


class CDSSource(BaseModel):
    label: str
    url: Optional[str] = None
    icon: Optional[str] = None


class CDSLink(BaseModel):
    label: str
    url: str
    type: str = "smart"  # 'smart' or 'absolute'
    appContext: Optional[str] = None


class CDSSuggestion(BaseModel):
    label: str
    uuid: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None


class CDSCard(BaseModel):
    """CDS Hooks decision card returned to EHR screen"""
    uuid: Optional[str] = None
    summary: str
    detail: Optional[str] = None
    indicator: str = Field(..., description="'info', 'warning', or 'critical'")
    source: CDSSource
    suggestions: Optional[List[CDSSuggestion]] = None
    selectionBehavior: Optional[str] = "at-most-one"
    links: Optional[List[CDSLink]] = None


class CDSHookResponse(BaseModel):
    """CDS Hooks Response containing decision cards"""
    cards: List[CDSCard]
