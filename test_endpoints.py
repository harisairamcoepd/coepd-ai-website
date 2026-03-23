"""Quick endpoint test script - run with server already started."""
import json
import sys

import requests

BASE = "http://127.0.0.1:8000"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def test(label, method, url, session=None, **kwargs):
    print(f"\n=== {label} ===")
    try:
        client = session or requests
        response = getattr(client, method)(url, timeout=5, **kwargs)
        print(f"Status: {response.status_code}")
        try:
            print(f"Body: {json.dumps(response.json(), indent=2)[:400]}")
        except Exception:
            print(f"Body: {response.text[:400]}")
    except Exception as exc:
        print(f"Error: {exc}")


# 1. Health check
test("GET /", "get", f"{BASE}/")

# 2. Public lead submission
test("POST /api/leads", "post", f"{BASE}/api/leads", json={
    "name": "Hari",
    "phone": "7337212474",
    "email": "hari@gmail.com",
    "location": "Hyderabad",
    "interested_domain": "Business Analyst",
    "whatsapp": "7337212474",
    "source": "chatbot",
})

# 3. Public lead list
test("GET /api/leads", "get", f"{BASE}/api/leads")

# 4. Staff login
test("POST /api/staff/login", "post", f"{BASE}/api/staff/login", json={
    "email": "admin",
    "password": "admin",
})

# 5. Admin login (returns cookie for subsequent requests)
session = requests.Session()
print("\n=== POST /api/admin/login (session) ===")
try:
    login_response = session.post(
        f"{BASE}/api/admin/login",
        json={"email": "admin", "password": "admin"},
        timeout=5,
    )
    print(f"Status: {login_response.status_code}")
    print(f"Body: {json.dumps(login_response.json(), indent=2)[:400]}")
except Exception as exc:
    print(f"Error: {exc}")

# 6. Admin leads (with auth cookie)
test("GET /api/admin/leads (auth)", "get", f"{BASE}/api/admin/leads", session=session)

# 7. Admin stats
test("GET /api/admin/stats (no auth)", "get", f"{BASE}/api/admin/stats")

# 8. Lead growth
test("GET /api/admin/lead-growth (no auth)", "get", f"{BASE}/api/admin/lead-growth")

# 9. Source breakdown
test("GET /api/admin/source-breakdown (no auth)", "get", f"{BASE}/api/admin/source-breakdown")

# 10. Staff list
test("GET /api/admin/staff (no auth)", "get", f"{BASE}/api/admin/staff")

print("\n=== Done ===")
