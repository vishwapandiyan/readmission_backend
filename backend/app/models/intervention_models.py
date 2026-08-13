"""
Intervention Models and Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class RiskLevel(str, Enum):
    """Risk stratification levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Priority(str, Enum):
    """Action priority levels"""
    ROUTINE = "ROUTINE"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    URGENT = "URGENT"


class CareAction(BaseModel):
    """Individual care action/intervention"""
    action: str = Field(..., description="Type of action")
    priority: Priority = Field(..., description="Priority level")
    timeline: str = Field(..., description="When action should occur")
    assigned_to: str = Field(..., description="Role responsible for action")
    description: str = Field(..., description="Detailed action description")
    completed: bool = Field(default=False, description="Whether action is completed")


class MonitoringPlan(BaseModel):
    """Patient monitoring plan"""
    frequency: str = Field(..., description="How often to monitor")
    parameters: List[str] = Field(..., description="What to monitor")
    escalation_criteria: str = Field(..., description="When to escalate care")
    duration_days: int = Field(..., description="How many days to monitor")


class RiskFactors(BaseModel):
    """Patient risk factors"""
    comorbidity_index: int
    previous_admissions_12m: int
    conditions: List[str]
    medications_count: int
    age: int
    icu_stay: bool = False
    discharge_destination: Optional[str] = None


class InterventionRequest(BaseModel):
    """Request for intervention recommendations"""
    patient_id: str = Field(..., description="Patient identifier")
    risk_probability: float = Field(..., ge=0, le=1, description="Risk score from ML model")
    risk_factors: RiskFactors = Field(..., description="Patient risk factors")
    use_llm_personalization: bool = Field(default=False, description="Generate personalized plan with LLM")


class InterventionResponse(BaseModel):
    """Intervention recommendations response"""
    patient_id: str
    risk_level: RiskLevel
    risk_probability: float
    immediate_actions: List[CareAction]
    follow_up_actions: List[CareAction]
    monitoring_plan: MonitoringPlan
    personalized_care_plan: Optional[str] = None
    patient_education: Optional[str] = None
    care_coordinator_notes: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AlertRequest(BaseModel):
    """Request to create care team alert"""
    patient_id: str
    risk_level: RiskLevel
    message: str
    priority: Priority
    assigned_to: str


class AlertResponse(BaseModel):
    """Alert creation response"""
    alert_id: str
    patient_id: str
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
