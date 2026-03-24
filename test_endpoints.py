"""Quick endpoint test script.

Default mode runs in-process via FastAPI TestClient (no running server needed).
Set TEST_REMOTE=1 to target a live server at BASE.
"""
import json
import os
import sys

import requests
from fastapi.testclient import TestClient

from main import app

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")
USE_REMOTE = os.getenv("TEST_REMOTE", "0") == "1"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def t(path: str) -> str:
    return f"{BASE}{path}" if USE_REMOTE else path


def test(label, method, target, session=None, **kwargs):
    print(f"\n=== {label} ===")
    try:
        client = session or (requests if USE_REMOTE else TestClient(app))
        if USE_REMOTE:
            response = getattr(client, method)(target, timeout=5, **kwargs)
        else:
            response = client.request(method.upper(), target, **kwargs)

        print(f"Status: {response.status_code}")
        try:
            print(f"Body: {json.dumps(response.json(), indent=2)[:400]}")
        except Exception:
            print(f"Body: {response.text[:400]}")
    except Exception as exc:
        print(f"Error: {exc}")


# 1. Health check
test("GET /", "get", t("/"))

# 2. Public lead submission
test("POST /api/leads", "post", t("/api/leads"), json={
    "name": "Hari",
    "phone": "7337212474",
    "email": "hari@gmail.com",
    "location": "Hyderabad",
    "interested_domain": "Business Analyst",
    "whatsapp": "7337212474",
    "source": "chatbot",
})

# 3. Public lead list
test("GET /api/leads", "get", t("/api/leads"))

# 4. Staff login
test("POST /api/staff/login", "post", t("/api/staff/login"), json={
    "email": "admin",
    "password": "admin",
})

# 5. Admin login (returns cookie for subsequent requests)
session = requests.Session() if USE_REMOTE else TestClient(app)
print("\n=== POST /api/admin/login (session) ===")
try:
    if USE_REMOTE:
        login_response = session.post(
            t("/api/admin/login"),
            json={"email": "admin", "password": "admin"},
            timeout=5,
        )
    else:
        login_response = session.post(
            t("/api/admin/login"),
            json={"email": "admin", "password": "admin"},
        )

    print(f"Status: {login_response.status_code}")
    print(f"Body: {json.dumps(login_response.json(), indent=2)[:400]}")
except Exception as exc:
    print(f"Error: {exc}")

# 6. Admin leads (with auth cookie)
test("GET /api/admin/leads (auth)", "get", t("/api/admin/leads"), session=session)

# 7. Admin stats (with auth cookie)
test("GET /api/admin/stats (auth)", "get", t("/api/admin/stats"), session=session)

# 8. Lead growth (with auth cookie)
test("GET /api/admin/lead-growth (auth)", "get", t("/api/admin/lead-growth"), session=session)

# 9. Source breakdown (with auth cookie)
test("GET /api/admin/source-breakdown (auth)", "get", t("/api/admin/source-breakdown"), session=session)

# 10. Staff list (with auth cookie)
test("GET /api/admin/staff (auth)", "get", t("/api/admin/staff"), session=session)

print("\n=== Done ===")
