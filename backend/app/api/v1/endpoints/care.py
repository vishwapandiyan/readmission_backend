"""
Care Coordination API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.care_models import (
    CarePlanCreate,
    CarePlanUpdate,
    CarePlanResponse,
    CareStatus,
)
from app.services.care_service import care_service
from app.services.auth_service import auth_service
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current user ID from token"""
    try:
        token = credentials.credentials
        payload = auth_service.decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return payload.get("user_id")
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )


@router.post(
    "/", response_model=CarePlanResponse, status_code=status.HTTP_201_CREATED
)
async def create_care_plan(
    plan_data: CarePlanCreate, user_id: str = Depends(get_current_user_id)
):
    """
    Create a new care plan for a patient

    **Features:**
    - Auto-assigns care coordinator if not specified
    - Sets default follow-up date (7 days)
    - Tracks intervention checklist
    """
    try:
        logger.info(f"Creating care plan for patient {plan_data.patient_id}")

        care_plan = care_service.create_care_plan(plan_data)

        logger.info(f"✓ Care plan created: {care_plan.care_plan_id}")

        return care_service.care_plan_to_response(care_plan)

    except Exception as e:
        logger.error(f"Create care plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create care plan: {str(e)}",
        )


@router.get("/{care_plan_id}", response_model=CarePlanResponse)
async def get_care_plan(
    care_plan_id: str, user_id: str = Depends(get_current_user_id)
):
    """Get care plan by ID"""
    try:
        care_plan = care_service.get_care_plan(care_plan_id)

        if not care_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care plan {care_plan_id} not found",
            )

        return care_service.care_plan_to_response(care_plan)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get care plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve care plan",
        )


@router.get("/patient/{patient_id}", response_model=CarePlanResponse)
async def get_care_plan_by_patient(
    patient_id: str, user_id: str = Depends(get_current_user_id)
):
    """Get care plan for a specific patient"""
    try:
        care_plan = care_service.get_care_plan_by_patient(patient_id)

        if not care_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No care plan found for patient {patient_id}",
            )

        return care_service.care_plan_to_response(care_plan)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get care plan by patient error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve care plan",
        )


@router.get("/", response_model=List[CarePlanResponse])
async def list_care_plans(
    status: Optional[CareStatus] = Query(None, description="Filter by status"),
    coordinator_id: Optional[str] = Query(
        None, description="Filter by coordinator"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    user_id: str = Depends(get_current_user_id),
):
    """
    List all care plans with optional filters

    **Filters:**
    - status: Pending, In Progress, Completed, Overdue
    - coordinator_id: Specific care coordinator
    """
    try:
        plans = care_service.list_care_plans(
            status=status, coordinator_id=coordinator_id, skip=skip, limit=limit
        )
        return [care_service.care_plan_to_response(p) for p in plans]

    except Exception as e:
        logger.error(f"List care plans error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list care plans",
        )


@router.put("/{care_plan_id}", response_model=CarePlanResponse)
async def update_care_plan(
    care_plan_id: str,
    update_data: CarePlanUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Update care plan

    **Updates:**
    - Task completion status
    - Care coordinator assignment
    - Follow-up dates
    - Status changes
    """
    try:
        care_plan = care_service.update_care_plan(care_plan_id, update_data)

        if not care_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care plan {care_plan_id} not found",
            )

        logger.info(f"✓ Care plan updated: {care_plan_id} by user {user_id}")
        return care_service.care_plan_to_response(care_plan)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update care plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update care plan",
        )


@router.delete("/{care_plan_id}", status_code=status.HTTP_200_OK)
async def delete_care_plan(
    care_plan_id: str, user_id: str = Depends(get_current_user_id)
):
    """Delete care plan"""
    try:
        success = care_service.delete_care_plan(care_plan_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care plan {care_plan_id} not found",
            )

        logger.info(f"✓ Care plan deleted: {care_plan_id} by user {user_id}")
        return {
            "message": f"Care plan {care_plan_id} deleted successfully",
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete care plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete care plan",
        )


@router.get("/stats/summary", response_model=dict)
async def get_care_stats(user_id: str = Depends(get_current_user_id)):
    """
    Get care coordination statistics

    **Returns:**
    - Total care plans
    - Status distribution
    - Calls due today
    - Completion rate
    """
    try:
        stats = care_service.get_care_stats()
        return stats

    except Exception as e:
        logger.error(f"Get care stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get care statistics",
        )


@router.get("/coordinators/list", response_model=List[dict])
async def get_coordinators(user_id: str = Depends(get_current_user_id)):
    """Get list of available care coordinators"""
    try:
        coordinators = care_service.get_coordinators()
        return coordinators

    except Exception as e:
        logger.error(f"Get coordinators error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get coordinators",
        )
