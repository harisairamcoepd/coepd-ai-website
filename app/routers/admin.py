import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import bcrypt
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_admin
from app.database import get_db
from app.db_models import Lead, Staff, IST, to_ist, format_ist
from app.services.analytics_service import build_analytics_response_for_db

logger = logging.getLogger("coepd-api")
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


def _err(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


DB_UNAVAILABLE = "Database connection unavailable"


# ── Settings ─────────────────────────────────────────────────────────────


@router.get("/settings")
async def admin_settings():
    return {"ok": True, "settings": {"role": "admin"}}


# ── Leads CRUD ───────────────────────────────────────────────────────────


@router.get("/leads")
async def get_admin_leads(
    date: str | None = None,
    source: str | None = None,
    search: str | None = None,
    interested_domain: str | None = None,
    db: Session = Depends(get_db),
):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        query = db.query(Lead)

        if date:
            try:
                filter_date = datetime.strptime(date, "%Y-%m-%d").date()
                day_start = datetime.combine(filter_date, datetime.min.time(), tzinfo=IST)
                day_end = day_start + timedelta(days=1)
                query = query.filter(Lead.created_at >= day_start, Lead.created_at < day_end)
            except ValueError:
                return _err("Invalid date format. Use YYYY-MM-DD.", 400)

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
                | (func.lower(Lead.location).like(like_val))
                | (func.lower(Lead.interested_domain).like(like_val))
            )

        leads = query.order_by(Lead.created_at.desc()).all()

        result = []
        for lead in leads:
            ist_dt = to_ist(lead.created_at)
            if ist_dt:
                date_display = ist_dt.strftime("%d %b %Y")
                time_display = ist_dt.strftime("%I:%M %p")
                datetime_display = f"{date_display} | {time_display}"
            else:
                date_display = time_display = datetime_display = "Unknown"

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

        return {"leads": result}
    except Exception as exc:
        logger.exception("GET /api/admin/leads failed")
        return _err(str(exc), 500)


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return _err("Lead not found", 404)
        db.delete(lead)
        db.commit()
        return {"success": True}
    except Exception as exc:
        logger.exception("DELETE /api/admin/leads/%s failed", lead_id)
        return _err(str(exc), 500)


# ── Stats ────────────────────────────────────────────────────────────────


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
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
    except Exception as exc:
        logger.exception("GET /api/admin/stats failed")
        return _err(str(exc), 500)


@router.get("/lead-growth")
async def get_lead_growth(db: Session = Depends(get_db)):
    """Return current-month day-by-day lead counts for charting."""
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        analytics = build_analytics_response_for_db(db)
        return {
            "daily_leads": analytics["daily_leads"],
            "labels": analytics["labels"],
            "data": analytics["data"],
        }
    except Exception as exc:
        logger.exception("GET /api/admin/lead-growth failed")
        return _err(str(exc), 500)


@router.get("/source-breakdown")
async def get_source_breakdown(db: Session = Depends(get_db)):
    """Return lead counts grouped by source for the doughnut chart."""
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        rows = (
            db.query(Lead.source, func.count(Lead.id))
            .group_by(Lead.source)
            .all()
        )
        result = {}
        for source, count in rows:
            key = (source or "webpage").strip().lower()
            result[key] = result.get(key, 0) + count
        return result
    except Exception as exc:
        logger.exception("GET /api/admin/source-breakdown failed")
        return _err(str(exc), 500)


# ── Staff management ─────────────────────────────────────────────────────


@router.get("/staff")
async def list_staff(db: Session = Depends(get_db)):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        users = db.query(Staff).order_by(Staff.created_at.desc()).all()
        return {
            "staff": [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "role": u.role,
                    "status": u.status,
                    "created_at": format_ist(u.created_at),
                }
                for u in users
            ]
        }
    except Exception as exc:
        logger.exception("GET /api/admin/staff failed")
        return _err(str(exc), 500)


@router.post("/staff")
async def create_staff(payload: dict, db: Session = Depends(get_db)):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        password = str(payload.get("password", "")).strip()
        role = str(payload.get("role", "staff")).strip().lower()

        if not name or not email or len(password) < 6:
            return _err("Name, email and password (min 6 chars) are required", 400)

        existing = db.query(Staff).filter(func.lower(Staff.email) == email).first()
        if existing:
            return _err("A staff user with this email already exists", 400)

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        staff = Staff(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role if role in ("admin", "staff") else "staff",
            status="active",
        )
        db.add(staff)
        db.commit()
        db.refresh(staff)
        return {"success": True, "id": staff.id}
    except Exception as exc:
        logger.exception("POST /api/admin/staff failed")
        return _err(str(exc), 500)


@router.post("/create-staff")
async def create_staff_compat(payload: dict, db: Session = Depends(get_db)):
    """Backward-compatible alias for POST /api/admin/staff."""
    return await create_staff(payload, db)


@router.put("/staff/activate/{user_id}")
async def activate_staff(user_id: int, db: Session = Depends(get_db)):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        user = db.query(Staff).filter(Staff.id == user_id).first()
        if not user:
            return _err("User not found", 404)
        user.status = "active"
        db.commit()
        return {"success": True}
    except Exception as exc:
        logger.exception("POST /api/admin/staff/activate/%s failed", user_id)
        return _err(str(exc), 500)


@router.put("/staff/deactivate/{user_id}")
async def deactivate_staff(user_id: int, db: Session = Depends(get_db)):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        user = db.query(Staff).filter(Staff.id == user_id).first()
        if not user:
            return _err("User not found", 404)
        user.status = "inactive"
        db.commit()
        return {"success": True}
    except Exception as exc:
        logger.exception("POST /api/admin/staff/deactivate/%s failed", user_id)
        return _err(str(exc), 500)


@router.put("/staff/set-role/{user_id}")
async def set_staff_role(user_id: int, payload: dict, db: Session = Depends(get_db)):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        new_role = str(payload.get("role", "")).strip().lower()
        if new_role not in ("admin", "staff"):
            return _err("Role must be 'admin' or 'staff'", 400)
        user = db.query(Staff).filter(Staff.id == user_id).first()
        if not user:
            return _err("User not found", 404)
        user.role = new_role
        db.commit()
        return {"success": True}
    except Exception as exc:
        logger.exception("POST /api/admin/staff/set-role/%s failed", user_id)
        return _err(str(exc), 500)


@router.delete("/staff/{user_id}")
async def delete_staff(user_id: int, db: Session = Depends(get_db)):
    if db is None:
        return _err(DB_UNAVAILABLE, 503)
    try:
        user = db.query(Staff).filter(Staff.id == user_id).first()
        if not user:
            return _err("User not found", 404)
        db.delete(user)
        db.commit()
        return {"success": True}
    except Exception as exc:
        logger.exception("DELETE /api/admin/staff/%s failed", user_id)
        return _err(str(exc), 500)
