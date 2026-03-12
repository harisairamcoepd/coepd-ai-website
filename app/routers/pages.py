from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import CSRF_COOKIE_NAME, create_csrf_token
from app.services.lead_service import list_dashboard_leads_paginated, list_leads
from chatbot.db import fetch_dashboard_stats


router = APIRouter()


def register_page_routes(templates: Jinja2Templates) -> APIRouter:
    @router.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    async def render_admin_dashboard(
        request: Request,
        date: str | None = None,
        source: str | None = None,
        search: str | None = None,
        interested_domain: str | None = None,
    ):
        current_user = getattr(request.state, "user", None)
        if not current_user:
            return RedirectResponse(url="/admin", status_code=302)
        if str(current_user.get("role", "")).strip().lower() != "admin":
            return RedirectResponse(url="/admin", status_code=302)

        try:
            stats = fetch_dashboard_stats()
        except Exception as e:
            print("Database error (stats):", e)
            stats = {"total_leads": 0, "today_leads": 0}

        try:
            leads = list_leads(date_prefix=date, source=source, search=search, interested_domain=interested_domain)
        except Exception as e:
            print("Database error (leads):", e)
            leads = []

        csrf_token = request.cookies.get(CSRF_COOKIE_NAME, "") or create_csrf_token()
        response = templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "leads": leads,
                "current_user": current_user,
                "csrf_token": csrf_token,
                "filter_date": date or "",
                "filter_source": source or "all",
                "filter_search": search or "",
                "filter_domain": interested_domain or "all",
                "total_leads": stats.get("total_leads", 0),
                "today_leads": stats.get("today_leads", 0),
                "chatbot_leads": stats.get("chatbot_leads", 0),
                "website_leads": stats.get("website_leads", 0),
            },
        )
        if not request.cookies.get(CSRF_COOKIE_NAME):
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=csrf_token,
                httponly=False,
                samesite="lax",
                path="/",
            )
        return response

    @router.get("/dashboard")
    async def staff_dashboard(
        request: Request,
        page: int = 1,
        search: str | None = None,
    ):
        current_user = getattr(request.state, "user", None)
        if not current_user:
            return RedirectResponse(url="/staff", status_code=302)
        if str(current_user.get("role", "")).strip().lower() != "staff":
            return RedirectResponse(url="/staff", status_code=302)

        try:
            leads_payload = list_dashboard_leads_paginated(page=page, page_size=20, search=search)
        except Exception as e:
            print("Database error:", e)
            leads_payload = {"items": [], "total": 0, "page": 1, "page_size": 20}

        try:
            stats = fetch_dashboard_stats()
        except Exception:
            stats = {"total_leads": 0, "chatbot_leads": 0, "website_leads": 0}

        total = int(leads_payload.get("total", 0) or 0)
        page_size = int(leads_payload.get("page_size", 20) or 20)
        safe_page = int(leads_payload.get("page", 1) or 1)
        total_pages = max(1, (total + page_size - 1) // page_size)
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "leads": leads_payload.get("items", []),
                "current_user": current_user,
                "user": current_user.get("email", ""),
                "search": search or "",
                "page": safe_page,
                "total_pages": total_pages,
                "total_leads": stats.get("total_leads", 0),
                "chatbot_leads": stats.get("chatbot_leads", 0),
                "website_leads": stats.get("website_leads", 0),
            },
        )

    @router.get("/admin/staff", response_class=HTMLResponse)
    async def admin_staff_page(
        request: Request,
        date: str | None = None,
        source: str | None = None,
        search: str | None = None,
        interested_domain: str | None = None,
    ):
        return await render_admin_dashboard(request, date=date, source=source, search=search, interested_domain=interested_domain)

    @router.get("/admin/dashboard", response_class=HTMLResponse)
    async def admin_page(
        request: Request,
        date: str | None = None,
        source: str | None = None,
        search: str | None = None,
        interested_domain: str | None = None,
    ):
        return await render_admin_dashboard(request, date=date, source=source, search=search, interested_domain=interested_domain)

    @router.get("/health")
    async def health(request: Request):
        startup_status = getattr(request.app.state, "startup_status", {})
        database_status = startup_status.get("database", "connected")
        auth_status = startup_status.get("auth", "enabled")
        return {
            "status": "running",
            "database": database_status,
            "auth": auth_status,
        }

    return router
