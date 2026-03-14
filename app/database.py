import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, fall back to a local sqlite file for development.
# This prevents the application from crashing when running locally without a DB.
if not DATABASE_URL:
    print("Warning: DATABASE_URL not found — falling back to sqlite:///./dev.db")
    DATABASE_URL = "sqlite:///./dev.db"

# Fix Render postgres URL
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables if they do not exist"""
    Base.metadata.create_all(bind=engine)

def db_available():
    """Return True if database connection works"""
    try:
        with engine.connect():
            return True
    except Exception:
        return False
