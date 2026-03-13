import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import bcrypt
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import func

from app.database import SessionLocal, db_available
from app.db_models import Staff

logger = logging.getLogger("coepd-api.auth")

AUTH_COOKIE_NAME = "auth_token"
CSRF_COOKIE_NAME = "coepd_csrf"


JWT_SECRET = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET") or "change-this-in-production"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "2"))
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").strip().lower() == "true"

ADMIN_LOGIN_EMAIL = os.getenv("ADMIN_LOGIN_EMAIL", "admin").strip().lower()
ADMIN_LOGIN_PASSWORD = os.getenv("ADMIN_LOGIN_PASSWORD", "admin")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
def create_token(email: str, role: str, user_id: int | None = None, name: str | None = None) -> str:
    now = utc_now()
    payload = {
        "sub": str(user_id) if user_id is not None else str(email).lower(),
        "name": (name or str(email).split("@", 1)[0]),
        "email": str(email).lower(),
        "picture": "",
        "role": str(role).lower(),
        "is_active": True,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRE_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def create_jwt_token(user: dict[str, Any]) -> str:
    return create_token(
        str(user.get("email", "")).strip().lower(),
        str(user.get("role", "staff")).strip().lower(),
        user_id=int(user.get("id", 0) or 0),
        name=str(user.get("name", "")),
    )


def decode_jwt_token(token: str) -> dict[str, Any] | None:
    return decode_token(token)


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def get_current_user(request: Request) -> dict[str, Any]:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not bool(user.get("is_active", True)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def get_current_admin(request: Request) -> dict[str, Any]:
    user = get_current_user(request)
    role = str(user.get("role", "")).strip().lower()
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_roles(*roles: str) -> Callable[[Request], dict[str, Any]]:
    normalized_roles = {r.strip().lower() for r in roles if r}

    def _checker(request: Request) -> dict[str, Any]:
        user = get_current_user(request)
        user_role = str(user.get("role", "")).strip().lower()
        if normalized_roles and user_role not in normalized_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _checker


def validate_auth_dependencies() -> None:
    return None


def validate_auth_configuration() -> list[str]:
    missing_env: list[str] = []
    for env_name in ("JWT_SECRET_KEY",):
        if not (os.getenv(env_name) or "").strip():
            missing_env.append(env_name)

    if missing_env:
        unique_missing = sorted(set(missing_env))
        return [
            "Missing environment variables detected: "
            + ", ".join(unique_missing)
            + ". App will run, but auth security may be limited until configured."
        ]

    return []


def validate_admin_credentials(email: str, password: str) -> bool:
    user = authenticate_user(email=email, password=password)
    return bool(user and user.get("role") == "admin")


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        logger.warning("Login attempt with empty email")
        return None

    if not db_available():
        logger.error("Cannot authenticate: database engine not initialized")
        return None

    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(func.lower(Staff.email) == normalized_email).first()
        if not staff:
            logger.warning("Login failed: no user found with email '%s'", normalized_email)
            return None

        if not bcrypt.checkpw((password or "").encode("utf-8"), staff.password_hash.encode("utf-8")):
            logger.warning("Login failed: invalid password for email '%s'", normalized_email)
            return None

        if str(staff.status or "active").strip().lower() != "active":
            logger.warning("Login failed: user '%s' is inactive", normalized_email)
            return None

        logger.info("Login successful for '%s' (role=%s)", normalized_email, staff.role)
        return {
            "id": staff.id,
            "name": staff.name or normalized_email.split("@", 1)[0],
            "email": normalized_email,
            "role": str(staff.role or "staff").strip().lower(),
            "is_active": True,
        }
    except Exception as exc:
        logger.exception("Database error during authentication for '%s': %s", normalized_email, exc)
        return None
    finally:
        db.close()
