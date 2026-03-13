import logging
import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

logger = logging.getLogger("coepd-api")

DATABASE_URL = os.getenv("DATABASE_URL", "")
SQLITE_FALLBACK = "sqlite:///./coepd.db"

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").strip().lower() == "true"
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

# ── Helpers ──────────────────────────────────────────────────────────────

_active_url: str = ""


def is_sqlite() -> bool:
    return _active_url.startswith("sqlite")


def _engine_kwargs_for(url: str) -> dict:
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_recycle=DB_POOL_RECYCLE,
        )
    return kwargs


def _try_connect(url: str, label: str):
    """Try to create & verify an engine. Returns engine or None."""
    try:
        eng = create_engine(url, **_engine_kwargs_for(url))
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to %s", label)
        return eng
    except Exception as exc:
        logger.warning("Connection to %s failed: %s", label, exc)
        return None


# ── Engine initialisation (with retry + fallback) ────────────────────────

engine = None

if DATABASE_URL:
    engine = _try_connect(DATABASE_URL, "Supabase PostgreSQL")
    if engine is None:
        logger.warning("Retrying Supabase connection…")
        engine = _try_connect(DATABASE_URL, "Supabase PostgreSQL (retry)")

if engine is not None:
    _active_url = DATABASE_URL
else:
    logger.warning("Falling back to local SQLite: %s", SQLITE_FALLBACK)
    engine = _try_connect(SQLITE_FALLBACK, "SQLite")
    _active_url = SQLITE_FALLBACK

if engine is None:
    logger.critical("ALL database connections failed — app will have no DB")


def db_available() -> bool:
    """Return True when the database engine has been initialised."""
    return engine is not None


# ── Session factory ──────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

Base = declarative_base()


def init_engine():
    """Create tables. Engine is already created at module level; retries if needed."""
    global engine, _active_url
    if engine is None:
        for url, label in [(DATABASE_URL, "PostgreSQL"), (SQLITE_FALLBACK, "SQLite")]:
            if not url:
                continue
            eng = _try_connect(url, f"{label} (init_engine)")
            if eng is not None:
                engine = eng
                _active_url = url
                SessionLocal.configure(bind=engine)
                break
        if engine is None:
            logger.error("init_engine: could not connect to any database")
            return None
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified (%s)", "SQLite" if is_sqlite() else "PostgreSQL")
    return engine


# ── Dependency ───────────────────────────────────────────────────────────


def get_db() -> Generator[Session | None, None, None]:
    """Yield a DB session, or ``None`` when no engine is bound."""
    if not db_available():
        logger.error("Database engine not initialized — cannot provide DB session")
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
