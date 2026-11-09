from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
FRONTEND = ROOT / "webapp" / "frontend"

sys.path.insert(0, str(BACKEND))
from app import app

client = app.test_client()

# 1) New logo path must be the one actually served.
r = client.get("/classic")
assert r.status_code == 200, r.data
html = r.data.decode("utf-8")
assert "harimaga-lanka-road-v8.svg" in html
assert "harimaga-ui-v8.css" in html
assert "harimaga-ui-v8.js" in html
assert "harimaga-logo.svg" not in html
print("PASS: v8 logo + cache-busted assets referenced")

r = client.get("/frontend/assets/harimaga-lanka-road-v8.svg")
assert r.status_code == 200
svg = r.data.decode("utf-8")
assert "golden guiding road" in svg
assert "#1FA7CB" in svg and "#2C7A52" in svg and "#7B263D" in svg
print("PASS: Sri Lanka + ocean + guiding-road logo served")

# 2) Service buttons must NEVER carry auto-submit prompts.
assert 'data-prompt=' not in html
assert 'data-category="water_issue"' in html
assert 'data-category="bus_complaint"' in html
assert 'data-fill="ape pare loku walak thyenawa"' in html
print("PASS: service/category clicks cannot contain canned auto-submit messages")

js = (FRONTEND / "harimaga-ui-v8.js").read_text(encoding="utf-8")
assert "fillButtons" in js
assert "input.value = example" in js
assert "await startRequest(prompt)" not in js
assert "categoryButtons.forEach" in js
print("PASS: examples fill composer only; category clicks select context only")

# 3) Professional UI assets + cache prevention.
r = client.get("/frontend/harimaga-ui-v8.css")
assert r.status_code == 200
assert "no-store" in client.get("/classic").headers.get("Cache-Control","")
assert "no-store" in r.headers.get("Cache-Control","")
css = r.data.decode("utf-8")
assert "--paddy-900:#164E3A" in css
assert "--ocean-700:#0C86AA" in css
assert "--maroon:#7B263D" in css
print("PASS: clean professional palette + no-cache frontend serving")

r = client.get("/api/health")
assert r.status_code == 200
d = r.get_json()
assert d["windows_evidence_delete_fix"] == "v7.2"
assert d["frontend_build"] == "clean-professional-v8"
print("PASS: v7.2 evidence backend preserved + v8 frontend active")

print("HARIMAGA CLEAN PROFESSIONAL v8: PASSED")
