import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas import ChatPayload, ContactPayload, LeadPayload
from app.services.lead_service import create_lead
from chatbot.chatbot_engine import get_bot_response


logger = logging.getLogger("coepd-api")
router = APIRouter()


FALLBACK_RESPONSE = {
    "reply": (
        "I'm sorry, I'm having trouble answering that right now.\n"
        "But I can still help you book a free demo session."
    ),
    "options": [
        "Book Free Demo",
        "Program Benefits",
        "Course Details",
        "Duration",
        "Placement Support",
    ],
    "placeholder": "Tap an option or type your question...",
    "meta": {"progress": 0},
}


def _to_chat_response(payload: dict) -> dict:
    reply = str(payload.get("reply") or payload.get("text") or "").strip()
    raw_options = payload.get("options") or []
    options: list[str] = []
    for item in raw_options:
        if isinstance(item, str):
            value = item.strip()
        elif isinstance(item, dict):
            value = str(item.get("label") or item.get("value") or "").strip()
        else:
            value = str(item).strip()
        if value:
            options.append(value)

    response = {
        "reply": reply,
        "options": options,
    }

    if "placeholder" in payload:
        response["placeholder"] = payload["placeholder"]
    if "meta" in payload:
        response["meta"] = payload["meta"]
    if "lead_payload" in payload:
        response["lead_payload"] = payload["lead_payload"]
    return response


@router.post("/chat")
async def chat(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = ChatPayload(**(await request.json()))
        else:
            form = await request.form()
            payload = ChatPayload(
                message=str(form.get("message", "")).strip(),
                user_id=str(form.get("user_id", "web_user")).strip() or "web_user",
            )
    except Exception as exc:
        logger.warning("/chat bad request: %s", exc)
        return FALLBACK_RESPONSE

    try:
        return _to_chat_response(get_bot_response(payload.message, user_id=payload.user_id))
    except Exception as exc:
        logger.exception("/chat engine error")
        return FALLBACK_RESPONSE


@router.post("/lead")
async def lead(payload: LeadPayload):
    try:
        lead_id = create_lead(payload.model_dump())
        return {"ok": True, "id": lead_id}
    except Exception as exc:
        logger.exception("/lead failed")
        raise HTTPException(status_code=500, detail="Unable to store lead") from exc


@router.post("/contact")
async def contact(payload: ContactPayload):
    try:
        lead_id = create_lead(
            {
                "name": payload.name,
                "phone": payload.phone,
                "email": payload.email,
                "location": payload.location,
                "interested_domain": payload.interested_domain,
                "experience": payload.experience,
                "demo_day": payload.demo_day,
                "whatsapp": payload.whatsapp,
                "source": payload.source or "webpage",
                "created_at": payload.created_at,
            }
        )
        return {"ok": True, "id": lead_id}
    except Exception as exc:
        logger.exception("/contact failed")
        raise HTTPException(status_code=500, detail="Unable to store contact lead") from exc


@router.post("/enquiry")
async def enquiry(payload: ContactPayload):
    """Alias for /contact — used by some frontend deployments."""
    return await contact(payload)
