from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth import AUTH_COOKIE_NAME, CSRF_COOKIE_NAME, decode_jwt_token


PUBLIC_PATH_PREFIXES = (
    "/",
    "/login",
    "/logout",
    "/health",
    "/static",
    "/favicon.ico",
    "/chat",
    "/lead",
    "/contact",
)

PUBLIC_EXACT_PATHS = {
    "/admin",
    "/admin/",
    "/staff",
    "/staff/",
}


class AuthAndSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None

        raw_token = request.cookies.get(AUTH_COOKIE_NAME, "")
        if raw_token:
            payload = decode_jwt_token(raw_token)
            if payload:
                try:
                    raw_sub = str(payload.get("sub", "") or "").strip()
                    user_id = int(raw_sub) if raw_sub.isdigit() else 0
                    request.state.user = {
                        "id": user_id,
                        "name": payload.get("name", ""),
                        "email": payload.get("email", ""),
                        "picture": payload.get("picture", ""),
                        "role": payload.get("role", "staff"),
                        "is_active": bool(payload.get("is_active", True)),
                    }
                except Exception:
                    request.state.user = None

        if request.state.user is None:
            try:
                session_user = str(request.session.get("user", "") or "").strip().lower()
                session_role = str(request.session.get("role", "") or "").strip().lower()
                if session_user and session_role in {"admin", "staff"}:
                    request.state.user = {
                        "id": int(request.session.get("user_id", 0) or 0),
                        "name": str(request.session.get("name", "") or session_user.split("@", 1)[0]),
                        "email": session_user,
                        "picture": "",
                        "role": session_role,
                        "is_active": True,
                    }
            except Exception:
                request.state.user = None

        if request.url.path in PUBLIC_EXACT_PATHS:
            return await call_next(request)

        if request.url.path in PUBLIC_PATH_PREFIXES or any(
            request.url.path.startswith(prefix + "/") for prefix in PUBLIC_PATH_PREFIXES
        ):
            return await call_next(request)

        path = request.url.path
        method = request.method.upper()

        if path.startswith("/admin") and request.state.user is None:
            if method == "GET":
                return RedirectResponse(url="/admin", status_code=302)
            accept = (request.headers.get("accept") or "").lower()
            if method == "GET" and "text/html" in accept:
                return RedirectResponse(url="/admin", status_code=302)
            return JSONResponse(status_code=401, content={"detail": "Authentication required"})

        if path.startswith("/admin") and request.state.user is not None:
            user_role = str(request.state.user.get("role", "staff")).strip().lower()
            if user_role != "admin":
                if method == "GET":
                    return RedirectResponse(url="/admin", status_code=302)
                return JSONResponse(status_code=403, content={"detail": "Admin access required"})

        if path == "/dashboard" and request.state.user is None:
            if method == "GET":
                return RedirectResponse(url="/staff", status_code=302)
            return JSONResponse(status_code=401, content={"detail": "Authentication required"})

        if path == "/dashboard" and request.state.user is not None:
            user_role = str(request.state.user.get("role", "staff")).strip().lower()
            if user_role != "staff":
                if method == "GET":
                    return RedirectResponse(url="/staff", status_code=302)
                return JSONResponse(status_code=403, content={"detail": "Staff access required"})

        needs_csrf = method in {"POST", "PUT", "PATCH", "DELETE"} and (
            path.startswith("/admin") or path == "/auth/logout"
        )
        if needs_csrf:
            csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME, "")
            csrf_header = request.headers.get("x-csrf-token", "")
            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

        response = await call_next(request)
        return response
