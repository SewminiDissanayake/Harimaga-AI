from pathlib import Path
import io
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
sys.path.insert(0, str(BACKEND))

from app import app, EVIDENCE_DB

client = app.test_client()

r = client.get("/api/health")
assert r.status_code == 200, r.data
d = r.get_json()
assert d["evidence_storage"] == "anonymous_sqlite_ttl_24h", d
assert d["conversation_persistence"] is False
assert d["identity_profile_storage"] is False
print("PASS: privacy storage mode")

request_id = "hm_testrequest_123456789"

fake_jpg = b"\xff\xd8\xff\xe0" + b"0" * 100 + b"\xff\xd9"

r = client.post(
    "/api/evidence",
    data={
        "request_id": request_id,
        "file": (io.BytesIO(fake_jpg), "my_private_filename.jpg", "image/jpeg"),
        "privacy_processed": "true",
    },
    content_type="multipart/form-data",
)
assert r.status_code == 200, r.data
d = r.get_json()
assert d["ok"] is True
eid = d["evidence"]["id"]
assert d["evidence"]["filename"] == "Photo evidence"
print("PASS: evidence attached anonymously")

with sqlite3.connect(EVIDENCE_DB) as conn:
    cols = [
        row[1]
        for row in conn.execute("PRAGMA table_info(evidence)").fetchall()
    ]
    assert "original_filename" not in cols
    assert "name" not in cols
    assert "email" not in cols
    assert "phone" not in cols
print("PASS: no identity/profile columns")

r = client.get(f"/api/evidence/request/{request_id}")
assert r.status_code == 200
assert len(r.get_json()["evidence"]) >= 1
print("PASS: request evidence restored from DB")

r = client.get(
    f"/api/evidence/{eid}?request_id={request_id}",
    buffered=True,
)
assert r.status_code == 200
_ = r.data
r.close()  # Important on Windows: release send_file() handle before DELETE.
print("PASS: evidence preview + response handle released")

r = client.delete(
    f"/api/evidence/{eid}",
    json={"request_id": request_id},
)
assert r.status_code == 200
d = r.get_json()
assert d["ok"] is True
assert d["deleted"] is True or d.get("delete_pending") is True
print("PASS: evidence delete / Windows-safe pending cleanup")

r = client.get("/api/health")
assert r.get_json()["windows_evidence_delete_fix"] == "v7.2"
print("PASS: v7.2 Windows evidence-delete fix active")

print("HARIMAGA WINDOWS EVIDENCE DELETE FIX v7.2: PASSED")
