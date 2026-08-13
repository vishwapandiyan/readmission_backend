"""
EHR Interoperability Endpoints: HL7 v2 ADT and SMART on FHIR
"""
from fastapi import APIRouter, HTTPException, status, Request, Query, Body
from typing import Dict, Any, Optional, List
import logging
import uuid

from app.models.ehr_models import (
    HL7ADTMessageRequest,
    HL7ADTResponse,
    SmartConfigurationResponse,
    FHIRSyncPatientRequest,
    FHIRBundleRequest,
    FHIRSyncResponse,
    CDSHookRequest,
    CDSHookResponse
)
from app.services.hl7_service import hl7_service
from app.services.fhir_service import fhir_service
from app.services.prediction_service import prediction_service
from app.services.patient_service import patient_service
from app.models.patient_models import PatientCreate

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# HL7 v2 ADT Endpoints
# ============================================================================

@router.post(
    "/hl7/adt",
    response_model=HL7ADTResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest HL7 v2 ADT Message",
    description="Parse standard HL7 v2 ADT message (ADT^A01, ADT^A03, ADT^A08), map to clinical features, run ML prediction, and return HL7 ACK."
)
async def process_hl7_adt_message(request: HL7ADTMessageRequest):
    """
    Process incoming HL7 v2 ADT Message:
    - Parses MSH, PID, PV1, DG1, OBX segments
    - Maps extracted clinical attributes to the 29 readmission prediction features
    - Executes 5-layer ML Readmission Risk Prediction
    - Generates HL7 ACK acknowledgment string for MLLP listener / EHR bridge
    """
    try:
        if not request.raw_message or not request.raw_message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty HL7 message provided"
            )

        logger.info("Processing incoming HL7 v2 ADT message...")

        # Parse message
        parsed_data, mapped_features, ack_message = hl7_service.parse_message(request.raw_message)

        # Run prediction if requested
        prediction = None
        if request.auto_predict:
            prediction = prediction_service.predict(mapped_features)

        # Save to database if requested
        if request.save_to_database:
            try:
                patient_create_data = PatientCreate(
                    full_name=parsed_data.full_name or f"Patient {parsed_data.patient_id}",
                    age=mapped_features.age,
                    sex=mapped_features.sex,
                    bmi=mapped_features.bmi,
                    insurance_type=mapped_features.insurance_type,
                    comorbidity_index=mapped_features.comorbidity_index,
                    diabetes_flag=mapped_features.diabetes_flag,
                    heart_failure_flag=mapped_features.heart_failure_flag,
                    copd_flag=mapped_features.copd_flag,
                    ckd_flag=mapped_features.ckd_flag,
                    cancer_flag=mapped_features.cancer_flag,
                    dementia_flag=mapped_features.dementia_flag,
                    previous_admissions_12m=mapped_features.previous_admissions_12m,
                    previous_er_visits_12m=mapped_features.previous_er_visits_12m,
                    prior_30_day_readmission_flag=mapped_features.prior_30_day_readmission_flag,
                    admission_type=mapped_features.admission_type,
                    length_of_stay_days=mapped_features.length_of_stay_days,
                    icu_stay_flag=mapped_features.icu_stay_flag,
                    discharge_destination=mapped_features.discharge_destination,
                    medication_count_at_discharge=mapped_features.medication_count_at_discharge,
                    polypharmacy_flag=mapped_features.polypharmacy_flag,
                    high_risk_medication_flag=mapped_features.high_risk_medication_flag,
                    hemoglobin=mapped_features.hemoglobin,
                    creatinine=mapped_features.creatinine,
                    glucose=mapped_features.glucose,
                    hba1c=mapped_features.hba1c,
                    wbc_count=mapped_features.wbc_count,
                    total_bilirubin=mapped_features.total_bilirubin,
                    follow_up_within_7_days_flag=mapped_features.follow_up_within_7_days_flag,
                    total_charges_index_stay=mapped_features.total_charges_index_stay,
                    drg_code=mapped_features.drg_code,
                    auto_predict=False
                )
                await patient_service.create_patient_async(patient_create_data, created_by="HL7_INGESTION")
            except Exception as db_err:
                logger.warning(f"Could not save HL7 patient to DB: {db_err}")

        logger.info(f"✓ Processed HL7 message for patient {parsed_data.patient_id} ({parsed_data.message_type})")

        return HL7ADTResponse(
            success=True,
            message=f"HL7 message {parsed_data.message_control_id} processed successfully",
            ack_message=ack_message,
            parsed_patient=parsed_data,
            mapped_features=mapped_features,
            prediction=prediction
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HL7 processing failed: {e}")
        # Generate Error ACK
        err_ack = hl7_service.generate_ack(
            message_control_id="UNKNOWN",
            receiving_app="UNKNOWN",
            receiving_facility="UNKNOWN",
            ack_code="AE",
            ack_text=f"HL7 processing error: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "ack_message": err_ack
            }
        )


