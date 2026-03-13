from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import cast, func, Date
from sqlalchemy.orm import Session

from app.database import SessionLocal, db_available
from app.db_models import Lead

IST = ZoneInfo("Asia/Kolkata")


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

    # Daily lead counts — use DB-appropriate date grouping
    # Use PostgreSQL date_trunc and timezone handling (SQLite removed)
    day_col = func.date_trunc("day", func.timezone("Asia/Kolkata", Lead.created_at)).label("day")

    rows = (
        db.query(day_col, func.count(Lead.id).label("count"))
        .filter(Lead.created_at >= month_start, Lead.created_at < next_month_start)
        .group_by("day")
        .order_by("day")
        .all()
    )

    counts_by_day: dict[str, int] = {}
    for row in rows:
        day_value = row.day
        if isinstance(day_value, datetime):
            day_key = day_value.date().isoformat()
        elif isinstance(day_value, date):
            day_key = day_value.isoformat()
        else:
            # SQLite returns "YYYY-MM-DD" string
            day_key = str(day_value)[:10]
        counts_by_day[day_key] = int(row.count or 0)

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
