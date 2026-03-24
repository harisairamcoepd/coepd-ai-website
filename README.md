# COEPD AI Website

COEPD AI Website is a FastAPI-based web platform for Business Analyst program marketing, lead capture, chatbot conversations, and admin/staff lead operations.

It serves:
- Public marketing pages rendered with Jinja templates.
- Chatbot and enquiry endpoints for incoming leads.
- Admin/staff authentication with session and JWT support.
- Lead analytics and export endpoints for operations teams.

## Core Features

- Public landing site with static assets and component-based templates.
- AI chatbot flow with persisted chat/lead data.
- Lead capture APIs (`/lead`, `/contact`, `/enquiry`, `/leads`).
- Admin dashboard with filters, stats, CSV export, and staff management.
- Staff dashboard with paginated lead view.
- Authentication middleware with cookie-based auth + CSRF checks.
- Startup checks for missing dependencies, env configuration, and merge conflict markers.
- Render-ready deployment configuration.

## Architecture

```mermaid
flowchart LR
    U[Website Visitor] --> A[FastAPI App]
    S[Staff/Admin User] --> A

    A --> MW[Middleware Layer<br/>Auth + CSRF + Rate Limit + CORS]
    MW --> R1[Pages Router]
    MW --> R2[Auth Router]
    MW --> R3[Chat Router]
    MW --> R4[Admin Router]
    MW --> R5[Leads Router]

    R1 --> T[Jinja Templates]
    R1 --> ST[Static Assets]
    R2 --> DB[(Primary DB)]
    R3 --> CDB[(Chatbot SQLite)]
    R3 --> DB
    R4 --> DB
    R5 --> DB
```

## Request Flow (High Level)

```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant M as Auth+Security Middleware
    participant R as Router/Handler
    participant D as Database

    C->>F: HTTP Request
    F->>M: Apply middleware checks
    M->>R: Forward if allowed
    R->>D: Read/Write (if required)
    D-->>R: Result
    R-->>C: HTML or JSON Response
```

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn
- Jinja2 templates
- SQLAlchemy
- SQLite (chatbot + local fallback)
- Optional SQL Server via `pyodbc`
- HTML/CSS/JavaScript frontend assets

## Project Structure

```text
coepd-ai-website/
├─ app/
│  ├─ factory.py               # App creation, middleware, startup checks
│  ├─ auth.py                  # Token/session auth helpers
│  ├─ middleware/              # Auth/security + rate limiting
│  ├─ routers/                 # pages, auth, chat, admin, leads
│  ├─ services/                # lead service/business logic
│  ├─ database.py              # DB engine/session config
│  └─ db_models.py             # SQLAlchemy models
├─ chatbot/                    # Chatbot DB + related logic
├─ templates/                  # Jinja templates
├─ static/                     # CSS/JS/images/chatbot assets
├─ main.py                     # Entry point + analytics endpoints
├─ render.yaml                 # Render service config
└─ requirements.txt
```

## API and Page Endpoints (Summary)

Public pages:
- `GET /`
- `GET /privacy`
- `GET /health`

Authentication:
- `GET /staff`, `POST /staff`
- `GET /admin`, `POST /admin`
- `POST /api/login`
- `POST /api/admin/login`
- `POST /api/staff/login`
- `GET /auth/me`
- `GET /logout`, `POST /auth/logout`

Chat and lead capture:
- `POST /chat`
- `POST /lead`
- `POST /contact`
- `POST /enquiry`
- `POST /leads`

Admin APIs:
- `GET /admin/leads`
- `GET /admin/stats`
- `GET /admin/lead-growth`
- `GET /admin/source-breakdown`
- `GET /admin/export`
- Staff management routes under `/admin/staff...`

Analytics in `main.py`:
- `GET /api/domains`
- `GET /api/analytics/city-distribution`
- `GET /api/analytics/experience-distribution`
- `GET /api/analytics/top-industries`
- `GET /api/analytics/location-trends`
- `GET /api/analytics/experience-trends`
- `GET /api/analytics/domain-trends`

