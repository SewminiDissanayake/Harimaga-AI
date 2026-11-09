"""Flask API: routing flow, category hint, DS options, feedback, rate limits, React serving."""
import io


def route(client, text, answers=None, hint=None):
    body = {"text": text, "answers": answers or {}}
    if hint:
        body["category_hint"] = hint
    res = client.post("/api/route", json=body)
    assert res.status_code == 200
    return res.get_json()


def test_health(client):
    assert client.get("/api/health").get_json()["ok"] is True


def test_empty_text_rejected(client):
    assert client.post("/api/route", json={"text": ""}).status_code == 400


# Category hint ---------------------------------------------------------------

def test_hint_used_when_classifier_unsure(client):
    # A message that says nothing specific: the classifier cannot know the category
    assert route(client, "I need some help")["classification"]["label"] == "unknown_government_issue"
    assert route(client, "I need some help", hint="electricity_issue")["classification"]["label"] == "electricity_issue"


def test_confident_classifier_wins_over_hint(client):
    assert route(client, "para kadila loku walak", hint="water_issue")["classification"]["label"] == "road_issue"


def test_safety_hint_always_wins(client):
    assert route(client, "bus stop eke kenek", hint="women_child_safety")["classification"]["label"] == "women_child_safety"


def test_invalid_hint_ignored(client):
    assert route(client, "para kadila loku walak", hint="hacker")["classification"]["label"] == "road_issue"


# Clarification ---------------------------------------------------------------

def test_answer_not_understood(client):
    r = route(client, "apita wathura na", {"service_provider_or_scheme": "Kandy"})["routing"]
    assert r["previous_answer_not_understood"] is True
    assert "options below" in r["hint"]


def test_water_routes_to_nwsdb(client):
    r = route(client, "apita wathura na", {"service_provider_or_scheme": "NWSDB"})["routing"]
    assert r["status"] == "routed"
    assert "Water Supply" in r["authority_name"]


def test_ds_division_offered_as_options(client):
    r = route(client, "garbage collect karanne na", {"district": "Kandy"})["routing"]
    assert r["needed_field"] == "ds_division"
    assert len(r["options"]) >= 10
    chosen = r["options"][0]
    r2 = route(client, "garbage collect karanne na", {"district": "Kandy", "ds_division": chosen})["routing"]
    assert r2.get("needed_field") != "ds_division"


def test_complaint_draft(client):
    res = client.post("/api/complaint-draft", json={
        "text": "para kadila loku walak",
        "answers": {"road_type_or_class": "National / RDA road"},
    })
    body = res.get_json()["draft"]["body"]
    assert "Road Development Authority" in body


# Evidence --------------------------------------------------------------------

def test_evidence_upload_and_delete(client):
    rid = "hm_test_request_123456"
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    res = client.post("/api/evidence", data={
        "request_id": rid, "file": (io.BytesIO(png), "photo.png"),
    }, content_type="multipart/form-data")
    ev = res.get_json()["evidence"]
    assert ev["filename"] == "Photo evidence"          # original name never stored
    assert client.delete(f"/api/evidence/{ev['id']}", json={"request_id": rid}).get_json()["deleted"]


def test_evidence_rejects_other_file_types(client):
    res = client.post("/api/evidence", data={
        "request_id": "hm_test_request_123456", "file": (io.BytesIO(b"MZ"), "virus.exe"),
    }, content_type="multipart/form-data")
    assert res.status_code == 400


def test_evidence_needs_matching_request_id(client):
    rid = "hm_test_request_abcdef"
    res = client.post("/api/evidence", data={
        "request_id": rid, "file": (io.BytesIO(b"%PDF-1.4"), "doc.pdf"),
    }, content_type="multipart/form-data")
    eid = res.get_json()["evidence"]["id"]
    assert client.get(f"/api/evidence/{eid}?request_id=hm_someone_else_999").status_code == 404


# Feedback --------------------------------------------------------------------

def test_feedback_counts(client):
    client.post("/api/feedback", json={"issue_key": "road_issue", "helpful": True})
    client.post("/api/feedback", json={"issue_key": "road_issue", "helpful": False})
    rows = {r["issue_key"]: r for r in client.get("/api/feedback/summary").get_json()["categories"]}
    assert rows["road_issue"]["helpful"] >= 1 and rows["road_issue"]["not_helpful"] >= 1


def test_feedback_rejects_bad_input(client):
    assert client.post("/api/feedback", json={"issue_key": "<script>", "helpful": True}).status_code == 400
    assert client.post("/api/feedback", json={"issue_key": "road_issue", "helpful": "yes"}).status_code == 400


# Rate limit ------------------------------------------------------------------

def test_rate_limit(tmp_path):
    """Runs in a separate process, because the limiter must be on from startup."""
    import os, subprocess, sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    code = (
        "import sys, warnings; warnings.filterwarnings('ignore');"
        f"sys.path[:0] = [{str(root)!r}, {str(root / 'webapp' / 'backend')!r}];"
        "import app; c = app.app.test_client();"
        "codes = [c.post('/api/route', json={'text': ''}).status_code for _ in range(61)];"
        "print(codes[-1], codes[0])"
    )
    env = dict(os.environ, HARIMAGA_RATE_LIMIT="1", HARIMAGA_RUNTIME_DIR=str(tmp_path), PYTHONUTF8="1")
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert out.stdout.split() == ["429", "400"], out.stdout + out.stderr[-1000:]


# Frontend serving -------------------------------------------------------------

def test_classic_ui_still_available(client):
    assert client.get("/classic").status_code == 200


def test_no_path_traversal(client):
    assert client.get("/../requirements.txt").status_code == 404
    assert client.get("/%2e%2e/requirements.txt").status_code == 404
