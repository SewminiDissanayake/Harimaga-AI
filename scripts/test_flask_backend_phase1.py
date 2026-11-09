from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
sys.path.insert(0, str(BACKEND))

from app import app

client = app.test_client()

# 1. Health
r = client.get("/api/health")
assert r.status_code == 200, r.data
data = r.get_json()
assert data["ok"] is True
assert data["status"] == "healthy"
print("PASS: /api/health")

# 2. Classification
r = client.post("/api/classify", json={"text": "mwa follow kranawa"})
assert r.status_code == 200, r.data
data = r.get_json()
assert data["ok"] is True
assert data["classification"]["label"] == "women_child_safety", data
print("PASS: /api/classify -> women_child_safety")

# 3. Core route can at least begin clarification/routing.
r = client.post(
    "/api/route",
    json={
        "text": "ape pare loku walak thyenawa",
        "answers": {}
    },
)
assert r.status_code == 200, r.data
data = r.get_json()
assert data["ok"] is True
assert data["classification"]["label"] == "road_issue", data
assert "routing" in data
print("PASS: /api/route -> road_issue")

# 4. Specialized flow is safely identified, not incorrectly sent
#    through the generic ComplaintRouter.
r = client.post(
    "/api/route",
    json={
        "text": "child abused",
        "answers": {}
    },
)
assert r.status_code == 200, r.data
data = r.get_json()
assert data["classification"]["label"] == "women_child_safety", data
assert data["routing"]["status"] == "specialized_flow_required", data
print("PASS: specialized flow guard")

print("HARIMAGA FLASK BACKEND PHASE 1: PASSED")
