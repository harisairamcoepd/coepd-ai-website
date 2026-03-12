from __future__ import annotations

import re
from typing import Any

from .db import load_session, save_session
from .intent_engine import detect_intent


QUICK_ACTIONS = [
    {"label": "Course Details", "value": "Course Details"},
    {"label": "Duration", "value": "Duration"},
    {"label": "Placement Support", "value": "Placement Support"},
    {"label": "Program Benefits", "value": "Program Benefits"},
    {"label": "Batch Timings", "value": "Batch Timings"},
    {"label": "Book Free Demo", "value": "Book Free Demo"},
]

FEES_FOLLOWUP_ACTIONS = [
    {"label": "Book Free Demo", "value": "Book Free Demo"},
    {"label": "Program Benefits", "value": "Program Benefits"},
    {"label": "Course Details", "value": "Course Details"},
    {"label": "Duration", "value": "Duration"},
]

DOMAIN_OPTIONS = [
    {"label": "IT", "value": "IT"},
    {"label": "Non-IT", "value": "Non-IT"},
    {"label": "BBA/BCom", "value": "BBA/BCom"},
    {"label": "MBA", "value": "MBA"},
    {"label": "Engineering", "value": "Engineering"},
    {"label": "Fresh Graduate", "value": "Fresh Graduate"},
    {"label": "Other", "value": "Other"},
]

DOMAIN_FOLLOWUP_ACTIONS = [
    {"label": "Course Details", "value": "Course Details"},
    {"label": "Program Benefits", "value": "Program Benefits"},
    {"label": "Placement Support", "value": "Placement Support"},
    {"label": "Book Free Demo", "value": "Book Free Demo"},
]

DOMAIN_RESPONSES = {
    "it": (
        "That's great \U0001f44d\n"
        "IT is the largest employer of Business Analysts worldwide.\n\n"
        "**BA Roles in IT:**\n\n"
        "\u2022 IT Business Analyst\n"
        "\u2022 Systems Analyst\n"
        "\u2022 Product Analyst\n"
        "\u2022 Data Analyst\n\n"
        "**Example Projects:**\n\n"
        "\u2022 Enterprise CRM System\n"
        "\u2022 ERP Implementation\n"
        "\u2022 Cloud Migration Platform\n"
        "\u2022 Agile Project Dashboard"
    ),
    "non-it": (
        "That's great \U0001f44d\n"
        "Business Analysts are in high demand across **Non-IT domains** like Finance, Healthcare, Retail, and Manufacturing.\n\n"
        "**BA Roles in Non-IT:**\n\n"
        "\u2022 Business Process Analyst\n"
        "\u2022 Operations Analyst\n"
        "\u2022 Domain-Specific Business Analyst\n\n"
        "**Example Projects:**\n\n"
        "\u2022 Supply Chain Optimization\n"
        "\u2022 Hospital Management System\n"
        "\u2022 Retail Analytics Platform"
    ),
    "bba/bcom": (
        "That's great \U0001f44d\n"
        "BBA/BCom graduates have strong business fundamentals — perfect for Business Analyst roles.\n\n"
        "**Your Advantages:**\n\n"
        "\u2022 Strong understanding of business processes\n"
        "\u2022 Financial & analytical skills\n"
        "\u2022 Management concepts\n\n"
        "Our program will add the **IT tools & project skills** needed for BA roles."
    ),
    "mba": (
        "Excellent \U0001f44d\n"
        "MBA graduates are highly valued as Business Analysts.\n\n"
        "**Your Advantages:**\n\n"
        "\u2022 Strategic thinking & leadership skills\n"
        "\u2022 Cross-functional business knowledge\n"
        "\u2022 Stakeholder management capabilities\n\n"
        "Our program will enhance your profile with **real-time BA tools & project experience**."
    ),
    "engineering": (
        "That's great \U0001f44d\n"
        "Engineers have excellent analytical thinking — ideal for IT Business Analyst roles.\n\n"
        "**BA Roles for Engineers:**\n\n"
        "\u2022 IT Business Analyst\n"
        "\u2022 Technical Business Analyst\n"
        "\u2022 Systems Analyst\n"
        "\u2022 Data Analyst\n\n"
        "Our program bridges the gap between **engineering skills and BA expertise**."
    ),
    "fresh graduate": (
        "That's perfectly fine \U0001f44d\n"
        "Many fresh graduates transition into Business Analysis.\n\n"
        "You will work on projects like:\n\n"
        "\u2022 Banking Application\n"
        "\u2022 E-commerce Platform\n"
        "\u2022 Healthcare System\n"
        "\u2022 Supply Chain System\n\n"
        "These projects help you gain **real-time BA experience**."
    ),
    "other": (
        "That's absolutely fine \U0001f44d\n"
        "Business Analysts work across **all industries**.\n\n"
        "No matter your background, the COEPD program will help you transition into a BA role "
        "with **real-time projects** based on your domain."
    ),
}

COURSE_DETAILS_ACTIONS = [
    {"label": "Program Benefits", "value": "Program Benefits"},
    {"label": "Placement Support", "value": "Placement Support"},
    {"label": "Batch Timings", "value": "Batch Timings"},
    {"label": "Book Free Demo", "value": "Book Free Demo"},
]

