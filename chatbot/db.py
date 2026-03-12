import calendar
import csv
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

_IST = timezone(timedelta(hours=5, minutes=30))

import bcrypt


# On Vercel/serverless, the filesystem is read-only except /tmp
if os.environ.get("VERCEL"):
    DB_PATH = Path("/tmp/app.db")
else:
    DB_PATH = Path(__file__).resolve().parent / "app.db"
_LOCAL = threading.local()

_TS_FORMATS = (
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)


def _utc_now_string() -> str:
    return datetime.now(_IST).strftime("%Y-%m-%dT%H:%M:%S")


def _parse_ts(raw: str) -> datetime | None:
    """Parse a timestamp string trying multiple formats."""
    raw = (raw or "").strip()
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def get_db() -> sqlite3.Connection:
    conn = getattr(_LOCAL, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=3000")
        _LOCAL.conn = conn
    return conn


@contextmanager
def db_cursor():
    conn = get_db()
    cur = conn.cursor()
    try:
        yield conn, cur
    finally:
        cur.close()


def _columns(cur: sqlite3.Cursor, table: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return {row["name"] for row in cur.fetchall()}


def _table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (table,))
    return cur.fetchone() is not None


def init_db() -> None:
    with db_cursor() as (conn, cur):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT PRIMARY KEY,
                stage TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                location TEXT,
                interested_domain TEXT,
                demo_day TEXT,
                whatsapp TEXT,
                source TEXT NOT NULL DEFAULT 'webpage',
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'inactive',
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS staff_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'inactive',
                created_at TEXT NOT NULL
            )
            """
        )

        staff_cols = _columns(cur, "staff_users")
        if "status" not in staff_cols:
            cur.execute("ALTER TABLE staff_users ADD COLUMN status TEXT NOT NULL DEFAULT 'inactive'")

        leads_cols = _columns(cur, "leads")
        migrations = {
            "location": "TEXT",
            "interested_domain": "TEXT",
            "experience": "TEXT",
            "demo_day": "TEXT",
            "whatsapp": "TEXT",
            "source": "TEXT NOT NULL DEFAULT 'webpage'",
            "created_at": "TEXT NOT NULL DEFAULT ''",
        }
        for col, col_type in migrations.items():
            if col not in leads_cols:
                cur.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type}")

        users_cols = _columns(cur, "users")
        user_migrations = {
            "password": "TEXT NOT NULL DEFAULT ''",
            "role": "TEXT NOT NULL DEFAULT 'staff'",
            "status": "TEXT NOT NULL DEFAULT 'inactive'",
            "created_at": "TEXT NOT NULL DEFAULT ''",
        }
        for col, col_type in user_migrations.items():
            if col not in users_cols:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")

        if _table_exists(cur, "staff_users"):
            cur.execute(
                """
                INSERT OR IGNORE INTO users(name, email, password, role, status, created_at)
                SELECT
                    ifnull(name, ''),
                    lower(ifnull(email, '')),
                    ifnull(password, ''),
                    CASE WHEN lower(ifnull(role, 'staff')) = 'admin' THEN 'admin' ELSE 'staff' END,
                    CASE WHEN lower(ifnull(status, 'inactive')) = 'active' THEN 'active' ELSE 'inactive' END,
                    ifnull(created_at, '')
                FROM staff_users
                WHERE trim(ifnull(email, '')) <> ''
                """
            )

        cur.execute(
            """
            UPDATE users
            SET role = CASE WHEN lower(ifnull(role, 'staff')) = 'admin' THEN 'admin' ELSE 'staff' END,
                status = CASE WHEN lower(ifnull(status, 'inactive')) = 'active' THEN 'active' ELSE 'inactive' END,
                email = lower(trim(ifnull(email, '')))
            """
        )

        cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.commit()


def load_session(user_id: str) -> dict[str, Any]:
    with db_cursor() as (_conn, cur):
        cur.execute("SELECT stage, data FROM sessions WHERE user_id = ?", (user_id,))
        row = cur.fetchone()

    if not row:
        return {"stage": "start", "data": {}}

    try:
        data = json.loads(row["data"] or "{}")
    except json.JSONDecodeError:
        data = {}

    return {"stage": row["stage"], "data": data}


def save_session(user_id: str, stage: str, data: dict[str, Any]) -> None:
    with db_cursor() as (conn, cur):
        cur.execute(
            """
            INSERT INTO sessions(user_id, stage, data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                stage = excluded.stage,
                data = excluded.data,
                updated_at = excluded.updated_at
            """,
            (user_id, stage, json.dumps(data), _utc_now_string()),
        )
        conn.commit()


def reset_session(user_id: str) -> None:
    with db_cursor() as (conn, cur):
        cur.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()


def save_lead(lead: dict[str, Any]) -> int:
    created_at_input = str(lead.get("created_at", "")).strip()
    created_at = created_at_input if _parse_ts(created_at_input) else _utc_now_string()
    normalized_source = str(lead.get("source", "webpage")).strip().lower()
    if normalized_source in {"website", "website_form"}:
        normalized_source = "webpage"
    if normalized_source not in {"webpage", "chatbot"}:
        normalized_source = "webpage"

    with db_cursor() as (conn, cur):
        normalized_email = str(lead.get("email", "")).strip().lower()
        normalized_phone = str(lead.get("phone", "")).strip()

        cur.execute(
            """
            SELECT id
            FROM leads
            WHERE lower(email) = ?
              AND phone = ?
              AND lower(source) = ?
              AND datetime(created_at) >= datetime('now', '-10 minutes')
            ORDER BY id DESC
            LIMIT 1
            """,
            (normalized_email, normalized_phone, normalized_source),
        )
        existing = cur.fetchone()
        if existing:
            return int(existing["id"])

        cur.execute(
            """
                INSERT INTO leads(
                    name,
                    phone,
                    email,
                    location,
                    interested_domain,
                    experience,
                    demo_day,
                    whatsapp,
                    source,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(lead.get("name", "")).strip(),
                normalized_phone,
                normalized_email,
                str(lead.get("location", "")).strip(),
                str(lead.get("interested_domain", lead.get("domain", ""))).strip(),
                str(lead.get("experience", "")).strip(),
                str(lead.get("demo_day", "")).strip(),
                str(lead.get("whatsapp", "")).strip(),
                normalized_source,
                created_at,
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        return int(row_id) if row_id is not None else 0


def delete_lead(lead_id: int) -> bool:
    with db_cursor() as (conn, cur):
        cur.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        deleted = cur.rowcount > 0
        conn.commit()
    return deleted


def update_lead_status(lead_id: int, working_status: str) -> bool:
    with db_cursor() as (conn, cur):
        cur.execute(
            "UPDATE leads SET working_status = ? WHERE id = ?",
            (working_status.strip(), lead_id),
        )
        updated = cur.rowcount > 0
        conn.commit()
    return updated


def _normalize_role(role: str) -> str:
    value = (role or "").strip().lower()
    return value if value in {"admin", "staff"} else "staff"


def fetch_user_by_email(email: str) -> dict[str, Any] | None:
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return None
    with db_cursor() as (_conn, cur):
        cur.execute("SELECT * FROM users WHERE lower(email) = ?", (normalized_email,))
        row = cur.fetchone()
    if not row:
        return None
    user = dict(row)
    user_status = str(user.get("status", "")).strip().lower()
    if user_status not in {"active", "inactive"}:
        user_status = "inactive"
    user["status"] = user_status
    user["is_active"] = 1 if user_status == "active" else 0
    return user


def fetch_user_by_id(user_id: int) -> dict[str, Any] | None:
    with db_cursor() as (_conn, cur):
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
    if not row:
        return None
    user = dict(row)
    user_status = str(user.get("status", "")).strip().lower()
    if user_status not in {"active", "inactive"}:
        user_status = "inactive"
    user["status"] = user_status
    user["is_active"] = 1 if user_status == "active" else 0
    return user


def create_user(name: str, email: str, role: str) -> int:
    normalized_name = (name or "").strip()
    normalized_email = (email or "").strip().lower()
    normalized_role = _normalize_role(role)
    with db_cursor() as (conn, cur):
        cur.execute(
            """
            INSERT INTO users(name, email, password, role, status, created_at)
            VALUES (?, ?, '', ?, 'active', ?)
            """,
            (normalized_name, normalized_email, normalized_role, _utc_now_string()),
        )
        conn.commit()
        row_id = cur.lastrowid
    return int(row_id) if row_id is not None else 0


def upsert_user(name: str, email: str, role: str, is_active: int = 1) -> dict[str, Any] | None:
    normalized_name = (name or "").strip()
    normalized_email = (email or "").strip().lower()
    normalized_role = _normalize_role(role)
    if not normalized_email:
        return None

    normalized_status = "active" if is_active else "inactive"

    with db_cursor() as (conn, cur):
        cur.execute(
            """
            INSERT INTO users(name, email, password, role, status, created_at)
            VALUES (?, ?, '', ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name = excluded.name,
                role = excluded.role,
                status = excluded.status
            """,
            (
                normalized_name,
                normalized_email,
                normalized_role,
                normalized_status,
                _utc_now_string(),
            ),
        )
        conn.commit()
    return fetch_user_by_email(normalized_email)


def list_users() -> list[dict[str, Any]]:
    with db_cursor() as (_conn, cur):
        cur.execute("SELECT * FROM users ORDER BY id DESC")
        rows = cur.fetchall()
    users: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        user_status = str(item.get("status", "")).strip().lower()
        if user_status not in {"active", "inactive"}:
            user_status = "inactive"
            item["status"] = user_status
        item["is_active"] = 1 if user_status == "active" else 0
        users.append(item)
    return users


def update_user_role(user_id: int, role: str) -> bool:
    normalized_role = _normalize_role(role)
    with db_cursor() as (conn, cur):
        cur.execute("UPDATE users SET role = ? WHERE id = ?", (normalized_role, user_id))
        updated = cur.rowcount > 0
        conn.commit()
    return updated


def set_user_active(user_id: int, is_active: bool) -> bool:
    normalized_status = "active" if is_active else "inactive"
    with db_cursor() as (conn, cur):
        cur.execute(
            "UPDATE users SET status = ? WHERE id = ?",
            (normalized_status, user_id),
        )
        updated = cur.rowcount > 0
        conn.commit()
    return updated


def delete_user(user_id: int) -> bool:
    with db_cursor() as (conn, cur):
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        deleted = cur.rowcount > 0
        conn.commit()
    return deleted


def _normalize_staff_role(role: str) -> str:
    value = (role or "").strip().lower()
    return "admin" if value == "admin" else "staff"


def _normalize_staff_status(status: str) -> str:
    value = (status or "").strip().lower()
    return "active" if value == "active" else "inactive"


def create_staff_user(
    name: str,
    email: str,
    password: str,
    role: str = "staff",
    status: str = "inactive",
) -> int:
    normalized_name = (name or "").strip()
    normalized_email = (email or "").strip().lower()
    normalized_role = _normalize_staff_role(role)
    normalized_status = _normalize_staff_status(status)
    hashed_password = bcrypt.hashpw((password or "").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with db_cursor() as (conn, cur):
        cur.execute(
            """
            INSERT INTO users(name, email, password, role, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (normalized_name, normalized_email, hashed_password, normalized_role, normalized_status, _utc_now_string()),
        )
        conn.commit()
        row_id = cur.lastrowid
    return int(row_id) if row_id is not None else 0


def fetch_staff_user_by_email(email: str) -> dict[str, Any] | None:
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return None
    with db_cursor() as (_conn, cur):
        cur.execute("SELECT * FROM users WHERE lower(email) = ?", (normalized_email,))
        row = cur.fetchone()
    return dict(row) if row else None


def list_staff_users() -> list[dict[str, Any]]:
    with db_cursor() as (_conn, cur):
        cur.execute(
            """
            SELECT id, name, email, role, status, created_at
            FROM users
            WHERE lower(role) IN ('admin', 'staff')
            ORDER BY id DESC
            """
        )
        rows = cur.fetchall()
    return [dict(row) for row in rows]


def set_staff_status(staff_id: int, status: str) -> bool:
    normalized_status = _normalize_staff_status(status)
    with db_cursor() as (conn, cur):
        cur.execute("UPDATE users SET status = ? WHERE id = ?", (normalized_status, staff_id))
        updated = cur.rowcount > 0
        conn.commit()
    return updated


def set_staff_role(staff_id: int, role: str) -> bool:
    normalized_role = _normalize_staff_role(role)
    with db_cursor() as (conn, cur):
        cur.execute("UPDATE users SET role = ? WHERE id = ?", (normalized_role, staff_id))
        updated = cur.rowcount > 0
        conn.commit()
    return updated


def update_staff_password(staff_id: int, password: str) -> bool:
    hashed_password = bcrypt.hashpw((password or "").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with db_cursor() as (conn, cur):
        cur.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, staff_id))
        updated = cur.rowcount > 0
        conn.commit()
    return updated


def delete_staff_user(staff_id: int) -> bool:
    with db_cursor() as (conn, cur):
        cur.execute("DELETE FROM users WHERE id = ?", (staff_id,))
        deleted = cur.rowcount > 0
        conn.commit()
    return deleted


def verify_staff_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw((plain_password or "").encode("utf-8"), (hashed_password or "").encode("utf-8"))
    except Exception:
        return False


def seed_default_admin_user(
    email: str = "admin@coepd.com",
    password: str = "admin123",
    name: str = "Admin",
) -> None:
    normalized_email = (email or "").strip().lower() or "admin@coepd.com"
    existing = fetch_staff_user_by_email(normalized_email)
    hashed_password = bcrypt.hashpw((password or "").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    if existing:
        with db_cursor() as (conn, cur):
            cur.execute(
                """
                UPDATE users
                SET role = 'admin',
                    status = 'active',
                    name = ?,
                    password = CASE
                        WHEN ifnull(password, '') = '' THEN ?
                        ELSE password
                    END
                WHERE lower(email) = ?
                """,
                (name or "Admin", hashed_password, normalized_email),
            )
            conn.commit()
        return
    create_staff_user(name=name, email=normalized_email, password=password, role="admin", status="active")


def seed_allowed_google_users(emails: list[str], admin_email: str | None = None) -> None:
    cleaned = [str(email or "").strip().lower() for email in emails if str(email or "").strip()]
    if not cleaned:
        return

    admin = str(admin_email or "").strip().lower()
    for email in cleaned:
        role = "admin" if admin and email == admin else "staff"
        display_name = email.split("@", 1)[0].replace(".", " ").title()
        existing = fetch_user_by_email(email)
        if existing:
            continue
        upsert_user(name=display_name or email, email=email, role=role, is_active=1)


def _with_display_fields(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    raw = str(item.get("created_at", "")).strip()
    dt = _parse_ts(raw)
    if dt:
        item["date_display"] = dt.strftime("%d %b %Y")
        item["time_display"] = dt.strftime("%I:%M %p")
        item["datetime_display"] = dt.strftime("%d %b %Y | %I:%M %p")
    else:
        item["date_display"] = "Unknown"
        item["time_display"] = "Unknown"
        item["datetime_display"] = "Unknown"
    return item


def fetch_leads(
    date_prefix: str | None = None,
    source: str | None = None,
    search: str | None = None,
    interested_domain: str | None = None,
) -> list[dict[str, Any]]:
    with db_cursor() as (_conn, cur):
        if date_prefix:
            # Ignore malformed filter dates to avoid accidental empty dashboards.
            try:
                datetime.strptime(date_prefix, "%Y-%m-%d")
            except ValueError:
                date_prefix = None


        where_clauses: list[str] = []
        params: list[str] = []

        if date_prefix:
            where_clauses.append("date(created_at) = ?")
            params.append(date_prefix)

        normalized_source = (source or "").strip().lower()
        if normalized_source and normalized_source != "all":
            where_clauses.append("lower(source) = ?")
            params.append(normalized_source)

        normalized_domain = (interested_domain or "").strip().lower()
        if normalized_domain and normalized_domain != "all":
            where_clauses.append("lower(ifnull(interested_domain, '')) = ?")
            params.append(normalized_domain)

        normalized_search = (search or "").strip().lower()
        if normalized_search:
            where_clauses.append(
                "(" 
                "lower(name) LIKE ? OR "
                "lower(email) LIKE ? OR "
                "lower(phone) LIKE ? OR "
                "lower(ifnull(location, '')) LIKE ? OR "
                "lower(ifnull(interested_domain, '')) LIKE ? OR "
                "lower(ifnull(experience, '')) LIKE ?"
                ")"
            )
            like_value = f"%{normalized_search}%"
            params.extend([like_value] * 6)

        sql = "SELECT * FROM leads"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY datetime(created_at) DESC, id DESC"

        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    return [_with_display_fields(row) for row in rows]


def fetch_dashboard_leads(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> dict[str, Any]:
    """Return paginated lead rows for staff dashboard in newest-first order."""
    safe_page = max(1, int(page or 1))
    safe_page_size = max(1, min(100, int(page_size or 20)))
    offset = (safe_page - 1) * safe_page_size

    where_clause = ""
    params: list[Any] = []
    normalized_search = (search or "").strip().lower()
    if normalized_search:
        where_clause = (
            "WHERE ("
            "lower(name) LIKE ? OR "
            "lower(email) LIKE ? OR "
            "lower(phone) LIKE ? OR "
            "lower(ifnull(location, '')) LIKE ? OR "
            "lower(ifnull(interested_domain, '')) LIKE ? OR "
            "lower(ifnull(experience, '')) LIKE ?"
            ")"
        )
        like_value = f"%{normalized_search}%"
        params.extend([like_value] * 6)

    with db_cursor() as (_conn, cur):
        cur.execute(f"SELECT COUNT(*) AS total_count FROM leads {where_clause}", tuple(params))
        total_row = cur.fetchone()
        total = int(total_row["total_count"] or 0) if total_row else 0

        cur.execute(
            f"""
            SELECT
                id,
                name,
                email,
                phone,
                location,
                interested_domain,
                experience,
                whatsapp,
                CASE
                    WHEN lower(ifnull(source, '')) IN ('website', 'website_form') THEN 'webpage'
                    WHEN lower(ifnull(source, '')) = 'chatbot' THEN 'chatbot'
                    ELSE 'webpage'
                END AS source,
                created_at
            FROM leads
            {where_clause}
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [safe_page_size, offset]),
        )
        rows = cur.fetchall()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def fetch_dashboard_stats() -> dict[str, int]:
    with db_cursor() as (_conn, cur):
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_leads,
                SUM(CASE WHEN date(created_at) = date('now', '+5 hours', '+30 minutes') THEN 1 ELSE 0 END) AS today_leads,
                SUM(CASE WHEN date(created_at) >= date('now', '+5 hours', '+30 minutes', 'weekday 0', '-7 days') THEN 1 ELSE 0 END) AS week_leads,
                SUM(CASE WHEN strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', '+5 hours', '+30 minutes') THEN 1 ELSE 0 END) AS month_leads,
                SUM(CASE WHEN lower(ifnull(source, '')) = 'chatbot' THEN 1 ELSE 0 END) AS chatbot_leads,
                SUM(CASE WHEN lower(ifnull(source, '')) IN ('webpage', 'website', 'website_form') THEN 1 ELSE 0 END) AS website_leads
            FROM leads
            """
        )
        row = cur.fetchone()
    return {
        "total_leads": int(row["total_leads"] or 0),
        "today_leads": int(row["today_leads"] or 0),
        "week_leads": int(row["week_leads"] or 0),
        "month_leads": int(row["month_leads"] or 0),
        "chatbot_leads": int(row["chatbot_leads"] or 0),
        "website_leads": int(row["website_leads"] or 0),
    }


def fetch_monthly_lead_growth(year: int | None = None, month: int | None = None) -> dict[str, list[Any]]:
    now = datetime.now(timezone.utc)
    target_year = year or now.year
    target_month = month or now.month
    month_key = f"{target_year}-{target_month:02d}"
    days_in_month = calendar.monthrange(target_year, target_month)[1]

    day_map = {
        f"{target_year}-{target_month:02d}-{day:02d}": 0
        for day in range(1, days_in_month + 1)
    }

    with db_cursor() as (_conn, cur):
        cur.execute(
            """
            SELECT date(created_at) AS lead_date, COUNT(*) AS lead_count
            FROM leads
            WHERE strftime('%Y-%m', date(created_at)) = ?
            GROUP BY date(created_at)
            ORDER BY date(created_at)
            """,
            (month_key,),
        )
        rows = cur.fetchall()

    for row in rows:
        lead_date = str(row["lead_date"] or "")
        if lead_date in day_map:
            day_map[lead_date] = int(row["lead_count"] or 0)

    return {
        "dates": list(day_map.keys()),
        "counts": list(day_map.values()),
    }


def export_leads_to_csv(filename: str) -> str:
    out_path = str(Path(__file__).resolve().parent / filename)
    rows = fetch_leads()
    fields = [
        "id",
        "name",
        "phone",
        "email",
        "location",
        "interested_domain",
        "experience",
        "whatsapp",
        "source",
        "created_at",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})

    return out_path
