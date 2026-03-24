from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import (
    AUTH_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    AUTH_COOKIE_SECURE,
    authenticate_user,
    create_token,
    decode_token,
)


router = APIRouter()


def _api_login_response(user: dict) -> JSONResponse:
    role = str(user.get("role", "staff")).strip().lower()
    email = str(user.get("email", "")).strip().lower()

    token = create_token(
        email,
        role,
        user_id=int(user.get("id", 0) or 0),
        name=str(user.get("name", "")),
    )

    response = JSONResponse({"success": True, "role": role})
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
        max_age=60 * 60 * 2,
        path="/",
    )
    return response


def register_auth_routes(templates: Jinja2Templates) -> APIRouter:

    # â”€â”€ STEP 3: Staff login GET â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @router.get("/staff", response_class=HTMLResponse)
    async def staff_login_page(request: Request):
        user = getattr(request.state, "user", None)
        if user:
            role = str(user.get("role", "staff")).strip().lower()
            if role == "staff":
                return RedirectResponse(url="/dashboard", status_code=302)
        return templates.TemplateResponse(
            request,
            "staff_login.html",
            {"request": request, "error": ""},
        )

    # â”€â”€ STEP 4: Admin login GET â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @router.get("/admin", response_class=HTMLResponse)
    async def admin_login_page(request: Request):
        user = getattr(request.state, "user", None)
        if user:
            role = str(user.get("role", "staff")).strip().lower()
            if role == "admin":
                return RedirectResponse(url="/admin/dashboard", status_code=302)
        return templates.TemplateResponse(
            request,
            "admin_login.html",
            {"request": request, "error": ""},
        )

    @router.get("/login", response_class=HTMLResponse)
    async def login_redirect(request: Request):
        return RedirectResponse(url="/staff", status_code=302)

    # â”€â”€ Staff login POST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @router.post("/staff", response_class=HTMLResponse)
    async def staff_login_submit(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
    ):
        return await _handle_login(
            templates, request, email, password,
            expected_role="staff",
            template_name="staff_login.html",
        )

    # â”€â”€ Admin login POST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @router.post("/admin", response_class=HTMLResponse)
    async def admin_login_submit(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
    ):
        return await _handle_login(
            templates, request, email, password,
            expected_role="admin",
            template_name="admin_login.html",
        )

    @router.post("/login", response_class=HTMLResponse)
    async def login_submit_backcompat(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
    ):
        return await _handle_login(
            templates, request, email, password,
            expected_role="staff",
            template_name="staff_login.html",
        )

    # â”€â”€ STEP 6: Logout â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @router.get("/logout")
    async def logout_get(request: Request):
        try:
            request.session.clear()
        except Exception:
            pass
        response = RedirectResponse(url="/", status_code=302)
        response.delete_cookie(AUTH_COOKIE_NAME, path="/")
        response.delete_cookie(CSRF_COOKIE_NAME, path="/")
        return response

    @router.post("/auth/logout")
    async def logout_post(request: Request):
        try:
            request.session.clear()
        except Exception:
            pass
        response = RedirectResponse(url="/", status_code=302)
        response.delete_cookie(AUTH_COOKIE_NAME, path="/")
        response.delete_cookie(CSRF_COOKIE_NAME, path="/")
        return response

    @router.post("/api/login")
    async def api_login(request: Request):
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        user = authenticate_user(email, password)
        if not user:
            return {"error": "Invalid email or password"}
        return _api_login_response(user)

    @router.post("/api/admin/login")
    async def api_admin_login(request: Request):
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        user = authenticate_user(email, password)
        if not user:
            return {"error": "Invalid email or password"}
        
        if user["role"] != "admin":
            return {"error": "Invalid email or password"}
        return _api_login_response(user)

    @router.post("/api/staff/login")
    async def api_staff_login(request: Request):
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        user = authenticate_user(email, password)
        if not user:
            return {"error": "Invalid email or password"}
        return _api_login_response(user)

    @router.get("/auth/me")
    async def auth_me(request: Request):
        raw_token = request.cookies.get(AUTH_COOKIE_NAME, "")
        payload = decode_token(raw_token) if raw_token else None
        return {"user": payload}

    return router


# â”€â”€ Shared login handler (STEP 8: error handling included) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _handle_login(
    templates: Jinja2Templates,
    request: Request,
    email: str,
    password: str,
    *,
    expected_role: str,
    template_name: str,
):
    normalized_email = (email or "").strip().lower()

    try:
        user = authenticate_user(normalized_email, password)
    except Exception as e:
        print("Database error during login:", e)
        user = None

    if not user:
        return templates.TemplateResponse(
            request,
            template_name,
            {"request": request, "error": "Invalid email or password"},
            status_code=401,
        )

    role = str(user.get("role", "staff")).strip().lower()
    if role != expected_role:
        portal_name = "Admin" if expected_role == "admin" else "Staff"
        return templates.TemplateResponse(
            request,
            template_name,
            {"request": request, "error": f"This account cannot sign in to {portal_name} portal."},
            status_code=403,
        )

    token = create_token(
        normalized_email,
        role,
        user_id=int(user.get("id", 0) or 0),
        name=str(user.get("name", "")),
    )

    redirect_url = "/admin/dashboard" if role == "admin" else "/dashboard"
    response = RedirectResponse(url=redirect_url, status_code=302)

    try:
        request.session["user"] = normalized_email
        request.session["role"] = role
        request.session["user_id"] = int(user.get("id", 0) or 0)
        request.session["name"] = str(user.get("name", "") or normalized_email.split("@", 1)[0])
    except Exception:
        pass

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite="lax",
        max_age=60 * 60 * 2,
        path="/",
    )
    return response