@router.get(
    "/hl7/sample-adt",
    response_model=Dict[str, str],
    summary="Get Sample HL7 v2 Messages",
    description="Retrieve ready-to-test sample HL7 v2 ADT^A01 (Admit) and ADT^A03 (Discharge) messages"
)
async def get_sample_hl7_messages():
    """Returns sample HL7 v2 ADT messages for quick demonstration and testing"""
    return hl7_service.get_sample_adt_messages()


# ============================================================================
# SMART on FHIR Discovery & Capabilities
# ============================================================================

@router.get(
    "/fhir/.well-known/smart-configuration",
    response_model=SmartConfigurationResponse,
    summary="SMART on FHIR Discovery Endpoint",
    description="Returns SMART on FHIR OAuth discovery metadata per the SMART App Launch IG specification"
)
async def get_smart_configuration(request: Request):
    """SMART on FHIR configuration discovery metadata"""
    base_url = str(request.base_url).rstrip("/")
    return fhir_service.get_smart_configuration(base_url)


@router.get(
    "/fhir/metadata",
    response_model=Dict[str, Any],
    summary="FHIR CapabilityStatement",
    description="Returns FHIR R4 CapabilityStatement describing supported resources and SMART security endpoints"
)
async def get_fhir_metadata(request: Request):
    """FHIR R4 CapabilityStatement"""
    base_url = str(request.base_url).rstrip("/")
    return fhir_service.get_capability_statement(base_url)


# ============================================================================
# FHIR Synchronization & Bundle Ingestion
# ============================================================================

@router.post(
    "/fhir/sync-patient",
    response_model=FHIRSyncResponse,
    summary="Fetch Patient from External FHIR Server and Predict",
    description="Connects to any external FHIR R4 server (SMART sandbox, Epic, Cerner), fetches patient clinical bundle, and evaluates readmission risk"
)
async def sync_patient_from_fhir_server(request: FHIRSyncPatientRequest):
    """
    Connect to external FHIR server (e.g. SMART sandbox / Epic / Cerner):
    - Fetches Patient, Encounter, Condition, Observation, and MedicationRequest resources
    - Maps FHIR codings (LOINC, SNOMED, ICD-10) to 29 model features
    - Runs 5-layer ML Readmission Risk model
    - Generates a compliant FHIR R4 RiskAssessment resource
    """
    try:
        logger.info(f"Syncing patient {request.patient_id} from FHIR server {request.fhir_server_url}...")

        # 1. Fetch resources
        bundle = await fhir_service.fetch_patient_bundle_from_fhir_server(
            fhir_server_url=request.fhir_server_url,
            patient_id=request.patient_id,
            access_token=request.access_token
        )

        # 2. Extract features
        patient_id, full_name, features = fhir_service.fhir_bundle_to_patient_features(
            bundle=bundle,
            fallback_patient_id=request.patient_id
        )

        # 3. Predict readmission
        prediction = prediction_service.predict(features)

        # 4. Build FHIR RiskAssessment
        risk_assessment = fhir_service.create_fhir_risk_assessment(
            patient_id=patient_id,
            prediction=prediction
        )

        logger.info(f"✓ Completed FHIR sync for {patient_id}: Readmission risk = {prediction.layer1_prediction.probability:.1%}")

        return FHIRSyncResponse(
            success=True,
            patient_id=patient_id,
            extracted_features=features,
            prediction=prediction,
            fhir_risk_assessment=risk_assessment
        )

    except Exception as e:
        logger.error(f"FHIR sync error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync patient from FHIR server: {str(e)}"
        )


@router.post(
    "/fhir/bundle",
    response_model=FHIRSyncResponse,
    summary="Ingest Raw FHIR R4 Bundle",
    description="Directly evaluate a FHIR R4 Bundle containing Patient, Encounters, Conditions, and Observations"
)
async def ingest_fhir_bundle(request: FHIRBundleRequest):
    """Direct FHIR R4 Bundle evaluation"""
    try:
        bundle_dict = request.model_dump()
        patient_id, full_name, features = fhir_service.fhir_bundle_to_patient_features(bundle_dict)

        prediction = prediction_service.predict(features)
        risk_assessment = fhir_service.create_fhir_risk_assessment(patient_id=patient_id, prediction=prediction)

        return FHIRSyncResponse(
            success=True,
            patient_id=patient_id,
            extracted_features=features,
            prediction=prediction,
            fhir_risk_assessment=risk_assessment
        )
    except Exception as e:
        logger.error(f"FHIR bundle ingestion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate FHIR Bundle: {str(e)}"
        )


