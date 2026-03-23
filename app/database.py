import os
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_sqlite_path() -> Path:
    """
    Pick a writable SQLite path.
    Prefer the configured path, but don't crash at import time if its parent
    directory is unavailable on the current host.
    """
    configured_path = (os.getenv("SQLITE_DATABASE_PATH") or "").strip()
    candidates: list[Path] = []

    if configured_path:
        candidates.append(Path(configured_path).expanduser())
    elif (os.getenv("RENDER") or "").strip().lower() == "true":
        candidates.append(Path("/var/data/coepd_local.db"))

    candidates.append(BASE_DIR / "coepd_local.db")
    candidates.append(Path("/tmp/coepd_local.db"))

    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError:
            continue

    # Final fallback: relative to the app root, even if parent creation checks failed earlier.
    return BASE_DIR / "coepd_local.db"


DEFAULT_SQLITE_PATH = _resolve_sqlite_path()
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
MSSQL_DATABASE_URL = (os.getenv("MSSQL_DATABASE_URL") or "").strip()
DATABASE_URL = MSSQL_DATABASE_URL or DEFAULT_SQLITE_URL

DB_CONNECT_TIMEOUT_SECONDS = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))
DB_AVAILABILITY_CACHE_SECONDS = int(os.getenv("DB_AVAILABILITY_CACHE_SECONDS", "30"))

engine_connect_args = {"timeout": DB_CONNECT_TIMEOUT_SECONDS}
if DATABASE_URL.startswith("sqlite"):
    # SQLite uses a different connect arg; also needed for FastAPI threaded handlers.
    engine_connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=engine_connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
_db_status_cache: dict[str, float | bool] = {"ok": False, "checked_at": 0.0}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create database tables if they do not exist."""
    # Ensure model metadata is registered before create_all runs.
    import app.db_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if DATABASE_URL.startswith("mssql"):
        _ensure_sqlserver_schema_compatibility()


def _ensure_sqlserver_schema_compatibility() -> None:
    """
    Backfill missing columns in existing SQL Server tables.
    This avoids runtime failures when older local schemas are reused.
    """
    insp = inspect(engine)

    if "leads" in insp.get_table_names():
        lead_columns = {col["name"].lower(): col for col in insp.get_columns("leads")}
        existing = set(lead_columns.keys())
        required = {
            "name": "NVARCHAR(255) NULL",
            "phone": "NVARCHAR(50) NULL",
            "email": "NVARCHAR(255) NULL",
            "location": "NVARCHAR(255) NULL",
            "interested_domain": "NVARCHAR(255) NULL",
            "whatsapp": "NVARCHAR(50) NULL",
            "source": "NVARCHAR(50) NULL",
            "created_at": "DATETIME2 NULL",
        }
        with engine.begin() as conn:
            for col_name, col_type in required.items():
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE [leads] ADD [{col_name}] {col_type}"))

            # Normalize legacy text/varchar created_at to DATETIME2 when needed.
            created_at_type = str(lead_columns.get("created_at", {}).get("type", "")).lower()
            if created_at_type and ("char" in created_at_type or "text" in created_at_type):
                conn.execute(
                    text(
                        "UPDATE [leads] "
                        "SET [created_at] = COALESCE("
                        "TRY_CONVERT(datetime2, [created_at]), "
                        "CAST(TRY_CONVERT(datetimeoffset, [created_at]) AS datetime2)"
                        ") "
                        "WHERE [created_at] IS NOT NULL"
                    )
                )
                conn.execute(text("ALTER TABLE [leads] ALTER COLUMN [created_at] DATETIME2 NULL"))

    if "staff" in insp.get_table_names():
        staff_columns = {col["name"].lower(): col for col in insp.get_columns("staff")}
        existing = set(staff_columns.keys())
        required = {
            "name": "NVARCHAR(120) NOT NULL CONSTRAINT DF_staff_name DEFAULT ''",
            "email": "NVARCHAR(120) NOT NULL CONSTRAINT DF_staff_email DEFAULT ''",
            "password_hash": "NVARCHAR(255) NOT NULL CONSTRAINT DF_staff_password_hash DEFAULT ''",
            "role": "NVARCHAR(20) NOT NULL CONSTRAINT DF_staff_role DEFAULT 'staff'",
            "status": "NVARCHAR(20) NOT NULL CONSTRAINT DF_staff_status DEFAULT 'active'",
            "created_at": "DATETIME2 NULL",
        }
        with engine.begin() as conn:
            for col_name, col_type in required.items():
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE [staff] ADD [{col_name}] {col_type}"))

            created_at_type = str(staff_columns.get("created_at", {}).get("type", "")).lower()
            if created_at_type and ("char" in created_at_type or "text" in created_at_type):
                conn.execute(
                    text(
                        "UPDATE [staff] "
                        "SET [created_at] = COALESCE("
                        "TRY_CONVERT(datetime2, [created_at]), "
                        "CAST(TRY_CONVERT(datetimeoffset, [created_at]) AS datetime2)"
                        ") "
                        "WHERE [created_at] IS NOT NULL"
                    )
                )
                conn.execute(text("ALTER TABLE [staff] ALTER COLUMN [created_at] DATETIME2 NULL"))


def db_available():
    """Return True if database connection works."""
    now = time.monotonic()
    checked_at = float(_db_status_cache.get("checked_at", 0.0) or 0.0)
    if now - checked_at < DB_AVAILABILITY_CACHE_SECONDS:
        return bool(_db_status_cache.get("ok", False))

    try:
        with engine.connect():
            _db_status_cache["ok"] = True
            _db_status_cache["checked_at"] = now
            return True
    except Exception:
        _db_status_cache["ok"] = False
        _db_status_cache["checked_at"] = now
        return False
