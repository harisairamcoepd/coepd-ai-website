import logging
import os
from importlib.util import find_spec

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import PREFERRED_STATIC_DIR, STATIC_DIR, TEMPLATES_DIR
from app.auth import AUTH_COOKIE_SECURE, validate_auth_configuration, validate_auth_dependencies
from app.middleware.auth_middleware import AuthAndSecurityMiddleware
from app.middleware.rate_limit import RateLimiter
from app.routers.admin import router as admin_router
from app.routers.auth import register_auth_routes
from app.routers.chat import router as chat_router
from app.routers.pages import register_page_routes
from chatbot.db import init_db, seed_default_admin_user


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
    app.state.startup_status = {
        "database": "disconnected",
        "auth": "enabled",
    }

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    if not PREFERRED_STATIC_DIR.exists():
        logger.warning("Preferred static directory not found at %s; using %s", PREFERRED_STATIC_DIR, STATIC_DIR)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), check_dir=False), name="static")
    app.mount("/chatbot", StaticFiles(directory=str(STATIC_DIR / "chatbot"), check_dir=False), name="chatbot")

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET_KEY", "coepd-super-secret-key"),
        same_site="lax",
        https_only=AUTH_COOKIE_SECURE,
    )

    app.add_middleware(AuthAndSecurityMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(RateLimiter(limit_per_minute=90))

    # Eagerly initialise the database so it works on Vercel serverless
    # where the ASGI "startup" lifespan event may never fire.
    _run_startup_checks()
    try:
        init_db()
        app.state.startup_status["database"] = "connected"
        logger.info("Database initialized")
    except Exception as exc:
        app.state.startup_status["database"] = "disconnected"
        logger.exception("Database initialization failed: %s", exc)

    admin_email = (os.getenv("ADMIN_LOGIN_EMAIL") or "admin@coepd.com").strip()
    admin_password = (os.getenv("ADMIN_LOGIN_PASSWORD") or "admin123").strip()
    try:
        seed_default_admin_user(email=admin_email, password=admin_password, name="Admin")
    except Exception as exc:
        logger.warning("Unable to seed default admin user: %s", exc)

    logger.info("Authentication enabled")
    logger.info("Application startup complete")

    app.include_router(register_page_routes(templates))
    app.include_router(register_auth_routes(templates))
    app.include_router(chat_router)
    app.include_router(admin_router)

    return app