@router.get(
    "/fhir/sample-bundle",
    response_model=Dict[str, Any],
    summary="Get Sample FHIR R4 Bundle",
    description="Retrieve a synthetic FHIR R4 Bundle for rapid testing"
)
async def get_sample_fhir_bundle():
    """Returns sample FHIR R4 Bundle"""
    return fhir_service.get_sample_fhir_bundle()


# ============================================================================
# CDS Hooks (Epic & Cerner Real-time Decision Support)
# ============================================================================

@router.get(
    "/cds-services",
    response_model=Dict[str, Any],
    summary="CDS Services Discovery Endpoint",
    description="Returns CDS Services list per the CDS Hooks specification"
)
async def get_cds_services(request: Request):
    """CDS Hooks discovery"""
    base_url = str(request.base_url).rstrip("/")
    return {
        "services": [
            {
                "hook": "patient-discharge",
                "name": "30-Day Hospital Readmission Risk Evaluator",
                "description": "Evaluates patient 30-day readmission risk upon hospital discharge and provides targeted clinical interventions.",
                "id": "patient-discharge-readmission-risk",
                "prefetch": {
                    "patient": "Patient/{{context.patientId}}",
                    "encounter": "Encounter/{{context.encounterId}}",
                    "conditions": "Condition?patient={{context.patientId}}",
                    "observations": "Observation?patient={{context.patientId}}&_count=20",
                    "medications": "MedicationRequest?patient={{context.patientId}}&status=active"
                }
            }
        ]
    }


@router.post(
    "/cds-services/patient-discharge",
    response_model=CDSHookResponse,
    summary="CDS Hook: Patient Discharge",
    description="Receives discharge context from EHR, calculates readmission probability, and returns CDS alert cards"
)
async def handle_cds_patient_discharge(
    request: CDSHookRequest,
    req: Request
):
    """CDS Hooks patient-discharge handler"""
    try:
        base_url = str(req.base_url).rstrip("/")
        response = fhir_service.handle_cds_hook(request, base_url=base_url)
        return response
    except Exception as e:
        logger.error(f"CDS Hook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CDS Hook execution failed: {str(e)}"
        )


# ============================================================================
# SMART on FHIR OAuth / App Launch Handlers (Simulation & Verification)
# ============================================================================

@router.get(
    "/smart/launch",
    summary="SMART on FHIR Launch Handler",
    description="Handles SMART on FHIR EHR app launch flow with launch context and patient ID"
)
async def handle_smart_launch(
    iss: str = Query("https://launch.smarthealthit.org/v/r4/fhir", description="FHIR Server Base URL"),
    launch: Optional[str] = Query(None, description="SMART Launch context token"),
    patient: Optional[str] = Query(None, description="Preselected patient ID")
):
    """SMART App Launch endpoint for EHR embedded iFrame"""
    return {
        "status": "ready",
        "message": "SMART on FHIR launch initiated",
        "fhir_server": iss,
        "launch_token": launch or str(uuid.uuid4()),
        "selected_patient": patient or "smart-1032702",
        "app_url": f"https://d578gwwut8r88.cloudfront.net/?iss={iss}&patient={patient or 'smart-1032702'}"
    }


@router.get(
    "/smart/authorize",
    summary="SMART OAuth Authorize Simulation",
    description="Returns simulated authorization code for SMART on FHIR standalone testing"
)
async def smart_authorize(
    response_type: str = Query("code"),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query("patient/*.read launch/patient"),
    state: str = Query(...),
    aud: Optional[str] = Query(None)
):
    """SMART Authorize simulation"""
    code = f"smart-auth-code-{uuid.uuid4().hex[:12]}"
    return {
        "redirect_to": f"{redirect_uri}?code={code}&state={state}",
        "authorization_code": code,
        "state": state
    }


@router.post(
    "/smart/token",
    summary="SMART OAuth Token Exchange",
    description="Exchanges authorization code for an access token and patient context"
)
async def smart_token(
    grant_type: str = Body("authorization_code"),
    code: Optional[str] = Body(None),
    client_id: Optional[str] = Body(None)
):
    """SMART Token exchange endpoint"""
    return {
        "access_token": f"smart-token-{uuid.uuid4().hex}",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "patient/*.read launch/patient openid profile",
        "patient": "smart-1032702",
        "encounter": "enc-90214",
        "need_patient_banner": True,
        "smart_style_url": "https://launch.smarthealthit.org/smart-style.json"
    }
