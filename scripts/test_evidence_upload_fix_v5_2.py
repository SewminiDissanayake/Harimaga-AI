from pathlib import Path
import io
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
sys.path.insert(0, str(BACKEND))

from app import app

client = app.test_client()

r = client.get("/api/health")
assert r.status_code == 200
d = r.get_json()
assert d["evidence_upload_fix"] == "v5.2", d
assert d["core_answer_normalization_fix"] is True, d
print("PASS: v5.2 backend loaded")

# Standard JPG-like upload with generic Windows MIME.
fake_jpg = b"\xff\xd8\xff\xe0" + b"0" * 100 + b"\xff\xd9"
r = client.post(
    "/api/evidence",
    data={
        "file": (io.BytesIO(fake_jpg), "evidence.jpg", "application/octet-stream"),
        "privacy_processed": "false",
    },
    content_type="multipart/form-data",
)
assert r.status_code == 200, r.data
d = r.get_json()
assert d["ok"] is True
assert d["evidence"]["mime_type"] == "image/jpeg"
eid = d["evidence"]["id"]
print("PASS: JPG with generic browser MIME accepted")

r = client.delete(f"/api/evidence/{eid}")
assert r.status_code == 200
print("PASS: evidence cleanup")

r = client.get("/")
assert r.status_code == 200
assert b"Add photo / PDF evidence" in r.data
print("PASS: explicit evidence button visible")

print("HARIMAGA EVIDENCE UPLOAD FIX v5.2: PASSED")
