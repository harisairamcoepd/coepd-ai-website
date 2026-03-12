from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(120), nullable=False, index=True)
    city = Column(String(120), nullable=True)
    course = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