PROGRAM_BENEFITS_ACTIONS = [
    {"label": "Course Details", "value": "Course Details"},
    {"label": "Duration", "value": "Duration"},
    {"label": "Placement Support", "value": "Placement Support"},
    {"label": "Book Free Demo", "value": "Book Free Demo"},
]

FAQ_ANSWERS = {
    "course_details": (
        "Course Structure:\n\n"
        "\u2022 6 Months Business Analyst Training Program\n"
        "\u2022 2 Hours Theory + 4 Hours Hands-On Practical Daily\n"
        "\u2022 Training on Industry Tools\n\n"
        "Tools Covered:\n\n"
        "\u2022 Jira\n"
        "\u2022 SQL\n"
        "\u2022 Tableau\n"
        "\u2022 Power BI\n"
        "\u2022 Balsamiq\n"
        "\u2022 Draw.io\n"
        "\u2022 Agile & Scrum Practices\n\n"
        "Projects:\n\n"
        "\u2022 3 Capstone Projects\n"
        "\u2022 2 Real-Time Live Projects"
    ),
    "program_benefits": (
        "Program Benefits of COEPD Business Analyst Training:\n\n"
        "\u2022 Industry-Focused Training Program\n"
        "\u2022 Suitable for IT and Non-IT Professionals\n"
        "\u2022 No Coding Required\n"
        "\u2022 Real Business Analyst Case Studies\n"
        "\u2022 Global Recognition Certificate (IIBA 40 PD Hours)\n"
        "\u2022 Resume Preparation Support\n"
        "\u2022 Mock Interview Preparation\n"
        "\u2022 Career Transition Guidance\n"
        "\u2022 Dedicated Placement Assistance\n"
        "\u2022 Hostel Facility for Outstation Candidates\n"
        "\u2022 Up to 15% Early Registration Discount"
    ),
    "duration": "The program is a **6-Month Job Ready Business Analyst Program** covering fundamentals, tools training, real-time projects, documentation practice, mock interviews and placement support.",
    "placement": (
        "We offer **100% Placement Guarantee** with a dedicated placement support team, "
        "resume preparation, mock interviews, interview training, and interview scheduling with partner companies. "
        "Most candidates receive offers within **3\u20135 interviews**."
    ),
    "fees": (
        "The course fee depends on current batch offers.\n\n"
        "Currently we provide **up to 15% discount for early registrations**.\n\n"
        "Our program advisor will explain the exact fee during the **Free Demo Session**.\n\n"
        "Would you like to join the upcoming demo?"
    ),
    "placement_support": (
        "Our **100% Placement Guarantee** includes:\n\n"
        "\u2022 Dedicated placement support team\n"
        "\u2022 Resume preparation & LinkedIn optimization\n"
        "\u2022 Mock interviews & interview training\n"
        "\u2022 Interview scheduling with 2700+ hiring partner companies\n"
        "\u2022 Most candidates get offers within **3\u20135 interviews**"
    ),
    "internship": (
        "Our **6-Month Job Ready Business Analyst Program** includes real-time project training as Stage 2.\n\n"
        "Students work on live case studies, BRD/FRD documentation, and hands-on experience with "
        "Power BI, SQL, Excel and Agile Scrum.\n\n"
        "\u2705 2 Hours Theory + 4 Hours Practical Training Daily\n"
        "\u2705 100% Placement Guarantee\n"
        "\u2705 Free Hostel Facility Available\n\n"
        "Book a free demo to learn more about program benefits and batch offers."
    ),
    "batch_timings": "We run both weekday and weekend batches. Training is 2 Hours Theory + 4 Hours Hands-On Practical Training daily.",
}


def _ui(
    text: str,
    options: list[dict[str, str]] | None = None,
    placeholder: str = "Type your message...",
    progress: int = 0,
) -> dict[str, Any]:
    return {
        "text": text,
        "options": options or [],
        "placeholder": placeholder,
        "meta": {"progress": progress},
    }


def _valid_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value or "")
    return len(digits) >= 10


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")[-10:]


def _valid_email(value: str) -> bool:
    if not value or "@" not in value:
        return False
    local, _, domain = value.partition("@")
    return bool(local and domain and "." in domain)


def _start_message() -> dict[str, Any]:
    return _ui(
        "Hello 👋\nWelcome to **COEPD – Centre of Excellence for Professional Development**.\n\n"
        "I can help you with:\n\n"
        "• Course Details\n"
        "• Fees\n"
        "• Placement Support\n"
        "• Free Demo Session\n\n"
        "To guide you better, I need a few details.",
        options=QUICK_ACTIONS,
        placeholder="Tap an option or type your question...",
        progress=10,
    )


