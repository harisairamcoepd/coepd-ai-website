import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import FileResponse

from app.auth import require_roles
from app.models import LeadStatusPayload, StaffCreatePayload, StaffPasswordUpdatePayload
from app.services.analytics_service import build_analytics_response
from app.services.lead_service import list_leads, remove_lead, set_lead_status
from chatbot.db import (
    create_staff_user,
    delete_staff_user,
    export_leads_to_csv,
    list_staff_users,
    set_staff_role,
    set_staff_status,
    update_staff_password,
)


logger = logging.getLogger("coepd-api")
router = APIRouter()


@router.get("/admin/settings")
async def admin_settings(_user: dict = Depends(require_roles("admin"))):
    return {"ok": True, "settings": {"role": "admin"}}


@router.get("/admin/leads")
async def admin_leads(
    date: str | None = None,
    source: str | None = None,
    search: str | None = None,
    interested_domain: str | None = None,
    _user: dict = Depends(require_roles("admin", "staff")),
):
    try:
        return {"leads": list_leads(date_prefix=date, source=source, search=search, interested_domain=interested_domain)}
    except Exception as exc:
        logger.exception("/admin/leads failed")
        raise HTTPException(status_code=500, detail="Unable to fetch leads") from exc


@router.get("/staff/leads")
async def staff_leads(
    date: str | None = None,
    source: str | None = None,
    search: str | None = None,
    interested_domain: str | None = None,
    _user: dict = Depends(require_roles("admin", "staff")),
):
    """Alias for /admin/leads — accessible to staff panel."""
    return await admin_leads(date=date, source=source, search=search, interested_domain=interested_domain, _user=_user)


@router.delete("/admin/leads/{lead_id}")
async def delete_admin_lead(lead_id: int, _user: dict = Depends(require_roles("admin"))):
    try:
        if not remove_lead(lead_id):
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("/admin/leads delete failed")
        raise HTTPException(status_code=500, detail="Unable to delete lead") from exc


@router.patch("/admin/leads/{lead_id}/status")
async def update_admin_lead_status(
    lead_id: int,
    payload: LeadStatusPayload,
    _user: dict = Depends(require_roles("admin", "staff")),
):
    try:
        if not set_lead_status(lead_id=lead_id, working_status=payload.working_status):
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("/admin/leads status update failed")
        raise HTTPException(status_code=500, detail="Unable to update lead status") from exc


@router.get("/admin/export")
async def export_csv(_user: dict = Depends(require_roles("admin"))):
    path = export_leads_to_csv("leads_export.csv")
    return FileResponse(path=path, media_type="text/csv", filename="leads_export.csv")


@router.get("/admin/analytics")
async def admin_analytics(_user: dict = Depends(require_roles("admin"))):
    try:
        return build_analytics_response()
    except Exception as exc:
        logger.exception("/admin/analytics failed")
        raise HTTPException(status_code=500, detail="Unable to build analytics") from exc


@router.get("/analytics")
async def analytics_compat(_user: dict = Depends(require_roles("admin"))):
    try:
        return build_analytics_response()
    except Exception as exc:
        logger.exception("/analytics failed")
        raise HTTPException(status_code=500, detail="Unable to build analytics") from exc


@router.get("/admin/users")
async def admin_users_compat(_user: dict = Depends(require_roles("admin"))):
    return {"users": list_staff_users()}


@router.post("/admin/users")
async def create_admin_user_compat(payload: StaffCreatePayload, _user: dict = Depends(require_roles("admin"))):
    try:
        user_id = create_staff_user(name=payload.name, email=payload.email, password=payload.password, role=payload.role)
        return {"ok": True, "id": user_id}
    except Exception as exc:
        logger.exception("/admin/users create failed")
        raise HTTPException(status_code=400, detail=f"Unable to create user: {exc}") from exc


@router.delete("/admin/users/{user_id}")
async def delete_admin_user_compat(user_id: int, _user: dict = Depends(require_roles("admin"))):
    if not delete_staff_user(user_id):
        raise HTTPException(status_code=400, detail="Unable to delete user")
    return {"ok": True}


@router.get("/admin/staff/list")
async def list_staff_accounts(_user: dict = Depends(require_roles("admin"))):
    try:
        return {"success": True, "staff": list_staff_users()}
    except Exception as exc:
        logger.exception("/admin/staff/list failed")
        return {"success": False, "error": f"Unable to list staff users: {exc}"}


@router.post("/admin/staff/create")
async def create_staff_account(payload: StaffCreatePayload, _user: dict = Depends(require_roles("admin"))):
    try:
        staff_id = create_staff_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role="staff",
            status="inactive",
        )
        return {"success": True, "id": staff_id}
    except Exception as exc:
        logger.exception("/admin/staff/create failed")
        return {"success": False, "error": f"Unable to create staff: {exc}"}


@router.put("/admin/staff/activate/{staff_id}")
async def activate_staff_account(staff_id: int, _user: dict = Depends(require_roles("admin"))):
    try:
        if not set_staff_status(staff_id, "active"):
            return {"success": False, "error": "Staff user not found"}
        return {"success": True}
    except Exception as exc:
        logger.exception("/admin/staff/activate failed")
        return {"success": False, "error": f"Unable to activate staff: {exc}"}


@router.put("/admin/staff/deactivate/{staff_id}")
async def deactivate_staff_account(staff_id: int, _user: dict = Depends(require_roles("admin"))):
    try:
        if not set_staff_status(staff_id, "inactive"):
            return {"success": False, "error": "Staff user not found"}
        return {"success": True}
    except Exception as exc:
        logger.exception("/admin/staff/deactivate failed")
        return {"success": False, "error": f"Unable to deactivate staff: {exc}"}


@router.put("/admin/staff/set-role/{staff_id}")
async def set_staff_account_role(
    staff_id: int,
    payload: dict = Body(...),
    _user: dict = Depends(require_roles("admin")),
):
    role = str(payload.get("role", "")).strip().lower()
    if role not in {"admin", "staff"}:
        return {"success": False, "error": "Role must be 'admin' or 'staff'"}
    try:
        if not set_staff_role(staff_id, role):
            return {"success": False, "error": "Staff user not found"}
        return {"success": True}
    except Exception as exc:
        logger.exception("/admin/staff/set-role failed")
        return {"success": False, "error": f"Unable to update role: {exc}"}


@router.put("/admin/staff/update-password/{staff_id}")
async def reset_staff_password(
    staff_id: int,
    payload: StaffPasswordUpdatePayload,
    _user: dict = Depends(require_roles("admin")),
):
    try:
        if not update_staff_password(staff_id, payload.password):
            return {"success": False, "error": "Staff user not found"}
        return {"success": True}
    except Exception as exc:
        logger.exception("/admin/staff/update-password failed")
        return {"success": False, "error": f"Unable to update password: {exc}"}


@router.delete("/admin/staff/delete/{staff_id}")
async def remove_staff_account(staff_id: int, _user: dict = Depends(require_roles("admin"))):
    try:
        if not delete_staff_user(staff_id):
            return {"success": False, "error": "Staff user not found"}
        return {"success": True}
    except Exception as exc:
        logger.exception("/admin/staff/delete failed")
        return {"success": False, "error": f"Unable to delete staff user: {exc}"}
