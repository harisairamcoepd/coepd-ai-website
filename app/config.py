from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
PREFERRED_STATIC_DIR = BASE_DIR / "data" / "static"
LEGACY_STATIC_DIR = BASE_DIR / "static"
STATIC_DIR = PREFERRED_STATIC_DIR if PREFERRED_STATIC_DIR.exists() else LEGACY_STATIC_DIR

load_dotenv(BASE_DIR / ".env")
