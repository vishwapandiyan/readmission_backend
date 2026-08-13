"""
LLM Service for Personalized Care Plan Generation
Uses Groq API with Llama 3.1
"""
from groq import Groq
from app.core.config import settings
from app.models.intervention_models import RiskFactors, RiskLevel
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating personalized care content using Groq/Llama"""
    
    def __init__(self):
        if settings.LLM_ENABLED:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY)
                self.model = settings.GROQ_MODEL
                self.enabled = True
                logger.info(f"✓ LLM Service initialized with Groq ({self.model})")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.enabled = False
        else:
            self.enabled = False
            logger.info("LLM Service disabled in config")
    
    def _call_llm(self, prompt: str) -> str:
        """Call Groq API with streaming"""
        if not self.enabled:
            return None
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a clinical care coordinator assistant helping create personalized discharge and follow-up plans for hospital patients at risk of readmission. Provide clear, actionable, and compassionate guidance."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                top_p=1,
                stream=False,  # Non-streaming for easier handling
                stop=None
            )
            
            return completion.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return None
    
    def generate_personalized_care_plan(
        self, 
        patient_id: str,
        risk_level: RiskLevel, 
        risk_probability: float,
        risk_factors: RiskFactors
    ) -> str:
        """Generate personalized care plan based on patient data"""
        
        if not self.enabled:
            return None
        
        # Build condition list
        conditions_str = ", ".join(risk_factors.conditions) if risk_factors.conditions else "none reported"
        
        # Create prompt
        prompt = f"""
Create a personalized post-discharge care plan for a {risk_level.value} risk patient.

**Patient Profile:**
- Patient ID: {patient_id}
- Readmission Risk: {risk_probability:.1%}
- Age: {risk_factors.age} years
- Comorbidity Index: {risk_factors.comorbidity_index}
- Medical Conditions: {conditions_str}
- Previous Hospital Admissions (12 months): {risk_factors.previous_admissions_12m}
- Current Medications: {risk_factors.medications_count}
- Recent ICU Stay: {'Yes' if risk_factors.icu_stay else 'No'}
{f'- Discharge Destination: {risk_factors.discharge_destination}' if risk_factors.discharge_destination else ''}

**Instructions:**
Create a comprehensive but concise care plan (300-400 words) that includes:
1. **Immediate Priorities**: What needs attention in first 24-48 hours
2. **Medication Management**: Key reminders for their specific conditions
3. **Warning Signs**: What symptoms require immediate medical attention
4. **Follow-up Schedule**: When and why they need appointments
5. **Lifestyle Recommendations**: Specific to their conditions

Make it compassionate, clear, and actionable. Use simple language a patient can understand.
"""
        
        response = self._call_llm(prompt)
        return response
    
    def generate_patient_education(
        self,
        risk_factors: RiskFactors,
        risk_level: RiskLevel
    ) -> str:
        """Generate patient-friendly education materials"""
        
        if not self.enabled:
            return None
        
        conditions_str = ", ".join(risk_factors.conditions) if risk_factors.conditions else "general health"
        
        prompt = f"""
Create patient-friendly discharge education for someone with {conditions_str}.

**Patient Context:**
- Risk Level: {risk_level.value}
- Medical Conditions: {conditions_str}
- Number of Medications: {risk_factors.medications_count}
- Age: {risk_factors.age} years

**Instructions:**
Write a clear, empathetic education guide (250-300 words) covering:
1. **Understanding Your Conditions**: Simple explanations
2. **Taking Your Medications**: Why each type matters
3. **Daily Self-Care**: What to do at home
4. **When to Call for Help**: Red flags explained simply
5. **Support Resources**: Who can help

Use 6th-8th grade reading level. Be encouraging and supportive.
"""
        
        response = self._call_llm(prompt)
        return response
    
    def generate_care_coordinator_notes(
        self,
        patient_id: str,
        risk_level: RiskLevel,
        risk_probability: float,
        risk_factors: RiskFactors
    ) -> str:
        """Generate detailed notes for care coordinator"""
        
        if not self.enabled:
            return None
        
        conditions_str = ", ".join(risk_factors.conditions) if risk_factors.conditions else "none"
        
        prompt = f"""
Create clinical handoff notes for care coordination team about a {risk_level.value} risk patient.

**Patient Summary:**
- ID: {patient_id}
- Readmission Risk Score: {risk_probability:.1%}
- Age: {risk_factors.age}
- Comorbidity Burden: {risk_factors.comorbidity_index} (Charlson Index)
- Active Conditions: {conditions_str}
- Recent Admissions: {risk_factors.previous_admissions_12m} in past 12 months
- Medication Regimen: {risk_factors.medications_count} medications
- ICU Care Required: {'Yes' if risk_factors.icu_stay else 'No'}

**Instructions:**
Write professional care coordination notes (200-250 words) for the care team including:
1. **Risk Assessment Summary**: Why this patient is {risk_level.value} risk
2. **Key Concerns**: What specifically makes them vulnerable
3. **Coordination Priorities**: What the care team should focus on
4. **Recommended Interventions**: Specific actions needed
5. **Follow-up Timeline**: Critical touchpoints

Use clinical but clear language for healthcare professionals.
"""
        
        response = self._call_llm(prompt)
        return response


# Singleton instance
llm_service = LLMService()
