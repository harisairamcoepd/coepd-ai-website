import os

import uvicorn

from app.factory import create_app

app = create_app()


@app.on_event("startup")
async def _ensure_tables():
    from app.database import init_engine
    init_engine()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        workers=2,
        proxy_headers=True,
        reload=False,
    )