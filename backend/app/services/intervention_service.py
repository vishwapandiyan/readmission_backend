"""
Intervention Service - Care Recommendations Based on Risk
Combines rule-based interventions with optional LLM personalization
"""
from app.models.intervention_models import (
    RiskLevel, Priority, CareAction, MonitoringPlan,
    InterventionRequest, InterventionResponse, RiskFactors
)
from app.services.llm_service import llm_service
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class InterventionService:
    """Service for generating care interventions based on risk stratification"""
    
    @staticmethod
    def determine_risk_level(risk_probability: float) -> RiskLevel:
        """Stratify patient into risk category"""
        if risk_probability < 0.30:
            return RiskLevel.LOW
        elif risk_probability < 0.60:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    @staticmethod
    def get_low_risk_interventions() -> Tuple[List[CareAction], List[CareAction]]:
        """Standard interventions for low-risk patients"""
        immediate = []
        
        follow_up = [
            CareAction(
                action="routine_follow_up",
                priority=Priority.ROUTINE,
                timeline="7-14 days post-discharge",
                assigned_to="primary_care_provider",
                description="Schedule routine follow-up appointment with primary care physician"
            ),
            CareAction(
                action="patient_education",
                priority=Priority.ROUTINE,
                timeline="At discharge",
                assigned_to="discharge_nurse",
                description="Provide standard discharge instructions and medication list"
            ),
            CareAction(
                action="medication_review",
                priority=Priority.ROUTINE,
                timeline="At discharge",
                assigned_to="pharmacist",
                description="Standard medication reconciliation and patient education"
            )
        ]
        
        return immediate, follow_up
    
    @staticmethod
    def get_medium_risk_interventions() -> Tuple[List[CareAction], List[CareAction]]:
        """Standard interventions for medium-risk patients"""
        immediate = [
            CareAction(
                action="care_coordinator_notification",
                priority=Priority.MODERATE,
                timeline="Within 24 hours",
                assigned_to="care_coordinator",
                description="Notify care coordination team of moderate-risk patient requiring follow-up"
            )
        ]
        
        follow_up = [
            CareAction(
                action="follow_up_call",
                priority=Priority.MODERATE,
                timeline="48-72 hours post-discharge",
                assigned_to="nurse_navigator",
                description="Conduct wellness check call to assess symptoms and medication adherence"
            ),
            CareAction(
                action="early_follow_up",
                priority=Priority.MODERATE,
                timeline="3-7 days post-discharge",
                assigned_to="primary_care_provider",
                description="Schedule earlier-than-routine follow-up appointment"
            ),
            CareAction(
                action="medication_reconciliation",
                priority=Priority.MODERATE,
                timeline="Within 72 hours",
                assigned_to="pharmacist",
                description="Comprehensive medication review and adherence assessment"
            ),
            CareAction(
                action="home_health_assessment",
                priority=Priority.MODERATE,
                timeline="If applicable, within 5 days",
                assigned_to="home_health_agency",
                description="Assess need for home health services or durable medical equipment"
            )
        ]
        
        return immediate, follow_up
    
    @staticmethod
    def get_high_risk_interventions(risk_factors: RiskFactors) -> Tuple[List[CareAction], List[CareAction]]:
        """Comprehensive interventions for high-risk patients"""
        immediate = [
            CareAction(
                action="urgent_care_coordinator_notification",
                priority=Priority.URGENT,
                timeline="Immediate",
                assigned_to="care_coordinator_supervisor",
                description="PRIORITY: High-risk patient requiring immediate care coordination and monitoring"
            ),
            CareAction(
                action="comprehensive_medication_review",
                priority=Priority.HIGH,
                timeline="Within 24 hours",
                assigned_to="clinical_pharmacist",
                description="Detailed medication reconciliation, interaction check, and adherence planning"
            )
        ]
        
        follow_up = [
            CareAction(
                action="urgent_follow_up_appointment",
                priority=Priority.URGENT,
                timeline="24-48 hours post-discharge",
                assigned_to="primary_care_provider",
                description="Schedule urgent follow-up appointment - same or next day if possible"
            ),
            CareAction(
                action="follow_up_call",
                priority=Priority.URGENT,
                timeline="Within 24 hours",
                assigned_to="nurse_navigator",
                description="Immediate post-discharge call to verify medications, symptoms, and understanding"
            ),
            CareAction(
                action="home_health_coordination",
                priority=Priority.HIGH,
                timeline="Within 48 hours",
                assigned_to="home_health_coordinator",
                description="Arrange home health visits for vital signs, medication management, and assessment"
            ),
            CareAction(
                action="enhanced_monitoring_setup",
                priority=Priority.HIGH,
                timeline="Before discharge",
                assigned_to="case_manager",
                description="Set up enhanced monitoring plan with daily check-ins and clear escalation pathways"
            )
        ]
        
        # Add condition-specific interventions
        if "heart_failure" in risk_factors.conditions:
            follow_up.append(
                CareAction(
                    action="cardiology_referral",
                    priority=Priority.HIGH,
                    timeline="Within 7 days",
                    assigned_to="care_coordinator",
                    description="Schedule cardiology follow-up for heart failure management and optimization"
                )
            )
        
        if "diabetes" in risk_factors.conditions and risk_factors.comorbidity_index > 5:
            follow_up.append(
                CareAction(
                    action="diabetes_education",
                    priority=Priority.HIGH,
                    timeline="Within 5 days",
                    assigned_to="diabetes_educator",
                    description="Arrange diabetes self-management education and support"
                )
            )
        
        if risk_factors.icu_stay:
            follow_up.append(
                CareAction(
                    action="post_icu_assessment",
                    priority=Priority.HIGH,
                    timeline="Within 72 hours",
                    assigned_to="intensivist_or_hospitalist",
                    description="Post-ICU syndrome assessment and recovery planning"
                )
            )
        
        if risk_factors.discharge_destination in ["nursing_home", "rehab"]:
            immediate.append(
                CareAction(
                    action="facility_coordination",
                    priority=Priority.URGENT,
                    timeline="Before discharge",
                    assigned_to="social_worker",
                    description="Coordinate care transition to skilled nursing or rehab facility with full documentation"
                )
            )
        
        return immediate, follow_up
    
    @staticmethod
    def create_monitoring_plan(risk_level: RiskLevel, risk_factors: RiskFactors) -> MonitoringPlan:
        """Create monitoring plan based on risk level"""
        if risk_level == RiskLevel.LOW:
            return MonitoringPlan(
                frequency="As needed, patient-initiated contact",
                parameters=["general_wellness", "medication_questions"],
                escalation_criteria="Patient reports concerning symptoms or medication issues",
                duration_days=14
            )
        
        elif risk_level == RiskLevel.MEDIUM:
            return MonitoringPlan(
                frequency="Check-in call every 3-4 days for first 2 weeks",
                parameters=[
                    "medication_adherence",
                    "symptom_assessment",
                    "appointment_compliance",
                    "functional_status"
                ],
                escalation_criteria="Missed medications, new symptoms, missed appointments, or patient concern",
                duration_days=14
            )
        
        else:  # HIGH risk
            return MonitoringPlan(
                frequency="Daily check-ins for first 7 days, then every 2-3 days for next 2 weeks",
                parameters=[
                    "vital_signs",
                    "medication_adherence",
                    "symptom_tracking",
                    "diet_and_fluid_intake",
                    "functional_status",
                    "caregiver_support",
                    "emergency_department_visits"
                ],
                escalation_criteria="Any concerning vital signs, new/worsening symptoms, missed medications, lack of caregiver support, or ER visit",
                duration_days=21
            )
    
    @classmethod
    def generate_interventions(cls, request: InterventionRequest) -> InterventionResponse:
        """
        Main method to generate intervention recommendations
        Combines rule-based interventions with optional LLM personalization
        """
        logger.info(f"Generating interventions for patient {request.patient_id}, risk: {request.risk_probability:.2%}")
        
        # Determine risk level
        risk_level = cls.determine_risk_level(request.risk_probability)
        logger.info(f"Risk level: {risk_level.value}")
        
        # Get standard interventions based on risk level
        if risk_level == RiskLevel.LOW:
            immediate_actions, follow_up_actions = cls.get_low_risk_interventions()
        elif risk_level == RiskLevel.MEDIUM:
            immediate_actions, follow_up_actions = cls.get_medium_risk_interventions()
        else:  # HIGH
            immediate_actions, follow_up_actions = cls.get_high_risk_interventions(request.risk_factors)
        
        # Create monitoring plan
        monitoring_plan = cls.create_monitoring_plan(risk_level, request.risk_factors)
        
        # Initialize LLM-generated content as None
        personalized_care_plan = None
        patient_education = None
        care_coordinator_notes = None
        
        # Generate personalized content with LLM if requested and patient is medium/high risk
        if request.use_llm_personalization and risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
            logger.info("Generating personalized content with LLM...")
            try:
                personalized_care_plan = llm_service.generate_personalized_care_plan(
                    patient_id=request.patient_id,
                    risk_level=risk_level,
                    risk_probability=request.risk_probability,
                    risk_factors=request.risk_factors
                )
                
                patient_education = llm_service.generate_patient_education(
                    risk_factors=request.risk_factors,
                    risk_level=risk_level
                )
                
                care_coordinator_notes = llm_service.generate_care_coordinator_notes(
                    patient_id=request.patient_id,
                    risk_level=risk_level,
                    risk_probability=request.risk_probability,
                    risk_factors=request.risk_factors
                )
                
                logger.info("✓ LLM personalization complete")
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                # Continue without LLM content rather than failing
        
        # Build response
        response = InterventionResponse(
            patient_id=request.patient_id,
            risk_level=risk_level,
            risk_probability=request.risk_probability,
            immediate_actions=immediate_actions,
            follow_up_actions=follow_up_actions,
            monitoring_plan=monitoring_plan,
            personalized_care_plan=personalized_care_plan,
            patient_education=patient_education,
            care_coordinator_notes=care_coordinator_notes
        )
        
        logger.info(f"✓ Generated {len(immediate_actions)} immediate + {len(follow_up_actions)} follow-up actions")
        return response


# Singleton instance
intervention_service = InterventionService()
