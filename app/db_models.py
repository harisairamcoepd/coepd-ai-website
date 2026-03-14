from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.database import Base

try:
    IST = ZoneInfo("Asia/Kolkata")
except ZoneInfoNotFoundError:
    # tzdata package not installed on this system (common on minimal Windows installs).
    # Fall back to a fixed-offset IST timezone (UTC+5:30) for local development.
    IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_now() -> datetime:
    """Return the current time in IST (Asia/Kolkata)."""
    return datetime.now(IST)


def to_ist(dt: datetime | None) -> datetime | None:
    """Convert any datetime to IST. Returns None if input is None."""
    if dt is None:
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
    name = Column(Text)
    phone = Column(Text)
    email = Column(Text)
    location = Column(Text)
    interested_domain = Column(Text)
    whatsapp = Column(Text)
    source = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="staff")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=get_ist_now, server_default=func.now(), nullable=False)
