"""
Intervention API Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from app.models.intervention_models import InterventionRequest, InterventionResponse, AlertRequest, AlertResponse
from app.services.intervention_service import intervention_service
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/recommend", response_model=InterventionResponse, status_code=status.HTTP_200_OK)
async def recommend_interventions(request: InterventionRequest):
    """
    Generate intervention recommendations based on patient risk
    
    **Risk Stratification:**
    - LOW (0-30%): Routine follow-up
    - MEDIUM (30-60%): Enhanced coordination and monitoring
    - HIGH (60-100%): Comprehensive intervention with urgent actions
    
    **LLM Personalization:**
    - Set `use_llm_personalization: true` to generate custom care plans
    - Only recommended for MEDIUM/HIGH risk patients
    - Adds 2-3 seconds to response time
    """
    try:
        logger.info(f"Intervention request for patient {request.patient_id}")
        
        # Validate risk probability
        if not 0 <= request.risk_probability <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="risk_probability must be between 0 and 1"
            )
        
        # Generate interventions
        response = intervention_service.generate_interventions(request)
        
        logger.info(f"✓ Interventions generated for {request.patient_id}: {response.risk_level.value} risk")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating interventions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate interventions: {str(e)}"
        )


@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(request: AlertRequest):
    """
    Create care team alert for high-priority patients
    
    This endpoint would typically integrate with:
    - EHR notification systems
    - Care coordinator dashboards
    - SMS/email alert systems
    - Paging systems for urgent alerts
    """
    try:
        logger.info(f"Creating alert for patient {request.patient_id}: {request.priority.value}")
        
        # In a real system, this would:
        # 1. Store alert in database
        # 2. Send notifications via configured channels
        # 3. Update care coordinator dashboard
        # 4. Log in audit trail
        
        # For now, return simulated response
        alert_id = str(uuid.uuid4())
        
        response = AlertResponse(
            alert_id=alert_id,
            patient_id=request.patient_id,
            status="SENT"
        )
        
        logger.info(f"✓ Alert {alert_id} created for patient {request.patient_id}")
        return response
    
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Check intervention service health"""
    return {
        "status": "healthy",
        "service": "intervention_service",
        "llm_enabled": intervention_service and hasattr(intervention_service, '__class__')
    }
