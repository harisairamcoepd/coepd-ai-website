import logging
import os
from collections.abc import Generator


# ── SAFE POSTGRESQL CONNECTION ──
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found")

# Render sometimes uses postgres:// instead of postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# ── DATABASE SESSION DEPENDENCY ──
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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


    """Create tables. Engine is already created at module level; retries if needed."""
    global engine, _active_url
    if engine is None:
        if DATABASE_URL:
            eng = _try_connect(DATABASE_URL, "PostgreSQL (init_engine)")
            if eng is not None:
                engine = eng
                _active_url = DATABASE_URL

                # ── SAFE DATABASE CONNECTION ──
                import os
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker, declarative_base
                from dotenv import load_dotenv

                load_dotenv()

                DATABASE_URL = os.getenv("DATABASE_URL")
                if not DATABASE_URL:
                    raise RuntimeError("DATABASE_URL not found")

                # Render sometimes provides 'postgres://' instead of 'postgresql://' for SQLAlchemy
                if DATABASE_URL.startswith("postgres://"):
                    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

                engine = create_engine(
                    DATABASE_URL,
                    pool_pre_ping=True
                )

                SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=engine
                )

                Base = declarative_base()

                # ── ADD DATABASE SESSION DEPENDENCY ──
                def get_db():
                    db = SessionLocal()
                    try:
                        yield db
                    finally:
                        db.close()
