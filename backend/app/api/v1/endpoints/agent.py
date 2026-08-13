"""
Post-Care AI WhatsApp Agent API Endpoints
Handles Patient Enrollment, Scheduled Check-Ins, Interactive Chat, and Meta WhatsApp Webhooks.
"""
from fastapi import APIRouter, HTTPException, status, Query, Request, Response, Body
from typing import Dict, Any, List, Optional
import logging

from app.models.agent_models import (
    HighRiskPatientEnrollRequest,
    FollowUpTriggerRequest,
    AgentChatRequest,
    AgentChatResponse,
    AgentSessionResponse,
    WhatsAppWebhookPayload
)
from app.services.agent_service import agent_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/enroll",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Enroll High-Risk Patient into WhatsApp AI Follow-Up",
    description="Accepts required patient features (name, phone number, disease) and initiates personalized post-care WhatsApp outreach via Meta API"
)
async def enroll_patient(request: HighRiskPatientEnrollRequest):
    """
    Enroll a high-risk patient:
    - Input: `name`, `phone_number`, `disease` (e.g. Heart Failure, Diabetes, COPD, etc.)
    - Generates personalized, disease-tailored WhatsApp welcome & check-in message via Groq Llama 3.1
    - Dispatches message directly to the patient's WhatsApp via Meta WhatsApp Cloud API
    """
    try:
        session, welcome_msg = await agent_service.enroll_patient(request)
        return {
            "success": True,
            "message": "Patient enrolled in AI Post-Care WhatsApp Agent successfully",
            "session": session,
            "initial_whatsapp_message": welcome_msg
        }
    except Exception as e:
        logger.error(f"Enrollment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll patient: {str(e)}"
        )


@router.post(
    "/trigger-followup",
    response_model=Dict[str, Any],
    summary="Trigger Disease-Specific WhatsApp Follow-Up",
    description="Manually or automatically triggers Day 1, Day 3, Day 7, or custom milestone check-in based on patient disease"
)
async def trigger_followup(request: FollowUpTriggerRequest):
    """Trigger a scheduled disease-targeted WhatsApp check-in"""
    session_id = request.session_id
    if not session_id and request.phone_number:
        clean_phone = agent_service._normalize_phone(request.phone_number)
        session_id = agent_service.phone_to_session.get(clean_phone)

    if not session_id or session_id not in agent_service.sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active session not found. Please enroll the patient first."
        )

    session = agent_service.sessions[session_id]
    msg = agent_service.generate_scheduled_followup(
        session_id=session_id,
        followup_day=request.followup_day,
        custom_note=request.custom_note
    )

    # Send via WhatsApp API
    delivery_status = await agent_service.send_whatsapp_message(
        to_phone=session["phone_number"],
        message_text=msg
    )

    return {
        "success": True,
        "session_id": session_id,
        "followup_day": request.followup_day,
        "disease": session["disease"],
        "message_sent": msg,
        "delivery_status": delivery_status
    }


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Interactive Patient Chat / Simulation",
    description="Simulate or process a patient WhatsApp message, triage symptoms with Groq, and return AI response"
)
async def process_chat(request: AgentChatRequest):
    """
    Process patient reply:
    - Analyzes symptoms, vitals, and red flags using Groq
    - Triages risk (SAFE, WARNING_MONITOR, CRITICAL_EMERGENCY)
    - Sends clinical WhatsApp reply via Meta API
    """
    phone = request.phone_number or "+15559876543"
    try:
        response = await agent_service.process_patient_message(
            phone_number=phone,
            patient_message=request.patient_message,
            session_id=request.session_id
        )
        return response
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(e)}"
        )


@router.get(
    "/sessions",
    response_model=List[AgentSessionResponse],
    summary="List Active Post-Care Follow-Up Sessions"
)
async def list_sessions():
    """List all high-risk patient AI follow-up sessions"""
    return agent_service.list_sessions()


@router.get(
    "/sessions/{session_id}",
    response_model=AgentSessionResponse,
    summary="Get Session Chat History & Triage Status"
)
async def get_session(session_id: str):
    """Retrieve full WhatsApp conversation history and clinical triage status for a patient"""
    session = agent_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return session


# ============================================================================
# Meta WhatsApp Cloud API Webhook Handlers
# ============================================================================

@router.get(
    "/whatsapp/webhook",
    summary="Meta WhatsApp Webhook Verification",
    description="Handles Meta's hub.challenge verification request when configuring your webhook in Meta App Dashboard"
)
async def verify_meta_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """Meta Webhook Challenge Handshake"""
    logger.info(f"Meta webhook verification handshake: mode={hub_mode}, token={hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("✓ Meta WhatsApp Webhook verified successfully!")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.warning("Meta Webhook verification token mismatch")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch"
    )


@router.post(
    "/whatsapp/webhook",
    summary="Meta WhatsApp Live Inbound Message Receiver",
    description="Receives real-time patient WhatsApp messages from Meta Graph API, processes with Groq AI, and auto-replies"
)
async def receive_meta_whatsapp_message(request: Request):
    """Process incoming WhatsApp message events from Meta Cloud API"""
    try:
        data = await request.json()
        logger.info("Received Meta WhatsApp Webhook event")

        # Parse Meta WhatsApp Cloud API payload format
        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    if msg.get("type") == "text":
                        sender_phone = msg.get("from")  # e.g. "15559876543"
                        message_body = msg.get("text", {}).get("body", "")

                        if sender_phone and message_body:
                            logger.info(f"Inbound WhatsApp from +{sender_phone}: {message_body}")
                            # Feed into Post-Care AI Agent
                            await agent_service.process_patient_message(
                                phone_number=f"+{sender_phone}",
                                patient_message=message_body
                            )

        return {"status": "EVENT_RECEIVED"}
    except Exception as e:
        logger.error(f"Error handling Meta WhatsApp webhook: {e}")
        return {"status": "ERROR", "detail": str(e)}
