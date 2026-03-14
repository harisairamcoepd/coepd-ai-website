import os
import uvicorn
from fastapi.staticfiles import StaticFiles

from app.factory import create_app


app = create_app()

# Serve top-level static/ folder for templates that reference /static/...
try:
    app.mount("/static", StaticFiles(directory=str(os.path.join(os.path.dirname(__file__), "static"))), name="static")
except Exception:
    # If mount fails, continue - app.factory also mounts a static directory.
    pass


# SAFE TABLE CREATION & STARTUP LOGGING
from app.database import create_tables
from fastapi.responses import JSONResponse


DOMAIN_DATA = [
    {"name": "Platform Engineering", "description": "Build and optimize platform tooling"},
    {"name": "Site Reliability", "description": "Improve uptime and observability"},
    {"name": "Quality Assurance", "description": "Define testing strategy"},
    {"name": "Banking", "description": "Analyze lending, onboarding, and risk workflows"},
    {"name": "Healthcare", "description": "Improve patient and hospital process outcomes"},
    {"name": "Retail", "description": "Optimize merchandising and inventory decisions"},
    {"name": "Insurance", "description": "Improve claims and policy lifecycle operations"},
    {"name": "Telecommunications", "description": "Reduce churn and optimize billing workflows"},
    {"name": "E-Commerce", "description": "Improve conversion funnels and checkout journeys"},
    {"name": "Supply Chain", "description": "Optimize procurement and logistics planning"},
]

CITY_DISTRIBUTION = {"labels": ["Hyderabad", "Bangalore", "Pune"], "data": [5, 3, 2]}
EXPERIENCE_DISTRIBUTION = {"labels": ["0-1 yrs", "1-3 yrs", "3-5 yrs"], "data": [4, 3, 1]}
INDUSTRY_DEMAND = {"labels": ["Banking", "Healthcare", "Retail"], "data": [6, 3, 2]}
LOCATION_TRENDS = {"labels": ["Hyderabad", "Bangalore", "Pune", "Mumbai", "Chennai"], "data": [25, 25, 18, 10, 11]}
EXPERIENCE_TRENDS = {"labels": ["0-1 yrs", "1-3 yrs", "3-5 yrs", "5+ yrs"], "data": [22, 34, 28, 16]}
DOMAIN_TRENDS = {"labels": ["Banking", "Healthcare", "Retail", "Insurance", "IT/Consulting"], "data": [24, 19, 18, 17, 22]}


@app.on_event("startup")
def startup():
    print("FastAPI server starting")
    print("DATABASE_URL loaded:", bool(os.getenv("DATABASE_URL")))
    try:
        create_tables()
        print("Database initialized successfully")
    except Exception as e:
        print("Database initialization failed:", e)


@app.get("/api/domains")
def api_domains():
    try:
        return DOMAIN_DATA
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/api/analytics/city-distribution")
def api_city_distribution():
    return CITY_DISTRIBUTION


@app.get("/api/analytics/experience-distribution")
def api_experience_distribution():
    return EXPERIENCE_DISTRIBUTION


@app.get("/api/analytics/top-industries")
def api_industry_demand():
    return INDUSTRY_DEMAND


@app.get("/api/analytics/location-trends")
def api_location_trends():
    return LOCATION_TRENDS


@app.get("/api/analytics/experience-trends")
def api_experience_trends():
    return EXPERIENCE_TRENDS


@app.get("/api/analytics/domain-trends")
def api_domain_trends():
    return DOMAIN_TRENDS


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        workers=2,
        proxy_headers=True,
        reload=False,
    )
