import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Lead
from app.schemas import LeadCreate, LeadResponse

logger = logging.getLogger("coepd-api")
router = APIRouter(prefix="/api", tags=["leads"])


@router.post("/leads", response_model=LeadResponse, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(
        name=payload.name.strip(),
        phone=payload.phone.strip(),
        email=payload.email.strip().lower(),
        city=payload.city.strip() if payload.city else "",
        course=payload.course.strip() if payload.course else "",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/leads", response_model=list[LeadResponse])
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).order_by(Lead.created_at.desc()).all()
