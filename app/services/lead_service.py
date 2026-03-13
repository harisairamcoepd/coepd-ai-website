import logging
from datetime import datetime, timezone

from sqlalchemy import func

from app.database import SessionLocal, db_available
from app.db_models import Lead, get_ist_now, to_ist, format_ist
from app.services.analytics_service import build_analytics_response_for_db

logger = logging.getLogger("coepd-api")


def create_lead(payload: dict) -> int:
    if not db_available():
        raise RuntimeError("Database not connected")
    db = SessionLocal()
    try:
        source = str(payload.get("source") or "webpage").strip().lower()
        if source in ("website", "website_form"):
            source = "webpage"
        if source not in ("webpage", "chatbot"):
            source = "webpage"

        lead = Lead(
            name=str(payload.get("name", "")).strip(),
            phone=str(payload.get("phone", "")).strip(),
            email=str(payload.get("email", "")).strip().lower(),
            location=str(payload.get("location") or payload.get("city") or "").strip(),
            interested_domain=str(payload.get("interested_domain") or payload.get("domain") or "").strip(),
            whatsapp=str(payload.get("whatsapp") or "").strip(),
            source=source,
            created_at=get_ist_now(),
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


def list_leads(
    date_prefix: str | None = None,
    source: str | None = None,
    search: str | None = None,
    interested_domain: str | None = None,
) -> list[dict]:
    db = SessionLocal()
    try:
        query = db.query(Lead)

        if source and source.lower() != "all":
            query = query.filter(func.lower(Lead.source) == source.lower())

        if interested_domain and interested_domain.lower() != "all":
            query = query.filter(func.lower(Lead.interested_domain) == interested_domain.lower())

        if search:
            like_val = f"%{search.lower()}%"
            query = query.filter(
                (func.lower(Lead.name).like(like_val))
                | (func.lower(Lead.email).like(like_val))
                | (func.lower(Lead.phone).like(like_val))
            )

        leads = query.order_by(Lead.created_at.desc()).limit(200).all()

        result = []
        for lead in leads:
            ist_dt = to_ist(lead.created_at)
            if ist_dt:
                date_display = ist_dt.strftime("%d %b %Y")
                time_display = ist_dt.strftime("%I:%M %p")
                datetime_display = f"{date_display} | {time_display}"
            else:
                date_display = time_display = datetime_display = ""

            result.append({
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "location": lead.location or "",
                "interested_domain": lead.interested_domain or "",
                "whatsapp": lead.whatsapp or "",
                "source": lead.source or "webpage",
                "created_at": format_ist(lead.created_at),
                "date_display": date_display,
                "time_display": time_display,
                "datetime_display": datetime_display,
            })
        return result
    finally:
        db.close()


def remove_lead(lead_id: int) -> bool:
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return False
        db.delete(lead)
        db.commit()
        return True
    finally:
        db.close()


def set_lead_status(lead_id: int, working_status: str) -> bool:
    return False


def fetch_dashboard_stats() -> dict:
    db = SessionLocal()
    try:
        analytics = build_analytics_response_for_db(db)
        return {
            "total_leads": analytics["total_leads"],
            "today_leads": analytics["today_leads"],
            "week_leads": analytics["week_leads"],
            "month_leads": analytics["month_leads"],
            "chatbot_leads": analytics["chatbot_leads"],
            "website_leads": analytics["website_leads"],
        }
    finally:
        db.close()


def list_dashboard_leads() -> list[dict]:
    return list_leads()


def list_dashboard_leads_paginated(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> dict:
    db = SessionLocal()
    try:
        query = db.query(Lead)
        if search:
            like_val = f"%{search.lower()}%"
            query = query.filter(
                (func.lower(Lead.name).like(like_val))
                | (func.lower(Lead.email).like(like_val))
                | (func.lower(Lead.phone).like(like_val))
            )

        total = query.count()
        leads = (
            query.order_by(Lead.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for lead in leads:
            ist_dt = to_ist(lead.created_at)
            datetime_display = ist_dt.strftime("%d %b %Y | %I:%M %p") if ist_dt else ""
            items.append({
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "location": lead.location or "",
                "interested_domain": lead.interested_domain or "",
                "whatsapp": lead.whatsapp or "",
                "source": lead.source or "webpage",
                "created_at": format_ist(lead.created_at),
                "datetime_display": datetime_display,
            })

        return {"items": items, "total": total, "page": page, "page_size": page_size}
    finally:
        db.close()
