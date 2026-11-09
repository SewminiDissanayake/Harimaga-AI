from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
sys.path.insert(0, str(BACKEND))

from app import app

client = app.test_client()

r = client.get("/")
assert r.status_code == 200, r.data
assert b"HariMaga AI" in r.data
assert b"harimaga-logo.svg" in r.data
print("PASS: premium homepage")

for path in [
    "/frontend/style.css",
    "/frontend/app.js",
    "/frontend/assets/harimaga-logo.svg",
]:
    r = client.get(path)
    assert r.status_code == 200, (path, r.status_code)
print("PASS: premium frontend assets")

r = client.get("/api/health")
assert r.status_code == 200
d = r.get_json()
assert d["status"] == "healthy"
assert d["frontend_loaded"] is True
print("PASS: backend health")

# Safety flow
r = client.post("/api/route", json={"text":"mwa follow kranawa","answers":{}})
assert r.status_code == 200
d = r.get_json()
assert d["classification"]["label"] == "women_child_safety", d
assert d["routing"]["status"] == "needs_clarification", d
print("PASS: safety routing preserved")

# Disaster flow
r = client.post("/api/route", json={"text":"ape paththe flood wela","answers":{"district":"Matale"}})
assert r.status_code == 200
d = r.get_json()
assert d["classification"]["label"] == "disaster_alert", d
assert d["routing"]["status"] in {"routed","resolved"}, d
print("PASS: disaster routing preserved")

print("HARIMAGA PREMIUM FRONTEND PHASE 4: PASSED")
