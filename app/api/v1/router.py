"""
API v1 router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import predictions

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["Predictions"]
)
