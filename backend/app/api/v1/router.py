"""
API v1 router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import predictions, interventions, auth, patients, care, ehr, agent

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    patients.router,
    prefix="/patients",
    tags=["Patient Management"]
)

api_router.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["Predictions"]
)

api_router.include_router(
    interventions.router,
    prefix="/interventions",
    tags=["Interventions"]
)

api_router.include_router(
    care.router,
    prefix="/care",
    tags=["Care Coordination"]
)

api_router.include_router(
    ehr.router,
    prefix="/ehr",
    tags=["EHR Interoperability (HL7 v2 & SMART on FHIR)"]
)

api_router.include_router(
    agent.router,
    prefix="/agent",
    tags=["Post-Care AI Agent (WhatsApp & Meta API)"]
)


