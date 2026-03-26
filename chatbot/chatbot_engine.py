from __future__ import annotations

import re
from typing import Any

from .db import load_session, save_session


INITIAL_GREETING = "Welcome to COEPD 👋\nHow can I help you know?"
DETAILS_PROMPT = "Thank you for reaching out 😊\nTo assist you better, please share your details."
ASK_NAME = "May I know your name?"
ASK_PHONE = "Please share your phone number."
ASK_EMAIL = "Please provide your email address."
ASK_LOCATION = "Your current location?"
FINAL_MESSAGE = (
    "Thank you for sharing your details 🙌\n"
    "Our team will reach out to you shortly.\n\n"
    "If you have more queries, feel free to visit our office in Hyderabad\n"
    "or contact us at +91 88850 24387 📞"
)

PHONE_RE = re.compile(r"^\d{10}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _ui(
    text: str,
    *,
    placeholder: str = "Type your message...",
    progress: int = 0,
    stage: str | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {"progress": progress}
    if stage:
        meta["stage"] = stage
    return {"text": text, "options": [], "placeholder": placeholder, "meta": meta}


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def get_bot_response(user_message: str, user_id: str = "web_user") -> dict[str, Any]:
    message = (user_message or "").strip()
    session = load_session(user_id)
    stage = str(session.get("stage") or "greeting")
    data = session.get("data") if isinstance(session.get("data"), dict) else {}

    if stage in {"start", "chat"}:
        stage = "greeting"
        save_session(user_id, stage, data)

    if message in {"__restart__"}:
        data = {}
        save_session(user_id, "greeting", data)
        return _ui(INITIAL_GREETING, placeholder="Type your message...", progress=5, stage="greeting")

    if message in {"__init__", ""}:
        if stage == "greeting":
            return _ui(INITIAL_GREETING, placeholder="Type your message...", progress=5, stage="greeting")
        if stage == "collect_name":
            return _ui(ASK_NAME, placeholder="Enter your full name", progress=20, stage="collect_name")
        if stage == "collect_phone":
            return _ui(ASK_PHONE, placeholder="10-digit phone number", progress=40, stage="collect_phone")
        if stage == "collect_email":
            return _ui(ASK_EMAIL, placeholder="name@example.com", progress=60, stage="collect_email")
        if stage == "collect_location":
            return _ui(ASK_LOCATION, placeholder="e.g. Hyderabad", progress=80, stage="collect_location")
        return _ui(FINAL_MESSAGE, progress=100, stage="completed")

    if stage == "greeting":
        save_session(user_id, "collect_name", data)
        return _ui(
            f"{DETAILS_PROMPT}\n\n{ASK_NAME}",
            placeholder="Enter your full name",
            progress=20,
            stage="collect_name",
        )

    if stage == "collect_name":
        if len(message) < 2:
            return _ui("Please enter a valid name.", placeholder="Enter your full name", progress=20, stage="collect_name")
        data["name"] = message.title()
        save_session(user_id, "collect_phone", data)
        return _ui(ASK_PHONE, placeholder="10-digit phone number", progress=40, stage="collect_phone")

    if stage == "collect_phone":
        phone = _normalize_phone(message)
        if not PHONE_RE.fullmatch(phone):
            return _ui(
                "Please enter a valid 10-digit phone number.",
                placeholder="e.g. 9876543210",
                progress=40,
                stage="collect_phone",
            )
        data["phone"] = phone
        save_session(user_id, "collect_email", data)
        return _ui(ASK_EMAIL, placeholder="name@example.com", progress=60, stage="collect_email")

    if stage == "collect_email":
        email = message.lower().strip()
        if not EMAIL_RE.fullmatch(email):
            return _ui("Please enter a valid email address.", placeholder="name@example.com", progress=60, stage="collect_email")
        data["email"] = email
        save_session(user_id, "collect_location", data)
        return _ui(ASK_LOCATION, placeholder="e.g. Hyderabad", progress=80, stage="collect_location")

    if stage == "collect_location":
        if len(message) < 2:
            return _ui("Please enter your current location.", placeholder="e.g. Hyderabad", progress=80, stage="collect_location")
        data["location"] = message.title()
        save_session(user_id, "completed", data)
        response = _ui(FINAL_MESSAGE, progress=100, stage="completed")
        response["lead_payload"] = {
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "location": data.get("location", ""),
            "interested_domain": "",
            "whatsapp": "",
            "source": "chatbot",
        }
        return response

    return _ui(FINAL_MESSAGE, progress=100, stage="completed")
