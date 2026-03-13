import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Lead
from app.schemas import LeadCreate

logger = logging.getLogger("coepd-api")
router = APIRouter(prefix="/api", tags=["leads"])


@router.post("/leads", status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    try:
        normalized_source = (payload.source or "webpage").strip().lower()
        if normalized_source in ("website", "website_form"):
            normalized_source = "webpage"
        if normalized_source not in ("webpage", "chatbot"):
            normalized_source = "webpage"

        lead = Lead(
            name=payload.name.strip(),
            phone=payload.phone.strip(),
            email=payload.email.strip().lower(),
            location=payload.location.strip() if payload.location else "",
            interested_domain=payload.interested_domain.strip() if payload.interested_domain else "",
            whatsapp=payload.whatsapp.strip() if payload.whatsapp else "",
            source=normalized_source,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return {
            "success": True,
            "id": lead.id,
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email,
            "location": lead.location or "",
            "interested_domain": lead.interested_domain or "",
            "whatsapp": lead.whatsapp or "",
            "source": lead.source,
            "created_at": str(lead.created_at or ""),
        }
    except Exception as exc:
        logger.exception("POST /api/leads failed")
        return JSONResponse(status_code=500, content={"error": "Database error"})


@router.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
        return [
            {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "location": lead.location or "",
                "interested_domain": lead.interested_domain or "",
                "whatsapp": lead.whatsapp or "",
                "source": lead.source or "webpage",
                "created_at": str(lead.created_at or ""),
            }
            for lead in leads
        ]
    except Exception as exc:
        logger.exception("GET /api/leads failed")
        return JSONResponse(status_code=500, content={"error": "Database error"})
