import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas import ChatPayload, ContactPayload, LeadPayload
from app.services.lead_service import create_lead
from chatbot.db import load_session, save_session
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
    lower_reply = reply.lower()
    if "whatsapp number" in lower_reply or "10-digit whatsapp" in lower_reply:
        reply = (
            "Thank you for sharing your details.\n\n"
            "Our advisor will contact you shortly.\n\n"
            "You can also join our Free Demo Session to understand the program in detail."
        )
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
        response = _to_chat_response(get_bot_response(payload.message, user_id=payload.user_id))

        # Persist chatbot lead immediately from backend when lead_payload is emitted.
        lead_payload = response.get("lead_payload")
        if isinstance(lead_payload, dict):
            try:
                create_lead(lead_payload)
                # Mark session once a chatbot lead is persisted to prevent fail-safe duplicate insert.
                session = load_session(payload.user_id)
                stage = str(session.get("stage") or "chat")
                data = session.get("data") if isinstance(session.get("data"), dict) else {}
                data["lead_saved"] = True
                save_session(payload.user_id, stage, data)
                # Prevent duplicate saves from frontend follow-up /lead call.
                response.pop("lead_payload", None)
            except Exception:
                logger.exception("/chat lead auto-save failed")

        # Fail-safe: persist once domain is selected, even if lead_payload key is absent.
        try:
            session = load_session(payload.user_id)
            stage = str(session.get("stage") or "")
            data = session.get("data") if isinstance(session.get("data"), dict) else {}
            if data and not data.get("lead_saved"):
                name = str(data.get("name") or "").strip()
                phone = str(data.get("phone") or "").strip()
                email = str(data.get("email") or "").strip().lower()
                location = str(data.get("location") or "").strip()
                interested_domain = str(data.get("interested_domain") or "").strip()
                if name and phone and email and location and interested_domain:
                    create_lead(
                        {
                            "name": name,
                            "phone": phone,
                            "email": email,
                            "location": location,
                            "interested_domain": interested_domain,
                            "whatsapp": "",
                            "source": "chatbot",
                        }
                    )
                    data["lead_saved"] = True
                    save_session(payload.user_id, stage or "chat", data)
        except Exception:
            logger.exception("/chat lead fail-safe save failed")

        return response
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
    """Alias for /contact â€” used by some frontend deployments."""
    return await contact(payload)
