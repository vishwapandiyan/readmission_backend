"""
Post-Care AI WhatsApp Follow-Up Agent Service
Powered by Groq API (Llama 3.1) and Meta WhatsApp Cloud API
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import uuid
import logging
import httpx
from groq import Groq

from app.core.config import settings
from app.models.agent_models import (
    HighRiskPatientEnrollRequest,
    AgentChatResponse,
    AgentSessionResponse,
    TriageStatus
)

logger = logging.getLogger(__name__)


# Disease-specific clinical guidelines and warning signs
DISEASE_GUIDELINES: Dict[str, Dict[str, Any]] = {
    "heart failure": {
        "key_focus": "Daily morning weigh-in, fluid retention, shortness of breath, salt restriction",
        "red_flags": [
            "Weight gain of >2-3 lbs in 1 day or >5 lbs in 1 week",
            "Worsening shortness of breath when lying flat (needs extra pillows)",
            "Noticeable swelling in legs, ankles, or abdomen",
            "Chest pain, pressure, or racing heartbeat",
            "Persistent dry cough or coughing pink frothy mucus"
        ],
        "daily_questions": [
            "Did you check your weight this morning on an empty stomach?",
            "Are you having any trouble breathing when lying flat in bed?",
            "Have you noticed any new swelling in your feet or ankles?"
        ],
        "medication_reminder": "Remember to take your water pills (diuretics) and blood pressure medications as prescribed."
    },
    "diabetes": {
        "key_focus": "Blood glucose tracking, hypoglycemia/hyperglycemia signs, meal balance, foot checks",
        "red_flags": [
            "Blood sugar below 70 mg/dL (hypoglycemia: shaky, sweaty, confused)",
            "Blood sugar above 250-300 mg/dL persistently",
            "Nausea, vomiting, fruity-smelling breath (DKA risk)",
            "New sores, cuts, or redness on feet that are not healing",
            "Severe dizziness or fainting"
        ],
        "daily_questions": [
            "What was your fasting blood sugar reading this morning?",
            "Have you felt shaky, sweaty, or unusually dizzy today?",
            "Did you take your insulin or diabetes medication on time with your meal?"
        ],
        "medication_reminder": "Keep fast-acting glucose (juice/candies) nearby in case your sugar drops."
    },
    "copd": {
        "key_focus": "Breathing difficulty, inhaler technique, sputum color and volume, avoiding irritants",
        "red_flags": [
            "Severe shortness of breath not relieved by rescue inhaler",
            "Sputum turning thick, dark yellow, green, or brown",
            "Chest pain or bluish color on lips/fingernails",
            "Fever or chills with increased cough",
            "Confusion or excessive sleepiness"
        ],
        "daily_questions": [
            "How is your breathing today compared to when you left the hospital?",
            "Have you had to use your rescue inhaler more often than usual?",
            "Have you noticed any change in the color or thickness of your phlegm?"
        ],
        "medication_reminder": "Always rinse your mouth with water after using your steroid inhaler."
    },
    "chronic kidney disease": {
        "key_focus": "Fluid management, blood pressure control, low-potassium/low-sodium diet, avoiding NSAIDs",
        "red_flags": [
            "Significant decrease in urine output",
            "Severe swelling in face, hands, or legs",
            "Nausea, metallic taste in mouth, or complete loss of appetite",
            "Sudden spike in blood pressure",
            "Irregular heartbeat or severe muscle weakness"
        ],
        "daily_questions": [
            "Have you noticed any decrease in how often you urinate?",
            "What was your latest blood pressure reading?",
            "Are you experiencing any nausea or swelling today?"
        ],
        "medication_reminder": "Avoid over-the-counter painkillers like Ibuprofen or Naproxen as they harm your kidneys."
    },
    "hypertension": {
        "key_focus": "Blood pressure tracking, headache, vision changes, medication compliance",
        "red_flags": [
            "Blood pressure reading >180/120 (Hypertensive Crisis)",
            "Severe throbbing headache or blurry vision",
            "Chest tightness or shortness of breath",
            "Sudden numbness or weakness in face, arm, or leg"
        ],
        "daily_questions": [
            "What was your blood pressure reading today?",
            "Are you experiencing any headaches or dizziness?",
            "Did you take your morning blood pressure medication?"
        ],
        "medication_reminder": "Do not skip doses even if you feel completely fine."
    }
}


class PostCareAgentService:
    """AI Post-Care Follow-up Service for High-Risk Patients"""

    def __init__(self):
        self.groq_client = None
        self.enabled = False
        if settings.LLM_ENABLED and settings.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                self.model = settings.GROQ_MODEL
                self.enabled = True
                logger.info("✓ Post-Care AI Agent initialized with Groq")
            except Exception as e:
                logger.error(f"Failed to initialize Groq for Agent: {e}")

        # In-memory storage for active sessions & chat histories
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.phone_to_session: Dict[str, str] = {}

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to digits with plus"""
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    def _get_disease_context(self, disease_str: str) -> Tuple[str, Dict[str, Any]]:
        """Find matching disease guidelines"""
        d_lower = disease_str.lower()
        for key, guide in DISEASE_GUIDELINES.items():
            if key in d_lower or d_lower in key:
                return key, guide
        
        # Default high-risk general guidance
        return "general high-risk recovery", {
            "key_focus": "Medication adherence, vital signs tracking, wound/symptom check, doctor follow-up",
            "red_flags": ["Severe sudden pain", "High fever over 101°F", "Shortness of breath", "Inability to keep food/water down"],
            "daily_questions": ["How are you feeling overall today?", "Did you pick up and take your discharge medications?"],
            "medication_reminder": "Take all medications exactly as directed on your discharge summary."
        }

    async def enroll_patient(self, request: HighRiskPatientEnrollRequest) -> Tuple[AgentSessionResponse, str]:
        """
        Enroll a high-risk patient into the WhatsApp AI Post-Care system.
        Generates personalized welcome message and sends via Meta WhatsApp Cloud API.
        """
        phone = self._normalize_phone(request.phone_number)
        session_id = f"PCS-{uuid.uuid4().hex[:8].upper()}"
        
        # Create session record
        session_data = {
            "session_id": session_id,
            "patient_id": request.patient_id or f"P-{uuid.uuid4().hex[:6].upper()}",
            "patient_name": request.name,
            "phone_number": phone,
            "disease": request.disease,
            "risk_score": request.risk_score,
            "medications": request.medications or [],
            "discharge_date": request.discharge_date or datetime.utcnow(),
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
            "last_interaction_at": datetime.utcnow(),
            "history": []
        }

        self.sessions[session_id] = session_data
        self.phone_to_session[phone] = session_id

        # Generate initial personalized welcome message
        welcome_message = self._generate_welcome_message(
            name=request.name,
            disease=request.disease,
            medications=request.medications or []
        )

        # Log message in history
        session_data["history"].append({
            "sender": "AGENT",
            "message": welcome_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Send via WhatsApp API
        delivery_status = "SIMULATED"
        if request.send_whatsapp_now:
            delivery_status = await self.send_whatsapp_message(
                to_phone=phone,
                message_text=welcome_message
            )

        response = AgentSessionResponse(
            session_id=session_id,
            patient_id=session_data["patient_id"],
            patient_name=session_data["patient_name"],
            phone_number=phone,
            disease=session_data["disease"],
            risk_score=session_data["risk_score"],
            status=session_data["status"],
            messages_count=len(session_data["history"]),
            created_at=session_data["created_at"],
            last_interaction_at=session_data["last_interaction_at"],
            conversation_history=session_data["history"]
        )

        return response, welcome_message

    def _generate_welcome_message(self, name: str, disease: str, medications: List[str]) -> str:
        """Generate empathetic, disease-targeted opening WhatsApp message using Groq"""
        disease_key, guidelines = self._get_disease_context(disease)
        meds_text = ", ".join(medications) if medications else "your prescribed medicines"

        prompt = f"""
You are {settings.AGENT_NAME}, an empathetic and professional AI Post-Discharge Care Coordinator for {settings.HOSPITAL_NAME}.
You are sending the very first WhatsApp welcome message to a HIGH RISK patient who just got discharged.

Patient Details:
- Name: {name}
- Primary Condition/Disease: {disease}
- Discharge Medications: {meds_text}
- Disease Clinical Focus: {guidelines['key_focus']}
- Key Warning Signs to Watch For: {', '.join(guidelines['red_flags'][:3])}

Instructions:
1. Warmly greet {name} by first name and introduce yourself as their dedicated AI Care Assistant from {settings.HOSPITAL_NAME}.
2. Reassure them that you are checking in to support their recovery at home with their {disease}.
3. Give ONE clear, disease-specific recovery reminder (e.g. daily weigh-in for Heart Failure, sugar check for Diabetes, inhaler for COPD).
4. Ask 1 gentle, simple opening question (e.g. "Did you manage to get your discharge medicines from the pharmacy?", "How are you feeling right now?").
5. Format for WhatsApp: Use friendly tone, clear spacing, and 2-3 appropriate emojis (e.g. 🩺, 💊, 💙).
6. Keep it concise (under 120 words). Do NOT use markdown headers (#).
"""
        if self.enabled and self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a clinical care coordinator assistant writing WhatsApp messages to patients."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                return completion.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Groq welcome message generation error: {e}")

        # Fallback template
        return (
            f"Hello {name}, 🩺\n\n"
            f"This is {settings.AGENT_NAME} from the {settings.HOSPITAL_NAME} Care Team.\n\n"
            f"We are checking in to help you recover safely at home with your **{disease}**. "
            f"We will be checking on you daily to help you track your symptoms and medications.\n\n"
            f"💊 **Quick Check:** Did you pick up your prescribed discharge medicines, and how are you feeling today?"
        )

    def generate_scheduled_followup(self, session_id: str, followup_day: int = 1, custom_note: Optional[str] = None) -> str:
        """Generate a structured daily check-in message based on disease and post-discharge day"""
        session = self.sessions.get(session_id)
        if not session:
            return "Session not found."

        name = session["patient_name"]
        disease = session["disease"]
        disease_key, guidelines = self._get_disease_context(disease)

        prompt = f"""
You are {settings.AGENT_NAME}, AI Post-Discharge Care Assistant for {settings.HOSPITAL_NAME}.
Send a Day {followup_day} WhatsApp check-in to {name}, who is recovering from {disease}.

Clinical Focus for {disease}:
- Key Focus: {guidelines['key_focus']}
- Typical Questions: {', '.join(guidelines['daily_questions'])}
- Medication Reminder: {guidelines['medication_reminder']}
{f'- Clinician Custom Note: {custom_note}' if custom_note else ''}

Instructions:
1. Greet {name} warmly for their Day {followup_day} check-in.
2. Ask 2 specific, targeted questions regarding their {disease} (e.g. today's readings, symptoms, or medication).
3. Mention 1 key red flag symptom they should tell you immediately if they feel it.
4. Keep it conversational, friendly, and formatted for WhatsApp (under 120 words). Use emojis.
"""
        if self.enabled and self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a clinical care assistant generating WhatsApp follow-up check-ins."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                msg = completion.choices[0].message.content.strip()
                session["history"].append({
                    "sender": "AGENT",
                    "message": msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                return msg
            except Exception as e:
                logger.error(f"Groq follow-up generation error: {e}")

        # Fallback
        q = guidelines["daily_questions"][0] if guidelines["daily_questions"] else "How are your symptoms today?"
        msg = f"Good day {name}! 🩺 It is Day {followup_day} of your recovery. {q} Please reply here so we can keep your care team updated! 💙"
        session["history"].append({
            "sender": "AGENT",
            "message": msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        return msg

    async def process_patient_message(
        self,
        phone_number: str,
        patient_message: str,
        session_id: Optional[str] = None
    ) -> AgentChatResponse:
        """
        Process an incoming WhatsApp reply from a patient:
        1. Evaluates symptoms and vitals using Groq AI.
        2. Triages for RED FLAGS (Safe / Warning / Critical Emergency).
        3. Formats clinical AI response.
        4. Sends reply back to patient via WhatsApp API.
        """
        phone = self._normalize_phone(phone_number)
        if not session_id:
            session_id = self.phone_to_session.get(phone)

        # If no active session, auto-create a default high-risk session
        if not session_id or session_id not in self.sessions:
            session_id = f"PCS-{uuid.uuid4().hex[:8].upper()}"
            self.sessions[session_id] = {
                "session_id": session_id,
                "patient_id": "P-AUTO",
                "patient_name": "Valued Patient",
                "phone_number": phone,
                "disease": "Heart Failure / High Risk",
                "risk_score": 0.85,
                "medications": [],
                "status": "ACTIVE",
                "created_at": datetime.utcnow(),
                "last_interaction_at": datetime.utcnow(),
                "history": []
            }
            self.phone_to_session[phone] = session_id

        session = self.sessions[session_id]
        session["last_interaction_at"] = datetime.utcnow()

        # Log inbound message
        session["history"].append({
            "sender": "PATIENT",
            "message": patient_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        disease = session["disease"]
        disease_key, guidelines = self._get_disease_context(disease)

        # Multi-turn conversation context
        recent_history = session["history"][-6:]  # Last 6 exchanges
        history_formatted = "\n".join([f"{h['sender']}: {h['message']}" for h in recent_history])

        # LLM Prompt for Clinical Triage & Response
        prompt = f"""
You are {settings.AGENT_NAME}, an expert Clinical Post-Care AI Agent for {settings.HOSPITAL_NAME}.
You are conversing with a patient on WhatsApp who has HIGH RISK of 30-day hospital readmission.

Patient Profile:
- Name: {session['patient_name']}
- Primary Disease: {disease}
- Prescribed Medications: {', '.join(session.get('medications', [])) if session.get('medications') else 'Standard regimen'}
- Known Clinical Red Flags for this Disease: {', '.join(guidelines['red_flags'])}

Recent Conversation Transcript:
{history_formatted}

Patient's Latest WhatsApp Message:
"{patient_message}"

TASK:
1. Analyze the patient's message carefully.
2. Triage their condition into one of three statuses:
   - "CRITICAL_EMERGENCY": Severe chest pain, acute inability to breathe, blood sugar <50 or >350, sudden weakness, rapid weight spike >3 lbs overnight with severe edema.
   - "WARNING_MONITOR": Moderate symptoms, mild side effects, missed doses, mild dizziness, mild swelling.
   - "SAFE": Feeling good, normal vitals, picked up meds, adhering to instructions.
3. Write a supportive, clear WhatsApp response:
   - If CRITICAL: Tell them with high urgency to call 911 / visit the nearest ER immediately, while reassuring them.
   - If WARNING: Provide clear safe at-home advice and notify them that their nurse will follow up.
   - If SAFE: Encourage them, validate their good habits, and provide reassurance.
4. Output STRICT JSON format with keys:
   - "triage_status": "SAFE" or "WARNING_MONITOR" or "CRITICAL_EMERGENCY"
   - "red_flags": list of strings (detected red flags or empty list)
   - "extracted_vitals": object of any vitals mentioned (e.g. {"blood_pressure": "140/90", "blood_sugar": 180, "weight_lbs": 178})
   - "whatsapp_reply": the message to send back to the patient on WhatsApp (under 130 words, with friendly emojis)
   - "care_team_alert": boolean (true if triage is WARNING or CRITICAL)
"""

        triage_status = TriageStatus.SAFE
        red_flags: List[str] = []
        extracted_vitals: Dict[str, Any] = {}
        agent_reply = "Thank you for updating us! We have logged your response and our care team is monitoring your progress. 💙"
        care_team_alert = False

        if self.enabled and self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a clinical decision AI system. Always output valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"} if hasattr(self.groq_client, "chat") else None,
                    max_tokens=400
                )
                content = completion.choices[0].message.content
                parsed = json.loads(content)
                
                raw_triage = parsed.get("triage_status", "SAFE").upper()
                if "CRITICAL" in raw_triage or "EMERGENCY" in raw_triage:
                    triage_status = TriageStatus.CRITICAL_EMERGENCY
                elif "WARNING" in raw_triage or "MONITOR" in raw_triage:
                    triage_status = TriageStatus.WARNING_MONITOR
                else:
                    triage_status = TriageStatus.SAFE

                red_flags = parsed.get("red_flags", [])
                extracted_vitals = parsed.get("extracted_vitals", {})
                agent_reply = parsed.get("whatsapp_reply", agent_reply)
                care_team_alert = parsed.get("care_team_alert", triage_status != TriageStatus.SAFE)

            except Exception as e:
                logger.error(f"Error parsing LLM triage response: {e}")

        # Update session status
        if triage_status == TriageStatus.CRITICAL_EMERGENCY:
            session["status"] = "ALERTED_CARE_TEAM_EMERGENCY"
        elif triage_status == TriageStatus.WARNING_MONITOR:
            session["status"] = "NEEDS_CLINICAL_ATTENTION"

        # Log AI reply
        session["history"].append({
            "sender": "AGENT",
            "message": agent_reply,
            "triage": triage_status.value,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Send response via Meta WhatsApp Cloud API
        delivery_status = await self.send_whatsapp_message(
            to_phone=phone,
            message_text=agent_reply
        )

        return AgentChatResponse(
            session_id=session_id,
            patient_name=session["patient_name"],
            phone_number=phone,
            disease=session["disease"],
            patient_message=patient_message,
            agent_reply=agent_reply,
            triage_status=triage_status,
            red_flags_detected=red_flags,
            extracted_vitals=extracted_vitals,
            whatsapp_status=delivery_status,
            care_team_notified=care_team_alert
        )

    async def send_whatsapp_message(self, to_phone: str, message_text: str) -> str:
        """
        Dispatch WhatsApp message using Meta WhatsApp Cloud API (Graph API).
        If credentials are not configured, smoothly logs and simulates delivery.
        """
        token = settings.WHATSAPP_API_TOKEN
        phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        version = settings.WHATSAPP_API_VERSION

        # Normalize recipient phone: Meta expects plain digits e.g. 15559876543
        clean_recipient = "".join(c for c in to_phone if c.isdigit())

        # If live Meta credentials provided, send HTTP POST to Meta Graph API
        if token and phone_number_id and clean_recipient:
            url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_recipient,
                "type": "text",
                "text": {"preview_url": False, "body": message_text}
            }
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code in [200, 201]:
                        logger.info(f"✓ Meta WhatsApp sent to {clean_recipient}")
                        return "DELIVERED_VIA_META_API"
                    else:
                        logger.warning(f"Meta WhatsApp API error ({resp.status_code}): {resp.text}")
                        return f"META_ERROR_{resp.status_code}"
            except Exception as e:
                logger.error(f"Failed to connect to Meta WhatsApp API: {e}")
                return "META_CONNECTION_FAILED"

        # Simulation Mode
        logger.info(f"[WHATSAPP SIMULATION] To: {to_phone} | Message: {message_text[:60]}...")
        return "SIMULATED_SUCCESS"

    def list_sessions(self) -> List[AgentSessionResponse]:
        """List all active patient follow-up sessions"""
        results = []
        for s in self.sessions.values():
            results.append(
                AgentSessionResponse(
                    session_id=s["session_id"],
                    patient_id=s.get("patient_id"),
                    patient_name=s["patient_name"],
                    phone_number=s["phone_number"],
                    disease=s["disease"],
                    risk_score=s.get("risk_score", 0.8),
                    status=s.get("status", "ACTIVE"),
                    messages_count=len(s.get("history", [])),
                    created_at=s.get("created_at", datetime.utcnow()),
                    last_interaction_at=s.get("last_interaction_at", datetime.utcnow()),
                    conversation_history=s.get("history", [])
                )
            )
        return results

    def get_session(self, session_id: str) -> Optional[AgentSessionResponse]:
        """Get details for a specific follow-up session"""
        s = self.sessions.get(session_id)
        if not s:
            return None
        return AgentSessionResponse(
            session_id=s["session_id"],
            patient_id=s.get("patient_id"),
            patient_name=s["patient_name"],
            phone_number=s["phone_number"],
            disease=s["disease"],
            risk_score=s.get("risk_score", 0.8),
            status=s.get("status", "ACTIVE"),
            messages_count=len(s.get("history", [])),
            created_at=s.get("created_at", datetime.utcnow()),
            last_interaction_at=s.get("last_interaction_at", datetime.utcnow()),
            conversation_history=s.get("history", [])
        )


agent_service = PostCareAgentService()
