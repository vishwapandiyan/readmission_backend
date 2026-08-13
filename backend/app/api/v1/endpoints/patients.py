"""
Patient Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.patient_models import (
    PatientCreate, PatientUpdate, PatientResponse, PatientWithPrediction
)
from app.services.patient_service import patient_service
from app.services.auth_service import auth_service
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user ID from token"""
    try:
        token = credentials.credentials
        payload = auth_service.decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return payload.get("user_id")
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )


@router.post("/", response_model=PatientWithPrediction, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new patient with complete details
    
    **Features:**
    - Creates patient record with all clinical data
    - Auto-triggers readmission prediction if `auto_predict=True`
    - Auto-generates care interventions if `auto_generate_interventions=True`
    - Optional LLM-powered personalized care plans
    
    **Returns:**
    - Patient information
    - Readmission prediction (probability, risk factors, timing)
    - Care interventions (immediate actions, follow-up, monitoring plan)
    - Personalized care plan (if LLM enabled)
    """
    try:
        logger.info(f"Create patient request from user {user_id}")
        
        # Create patient and run prediction/interventions
        result = await patient_service.create_patient_async(patient_data, created_by=user_id)
        
        logger.info(f"✓ Patient created: {result['patient'].patient_id}")
        
        # Return combined response
        return PatientWithPrediction(
            **result["patient"].model_dump(),
            prediction=result.get("prediction"),
            interventions=result.get("interventions")
        )
    
    except ValueError as e:
        logger.warning(f"Create patient failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create patient error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {str(e)}"
        )


@router.get("/{patient_id}", response_model=PatientWithPrediction)
async def get_patient(
    patient_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get patient by ID with prediction and intervention results
    
    **Returns:**
    - Complete patient information
    - Cached prediction results (if available)
    - Cached intervention recommendations (if available)
    """
    try:
        patient = await patient_service.get_patient_async(patient_id)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found"
            )
        
        return PatientWithPrediction(
            **patient_service.patient_to_response(patient).model_dump(),
            prediction=patient.prediction_result,
            interventions=patient.intervention_result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get patient error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient"
        )


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    user_id: str = Depends(get_current_user_id)
):
    """
    List all patients with pagination
    
    **Parameters:**
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return
    """
    try:
        patients = await patient_service.list_patients_async(skip=skip, limit=limit)
        return [patient_service.patient_to_response(p) for p in patients]
    
    except Exception as e:
        logger.error(f"List patients error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list patients"
        )


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    update_data: PatientUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update patient information
    
    **Note:** Partial updates supported - only provide fields to update
    """
    try:
        patient = await patient_service.update_patient_async(patient_id, update_data)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found"
            )
        
        logger.info(f"✓ Patient updated: {patient_id} by user {user_id}")
        return patient_service.patient_to_response(patient)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update patient error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update patient"
        )


@router.delete("/{patient_id}", status_code=status.HTTP_200_OK)
async def delete_patient(
    patient_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete patient record
    
    **Warning:** This action cannot be undone
    """
    try:
        success = await patient_service.delete_patient_async(patient_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found"
            )
        
        logger.info(f"✓ Patient deleted: {patient_id} by user {user_id}")
        return {
            "message": f"Patient {patient_id} deleted successfully",
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete patient error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete patient"
        )


@router.post("/{patient_id}/predict", response_model=dict)
async def predict_patient_readmission(
    patient_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Manually trigger readmission prediction for existing patient
    
    **Use when:**
    - Patient was created without auto-prediction
    - Need to re-run prediction after updates
    """
    try:
        prediction = await patient_service.predict_readmission_async(patient_id)
        
        logger.info(f"✓ Prediction run for patient {patient_id}: {prediction['readmission_probability']:.1%}")
        return prediction
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Predict patient error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run prediction"
        )


@router.post("/{patient_id}/interventions", response_model=dict)
async def generate_patient_interventions(
    patient_id: str,
    use_llm: bool = Query(False, description="Use LLM for personalized care plans"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Manually generate care interventions for existing patient
    
    **Parameters:**
    - use_llm: Enable AI-powered personalized care plans
    
    **Use when:**
    - Patient was created without auto-interventions
    - Need to re-generate after clinical updates
    - Want to add LLM personalization later
    """
    try:
        interventions = await patient_service.generate_interventions_async(patient_id, use_llm=use_llm)
        
        logger.info(f"✓ Interventions generated for patient {patient_id}")
        return interventions
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Generate interventions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interventions"
        )


@router.get("/stats/summary", response_model=dict)
async def get_patient_stats(user_id: str = Depends(get_current_user_id)):
    """
    Get patient statistics summary
    
    **Returns:**
    - Total patients
    - Patients with predictions
    - Risk level distribution
    - Average readmission probability
    """
    try:
        patients = await patient_service.list_patients_async(skip=0, limit=10000)
        
        total = len(patients)
        with_predictions = sum(1 for p in patients if p.prediction_result)
        
        # Risk levels
        high_risk = sum(1 for p in patients if p.intervention_result and p.intervention_result.get("risk_level") == "HIGH")
        medium_risk = sum(1 for p in patients if p.intervention_result and p.intervention_result.get("risk_level") == "MEDIUM")
        low_risk = sum(1 for p in patients if p.intervention_result and p.intervention_result.get("risk_level") == "LOW")
        
        # Average probability
        probabilities = [p.prediction_result["readmission_probability"] for p in patients if p.prediction_result]
        avg_probability = sum(probabilities) / len(probabilities) if probabilities else 0
        
        return {
            "total_patients": total,
            "patients_with_predictions": with_predictions,
            "risk_distribution": {
                "high": high_risk,
                "medium": medium_risk,
                "low": low_risk
            },
            "average_readmission_probability": round(avg_probability, 4)
        }
    
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )
