from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import Column, DateTime, Integer, String, func

from app.database import Base

try:
    IST = ZoneInfo("Asia/Kolkata")
except ZoneInfoNotFoundError:
    # tzdata package not installed on this system (common on minimal Windows installs).
    # Fall back to a fixed-offset IST timezone (UTC+5:30) for local development.
    IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_now() -> datetime:
    """Return current UTC time as naive datetime for DB storage compatibility."""
    return datetime.utcnow()


def to_ist(dt: datetime | None) -> datetime | None:
    """Convert any datetime to IST. Returns None if input is None."""
    if dt is None:
        return None
    if isinstance(dt, str):
        raw = dt.strip()
        if not raw:
            return None
        try:
            # Support ISO8601 strings, including trailing 'Z'.
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
        dt = parsed
    elif not isinstance(dt, datetime):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def format_ist(dt: datetime | None) -> str:
    """Format a datetime as '2026-03-13 16:45:22 IST'. Empty string if None."""
    ist_dt = to_ist(dt)
    if ist_dt is None:
        return ""
    return ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")



class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    location = Column(String(255))
    interested_domain = Column(String(255))
    whatsapp = Column(String(50))
    source = Column(String(50))
    created_at = Column(DateTime(timezone=False), server_default=func.now())


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="staff")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=False), default=get_ist_now, server_default=func.now(), nullable=False)
