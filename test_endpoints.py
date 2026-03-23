"""Quick endpoint test script — run with server already started."""
import requests
import json

BASE = "http://127.0.0.1:8000"


def test(label, method, url, **kwargs):
    print(f"\n=== {label} ===")
    try:
        r = getattr(requests, method)(url, timeout=5, **kwargs)
        print(f"Status: {r.status_code}")
        try:
            print(f"Body: {json.dumps(r.json(), indent=2)[:400]}")
        except Exception:
            print(f"Body: {r.text[:400]}")
    except Exception as e:
        print(f"Error: {e}")


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
test("POST /api/staff/login", "post", f"{BASE}/api/staff/login",
     json={"email": "admin", "password": "admin"})

# 5. Admin login (returns cookie for subsequent requests)
session = requests.Session()
print("\n=== POST /api/admin/login (session) ===")
try:
    r = session.post(f"{BASE}/api/admin/login",
                     json={"email": "admin", "password": "admin"}, timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Body: {json.dumps(r.json(), indent=2)[:400]}")
except Exception as e:
    print(f"Error: {e}")

# 6. Admin leads (with auth cookie)
test("GET /api/admin/leads (auth)", "get", f"{BASE}/api/admin/leads")

# 7. Admin stats
test("GET /api/admin/stats (no auth)", "get", f"{BASE}/api/admin/stats")

# 8. Lead growth
test("GET /api/admin/lead-growth (no auth)", "get", f"{BASE}/api/admin/lead-growth")

# 9. Source breakdown
test("GET /api/admin/source-breakdown (no auth)", "get", f"{BASE}/api/admin/source-breakdown")

# 10. Staff list
test("GET /api/admin/staff (no auth)", "get", f"{BASE}/api/admin/staff")

print("\n=== Done ===")