def get_bot_response(user_message: str, user_id: str = "web_user") -> dict[str, Any]:
    message = (user_message or "").strip()
    session = load_session(user_id)
    stage = session["stage"]
    data = session["data"]

    if message in {"__init__", ""}:
        if stage == "start":
            save_session(user_id, "chat", data)
        return _start_message()

    if message == "__restart__":
        save_session(user_id, "chat", {})
        return _start_message()

    if stage in {"start", "chat"}:
        intent = detect_intent(message)

        if intent == "book_demo":
            save_session(user_id, "lead_name", data)
            return _ui("Great choice! To guide you better, I need a few details.\n\nWhat is your Full Name?", progress=15)

        if intent in FAQ_ANSWERS:
            text = FAQ_ANSWERS[intent]
            if intent == "course_details":
                return _ui(text, options=COURSE_DETAILS_ACTIONS, progress=25)
            if intent == "program_benefits":
                return _ui(text, options=PROGRAM_BENEFITS_ACTIONS, progress=25)
            if intent == "fees":
                return _ui(text, options=FEES_FOLLOWUP_ACTIONS, progress=25)
            text = f"{text}\n\nWould you like to book a free demo session?"
            return _ui(text, options=QUICK_ACTIONS, progress=25)

        return _ui(
            "I can help with Course Details, Program Benefits, Duration, Placement Support, Batch Timings, Fees, or booking a demo.",
            options=QUICK_ACTIONS,
            progress=20,
        )

    if stage == "lead_name":
        if len(message) < 2:
            return _ui("Please share your full name to continue.", progress=20)
        data["name"] = message.title()
        save_session(user_id, "lead_phone", data)
        return _ui("What is your Phone Number?", placeholder="10-digit phone number", progress=30)

    if stage == "lead_phone":
        if not _valid_phone(message):
            return _ui("Please enter a valid 10-digit phone number.", placeholder="e.g. 9876543210", progress=30)
        data["phone"] = _normalize_phone(message)
        save_session(user_id, "lead_email", data)
        return _ui("What is your Email Address?", placeholder="name@email.com", progress=40)

    if stage == "lead_email":
        if not _valid_email(message):
            return _ui("Please enter a valid email address.", placeholder="name@email.com", progress=40)
        data["email"] = message.strip().lower()
        save_session(user_id, "lead_location", data)
        return _ui("Which City are you currently located in?", placeholder="e.g. Hyderabad", progress=50)

    if stage == "lead_location":
        if len(message) < 2:
            return _ui("Please share your city to continue.", placeholder="e.g. Hyderabad", progress=50)
        data["location"] = message.strip().title()
        save_session(user_id, "lead_domain", data)
        return _ui("What is your Interested Domain?", options=DOMAIN_OPTIONS, progress=60)

    if stage == "lead_domain":
        options = {item["value"].lower(): item["value"] for item in DOMAIN_OPTIONS}
        selected = options.get(message.lower().strip())
        if not selected:
            return _ui("Please select your interested domain.", options=DOMAIN_OPTIONS, progress=60)
        data["interested_domain"] = selected
        domain_text = DOMAIN_RESPONSES.get(selected.lower(), "")
        if domain_text:
            domain_text += (
                "\n\nWould you like to know about the **course structure, program benefits, or placement support**?"
            )
            save_session(user_id, "lead_domain_followup", data)
            return _ui(domain_text, options=DOMAIN_FOLLOWUP_ACTIONS, progress=65)
        save_session(user_id, "lead_experience", data)
        return _ui("How many years of experience do you have?", placeholder="e.g. Fresher / 1 year / 3 years", progress=75)

    if stage == "lead_domain_followup":
        intent = detect_intent(message)
        if intent in FAQ_ANSWERS:
            text = FAQ_ANSWERS[intent]
            text += "\n\nNow, please share your **Experience** (Fresher / years)."
            save_session(user_id, "lead_experience", data)
            return _ui(text, placeholder="e.g. Fresher / 1 year", progress=75)
        save_session(user_id, "lead_experience", data)
        return _ui("How many years of experience do you have?", placeholder="e.g. Fresher / 1 year / 3 years", progress=75)

    if stage == "lead_experience":
        exp = message.strip()
        if len(exp) < 2:
            return _ui("Please share your experience level to continue.", placeholder="e.g. Fresher / 2 years", progress=75)
        data["experience"] = exp
        save_session(user_id, "lead_whatsapp", data)
        return _ui("What is your WhatsApp Number?", placeholder="10-digit WhatsApp number", progress=85)

    if stage == "lead_whatsapp":
        if not _valid_phone(message):
            return _ui("Please enter a valid 10-digit WhatsApp number.", placeholder="e.g. 9876543210", progress=85)
        data["whatsapp"] = _normalize_phone(message)
        save_session(user_id, "chat", data)

        response = _ui(
            "Thank you for sharing your details.\n\n"
            "Our program advisor will contact you shortly on **Phone or WhatsApp**.\n\n"
            "You can also join our **Free Demo Session** to understand the program in detail.",
            options=QUICK_ACTIONS,
            progress=100,
        )
        response["lead_payload"] = {
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "location": data.get("location", ""),
            "interested_domain": data.get("interested_domain", ""),
            "experience": data.get("experience", ""),
            "whatsapp": data.get("whatsapp", ""),
            "source": "chatbot",
        }
        return response

    save_session(user_id, "chat", data)
    return _start_message()
