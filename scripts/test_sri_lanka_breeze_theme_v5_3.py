from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
sys.path.insert(0, str(BACKEND))

from app import app

client = app.test_client()

# backend remains stable
r = client.get("/api/health")
assert r.status_code == 200, r.data
d = r.get_json()
assert d["status"] == "healthy"
assert d["core_answer_normalization_fix"] is True
assert d["evidence_upload_fix"] == "v5.2"
print("PASS: backend functionality preserved")

# visual assets
r = client.get("/")
assert r.status_code == 200
assert b"HariMaga AI" in r.data
print("PASS: homepage")

r = client.get("/frontend/style.css")
assert r.status_code == 200
css = r.data.decode("utf-8")
assert "HariMaga Sri Lanka Breeze Theme v5.3" in css
assert "--sky-500" in css
assert "--maroon" in css
print("PASS: Sri Lanka Breeze theme loaded")

r = client.get("/frontend/assets/harimaga-logo.svg")
assert r.status_code == 200
svg = r.data.decode("utf-8")
assert "#8B2E47" in svg
assert "#5DB9E8" in svg
print("PASS: refreshed logo palette")

print("HARIMAGA SRI LANKA BREEZE THEME v5.3: PASSED")
