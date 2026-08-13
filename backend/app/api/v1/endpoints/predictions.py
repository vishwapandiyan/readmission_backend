"""
Prediction endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.models.schemas import (
    PatientFeatures,
    PredictionResponse,
    ComprehensivePrediction,
    ErrorResponse
)
from app.services.prediction_service import prediction_service

router = APIRouter()


@router.post(
    "/score",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict readmission risk",
    description="Make a comprehensive 5-layer prediction for a single patient"
)
async def predict_readmission(features: PatientFeatures):
   
    try:
        prediction = prediction_service.predict(features)
        
        return PredictionResponse(
            success=True,
            prediction=prediction,
            message="Prediction completed successfully"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post(
    "/batch",
    response_model=List[ComprehensivePrediction],
    status_code=status.HTTP_200_OK,
    summary="Batch predict readmission risk",
    description="Make predictions for multiple patients at once"
)
async def batch_predict_readmission(features_list: List[PatientFeatures]):
    """
    Predict readmission risk for multiple patients in a single request.
    
    Maximum batch size: 100 patients
    """
    if len(features_list) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 100 patients"
        )
    
    if len(features_list) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch cannot be empty"
        )
    
    try:
        predictions = prediction_service.batch_predict(features_list)
        return predictions
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )
