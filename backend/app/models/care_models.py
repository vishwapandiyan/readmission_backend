"""
Care Coordinator and Status Tracking Models
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class CareStatus(str, Enum):
    """Care status options"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"


class CareCoordinator(BaseModel):
    """Care coordinator information"""
    id: str
    name: str
    role: str = "Care Coordinator"
    phone: Optional[str] = None
    email: Optional[str] = None


class CarePlan(BaseModel):
    """Patient care plan"""
    care_plan_id: str
    patient_id: str
    status: CareStatus = CareStatus.PENDING
    coordinator_id: Optional[str] = None
    coordinator_name: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    
    # Intervention tracking
    medication_reconciliation: bool = Field(default=False)
    follow_up_appointment: bool = Field(default=False)
    patient_education: bool = Field(default=False)
    follow_up_call: bool = Field(default=False)
    home_health_assessment: bool = Field(default=False)
    primary_care_coordination: bool = Field(default=False)
    specialist_referral: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Notes
    notes: Optional[str] = None


class CarePlanCreate(BaseModel):
    """Create care plan"""
    patient_id: str
    coordinator_id: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None


class CarePlanUpdate(BaseModel):
    """Update care plan"""
    status: Optional[CareStatus] = None
    coordinator_id: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    medication_reconciliation: Optional[bool] = None
    follow_up_appointment: Optional[bool] = None
    patient_education: Optional[bool] = None
    follow_up_call: Optional[bool] = None
    home_health_assessment: Optional[bool] = None
    primary_care_coordination: Optional[bool] = None
    specialist_referral: Optional[bool] = None
    notes: Optional[str] = None


class CarePlanResponse(BaseModel):
    """Care plan response"""
    care_plan_id: str
    patient_id: str
    status: CareStatus
    coordinator_id: Optional[str]
    coordinator_name: Optional[str]
    follow_up_date: Optional[datetime]
    progress_percentage: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Default coordinators pool
DEFAULT_COORDINATORS = [
    CareCoordinator(
        id="coord-001",
        name="Nurse P. Raman",
        phone="+1 (555) 0101",
        email="p.raman@hospital.org"
    ),
    CareCoordinator(
        id="coord-002",
        name="Nurse L. Cortez",
        phone="+1 (555) 0102",
        email="l.cortez@hospital.org"
    ),
    CareCoordinator(
        id="coord-003",
        name="Nurse D. Okafor",
        phone="+1 (555) 0103",
        email="d.okafor@hospital.org"
    ),
    CareCoordinator(
        id="coord-004",
        name="Nurse S. Blake",
        phone="+1 (555) 0104",
        email="s.blake@hospital.org"
    ),
]
