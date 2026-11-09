from pathlib import Path
import io
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
sys.path.insert(0, str(BACKEND))

from app import app

client = app.test_client()

# Health
r = client.get("/api/health")
assert r.status_code == 200, r.data
d = r.get_json()
assert d["status"] == "healthy"
assert d["api_phase"] == 5
assert d["evidence_upload_enabled"] is True
assert d["complaint_draft_enabled"] is True
print("PASS: Phase 5 health")

# Minimal 1x1 PNG bytes
png = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd9\x89\xe8"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

r = client.post(
    "/api/evidence",
    data={
        "file": (io.BytesIO(png), "road_photo.png"),
        "privacy_processed": "true",
    },
    content_type="multipart/form-data",
)
assert r.status_code == 200, r.data
d = r.get_json()
assert d["ok"] is True
eid = d["evidence"]["id"]
assert d["evidence"]["privacy_processed"] is True
print("PASS: evidence upload")

r = client.get(f"/api/evidence/{eid}")
assert r.status_code == 200
print("PASS: evidence preview")

# Complaint draft with a flow known to complete in the existing project.
# Women/child safety is used because its answers are stable and non-geographic.
r = client.post(
    "/api/complaint-draft",
    json={
        "text": "mwa follow kranawa",
        "answers": {
            "safety_subtype": "stalking_or_following",
            "immediate_danger": False,
        },
        "evidence_ids": [eid],
    },
)
assert r.status_code == 200, r.data
d = r.get_json()
assert d["ok"] is True
assert "road_photo.png" in d["draft"]["body"]
assert d["draft"]["subject"]
print("PASS: complaint draft")

r = client.delete(f"/api/evidence/{eid}")
assert r.status_code == 200
assert r.get_json()["deleted"] is True
print("PASS: evidence delete")

# Static frontend
for path in [
    "/",
    "/frontend/style.css",
    "/frontend/app.js",
    "/frontend/assets/harimaga-logo.svg",
]:
    r = client.get(path)
    assert r.status_code == 200, (path, r.status_code)
print("PASS: frontend assets")

print("HARIMAGA EVIDENCE + PORTAL PHASE 5: PASSED")
