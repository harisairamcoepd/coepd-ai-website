import os

import uvicorn

from app.factory import create_app


app = create_app()

# ── SAFE TABLE CREATION & STARTUP LOGGING ──
from app.database import engine
from app.db_models import Base
import os

@app.on_event("startup")
def startup():
    print("FastAPI server starting")
    print("DATABASE_URL loaded:", bool(os.getenv("DATABASE_URL")))
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully")
    except Exception as e:
        print("Database initialization failed:", e)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        workers=2,
        proxy_headers=True,
        reload=False,
    )