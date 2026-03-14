import logging
import os
from importlib.util import find_spec

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
try:
    from starlette.middleware.sessions import SessionMiddleware
except Exception:
    SessionMiddleware = None

from app.config import PREFERRED_STATIC_DIR, STATIC_DIR, TEMPLATES_DIR
from app.auth import AUTH_COOKIE_SECURE, validate_auth_configuration, validate_auth_dependencies
from app.middleware.auth_middleware import AuthAndSecurityMiddleware
from app.middleware.rate_limit import RateLimiter

# Defer router and chatbot imports to avoid import-time circular dependencies.



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("coepd-api")


def _validate_runtime_dependencies() -> None:
    required_modules = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "pydantic": "pydantic",
        "jinja2": "jinja2",
        "jose": "python-jose",
        "bcrypt": "bcrypt",
        "multipart": "python-multipart",
        "dotenv": "python-dotenv",
    }

    missing = [f"{pkg} (import: {mod})" for mod, pkg in required_modules.items() if find_spec(mod) is None]
    if missing:
        logger.warning(
            "Dependency warning: Missing Python dependencies: %s. Install with: pip install -r requirements.txt",
            ", ".join(missing),
        )


def _run_startup_checks() -> list[str]:
    _validate_runtime_dependencies()
    warnings: list[str] = []

    try:
        validate_auth_dependencies()
    except Exception as exc:
        warnings.append(f"Authentication dependency warning: {exc}")

    warnings.extend(validate_auth_configuration())
    return warnings


def create_app() -> FastAPI:
    print("Starting FastAPI application...")
    logger.info("Starting FastAPI application...")

    app = FastAPI(title="COEPD AI Website", version="2.0.0")

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError):
        logger.error("RuntimeError: %s", exc)
        return JSONResponse(status_code=503, content={"error": str(exc)})

    app.state.startup_status = {
        "database": "disconnected",
        "auth": "enabled",
    }

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    if not PREFERRED_STATIC_DIR.exists():
        logger.warning("Preferred static directory not found at %s; using %s", PREFERRED_STATIC_DIR, STATIC_DIR)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), check_dir=False), name="static")
    app.mount("/chatbot", StaticFiles(directory=str(STATIC_DIR / "chatbot"), check_dir=False), name="chatbot")

    if SessionMiddleware is not None:
        app.add_middleware(
            SessionMiddleware,
            secret_key=os.getenv("SESSION_SECRET_KEY", "coepd-super-secret-key"),
            same_site="lax",
            https_only=AUTH_COOKIE_SECURE,
        )
    else:
        logger.warning("SessionMiddleware not available; sessions disabled. Install 'itsdangerous' to enable.")

    app.add_middleware(AuthAndSecurityMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(RateLimiter(limit_per_minute=90))

    # ── Startup checks ──────────────────────────────────────────────────
    _run_startup_checks()

    # ── Initialise chatbot SQLite DB (deferred import) ───────────────────
    try:
        from chatbot.db import init_db as _init_db
        _init_db()
        logger.info("Chatbot SQLite database initialized")
    except Exception as exc:
        logger.warning("Chatbot DB init skipped: %s", exc)

    # ── Initialise Supabase PostgreSQL ───────────────────────────────────
    try:
        from app.database import create_tables, SessionLocal
        from app.db_models import Staff

        create_tables()
        app.state.startup_status["database"] = "connected"
        logger.info("PostgreSQL tables created")

        # Seed default admin user
        import bcrypt
        from sqlalchemy import func as sa_func
        admin_email = (os.getenv("ADMIN_LOGIN_EMAIL") or "admin").strip().lower()
        admin_password = (os.getenv("ADMIN_LOGIN_PASSWORD") or "admin").strip()
        db = SessionLocal()
        try:
            existing = db.query(Staff).filter(sa_func.lower(Staff.email) == admin_email).first()
            if not existing:
                pw_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                db.add(Staff(name="Admin", email=admin_email, password_hash=pw_hash, role="admin", status="active"))
                db.commit()
                logger.info("Default admin user seeded (email=%s)", admin_email)
            else:
                logger.info("Admin user already exists (email=%s)", admin_email)
        finally:
            db.close()

        from app.db_models import Lead
        db = SessionLocal()
        try:
            lead_count = db.query(sa_func.count(Lead.id)).scalar() or 0
            logger.info("Startup check: database connected, %d leads in table", lead_count)
        finally:
            db.close()

        print("Database connected")

    except Exception as exc:
        app.state.startup_status["database"] = "disconnected"
        logger.warning("PostgreSQL init failed: %s", exc)

    logger.info("Authentication enabled")
    logger.info("Application startup complete")

    # ── Include routers (deferred imports to avoid circular import issues) ─
    try:
        from app.routers.pages import register_page_routes as _rpr
        from app.routers.auth import register_auth_routes as _rar
        from app.routers.chat import router as _chat_router
        from app.routers.admin import router as _admin_router
        from app.routers.leads import router as _leads_router

        app.include_router(_rpr(templates))
        app.include_router(_rar(templates))
        app.include_router(_chat_router)
        app.include_router(_admin_router)
        app.include_router(_leads_router)
    except Exception as exc:
        logger.warning("Failed to include some routers: %s", exc)

    return app