## Environment Variables

Create a `.env` file in project root.

Minimum recommended:

```env
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=2
AUTH_COOKIE_SECURE=false
SESSION_SECRET_KEY=change-me
ADMIN_LOGIN_EMAIL=admin
ADMIN_LOGIN_PASSWORD=admin
```

Database options:
- Local/default SQLite is used when SQL Server is unavailable.
- For SQL Server, configure `MSSQL_DATABASE_URL` in SQLAlchemy format.

Render defaults from `render.yaml`:
- `PYTHON_VERSION=3.11.11`
- `SQLITE_DATABASE_PATH=/var/data/coepd_local.db`
- `CHATBOT_DB_PATH=/var/data/chatbot_app.db`
- `DB_CONNECT_TIMEOUT_SECONDS=5`
- `DB_AVAILABILITY_CACHE_SECONDS=15`

## Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add `.env` values (see above).

3. Run app:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open:
- `http://localhost:8000/`
- `http://localhost:8000/health`

## Render Deployment

This repository includes `render.yaml` for one web service.

```mermaid
flowchart TD
    G[Push to GitHub main] --> R[Render Build]
    R --> I[pip install -r requirements.txt]
    I --> S[Start: uvicorn main:app --host 0.0.0.0 --port $PORT]
    S --> H[Health Check: /health]
    H --> L[Service Live]
```

### Production Deploy Checklist (No Data Loss)

1. Keep the same Render service and attached disk (`/var/data`). Do not recreate the service unless you migrate data first.
2. Confirm env vars:
   - `JWT_SECRET_KEY=<strong secret>`
   - `AUTH_COOKIE_SECURE=true`
   - `SQLITE_DATABASE_PATH=/var/data/coepd_local.db`
   - `CHATBOT_DB_PATH=/var/data/chatbot_app.db`
3. Build command:
   - `pip install -r requirements.txt`
4. Start command:
   - `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Health check path:
   - `/health`

### Backup Before Deploy (Recommended)

Take a disk snapshot or copy both DB files before major releases:

```bash
cp /var/data/coepd_local.db /var/data/coepd_local.backup.$(date +%F_%H%M%S).db
cp /var/data/chatbot_app.db /var/data/chatbot_app.backup.$(date +%F_%H%M%S).db
```

If SQLite is busy, stop app briefly before backup for a fully consistent file copy.

### Rollback-Safe Data Migration (Old Service -> New Service)

Use this only when moving to a new Render service/disk.

1. Put old service in maintenance mode (or stop writes briefly).
2. Copy DB files from old disk:
   - `/var/data/coepd_local.db`
   - `/var/data/chatbot_app.db`
3. Upload/copy them to new service disk at same paths.
4. Set same env vars (`SQLITE_DATABASE_PATH`, `CHATBOT_DB_PATH`).
5. Start new service and verify:
   - `/health` returns connected DB status
   - admin/staff dashboards show historical leads/users

### Optional MSSQL Setup

Default deploy uses SQLite (recommended on Render free/basic setups).

If you need MSSQL:

1. Install extra dependency:

```bash
pip install -r requirements-mssql.txt
```

2. Set `MSSQL_DATABASE_URL` env var.
3. Ensure ODBC Driver 18 for SQL Server is available in runtime image.
4. Keep SQLite env vars as fallback unless you intentionally disable fallback.

## Operations Notes

- If root (`/`) returns `{"error":"Service temporarily unavailable"}`, check logs for middleware-caught exceptions.
- Ensure `JWT_SECRET_KEY` is set in production.
- Keep `AUTH_COOKIE_SECURE=true` in HTTPS production environments.
- Verify persistent disk is mounted on Render for SQLite durability.

## Testing

Basic endpoint checks can be run using:

```bash
python test_endpoints.py
```

## Security Checklist

- Set strong `JWT_SECRET_KEY`.
- Use non-default admin credentials.
- Enable secure cookies in production.
- Restrict CORS origins for production instead of `*`.
- Rotate credentials periodically.
