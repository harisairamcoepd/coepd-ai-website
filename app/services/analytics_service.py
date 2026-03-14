from datetime import date, datetime, time, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))

import os
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal, db_available
from app.db_models import Lead


def _start_of_day_ist(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=IST)


def _empty_response() -> dict:
    return {
        "total_leads": 0,
        "today_leads": 0,
        "week_leads": 0,
        "month_leads": 0,
        "chatbot_leads": 0,
        "website_leads": 0,
        "daily_leads": [],
        "labels": [],
        "data": [],
    }


def build_analytics_response_for_db(db: Session, *, now_ist: datetime | None = None) -> dict:
    now = now_ist or datetime.now(IST)
    today = now.date()
    today_start = _start_of_day_ist(today)
    tomorrow_start = today_start + timedelta(days=1)

    month_start_day = today.replace(day=1)
    month_start = _start_of_day_ist(month_start_day)
    if month_start_day.month == 12:
        next_month_start = _start_of_day_ist(date(month_start_day.year + 1, 1, 1))
    else:
        next_month_start = _start_of_day_ist(date(month_start_day.year, month_start_day.month + 1, 1))

    week_start = today_start - timedelta(days=6)

    total_leads = int(db.query(func.count(Lead.id)).scalar() or 0)
    today_leads = int(
        db.query(func.count(Lead.id))
        .filter(Lead.created_at >= today_start, Lead.created_at < tomorrow_start)
        .scalar()
        or 0
    )
    week_leads = int(
        db.query(func.count(Lead.id))
        .filter(Lead.created_at >= week_start, Lead.created_at < tomorrow_start)
        .scalar()
        or 0
    )
    month_leads = int(
        db.query(func.count(Lead.id))
        .filter(Lead.created_at >= month_start, Lead.created_at < next_month_start)
        .scalar()
        or 0
    )
    chatbot_leads = int(
        db.query(func.count(Lead.id))
        .filter(func.lower(Lead.source) == "chatbot")
        .scalar()
        or 0
    )
    website_leads = max(total_leads - chatbot_leads, 0)

    # Build daily counts by issuing a small per-day count using UTC boundaries.
    counts_by_day: dict[str, int] = {}
    cursor_ist = month_start_day
    while cursor_ist <= today:
        day_start_ist = _start_of_day_ist(cursor_ist)
        day_end_ist = day_start_ist + timedelta(days=1)
        day_start_utc = day_start_ist.astimezone(timezone.utc)
        day_end_utc = day_end_ist.astimezone(timezone.utc)
        cnt = int(
            db.query(func.count(Lead.id))
            .filter(Lead.created_at >= day_start_utc, Lead.created_at < day_end_utc)
            .scalar()
            or 0
        )
        counts_by_day[cursor_ist.isoformat()] = cnt
        cursor_ist = cursor_ist + timedelta(days=1)

    daily_leads: list[dict[str, int | str]] = []
    cursor = month_start_day
    while cursor <= today:
        day_key = cursor.isoformat()
        daily_leads.append({"date": day_key, "count": int(counts_by_day.get(day_key, 0))})
        cursor = cursor + timedelta(days=1)

    return {
        "total_leads": total_leads,
        "today_leads": today_leads,
        "week_leads": week_leads,
        "month_leads": month_leads,
        "chatbot_leads": chatbot_leads,
        "website_leads": website_leads,
        "daily_leads": daily_leads,
        "labels": [item["date"] for item in daily_leads],
        "data": [item["count"] for item in daily_leads],
    }


def build_analytics_response() -> dict:
    if not db_available():
        return _empty_response()

    db = SessionLocal()
    try:
        return build_analytics_response_for_db(db)
    except Exception:
        return _empty_response()
    finally:
        db.close()
