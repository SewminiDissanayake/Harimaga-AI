from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "webapp" / "backend"
sys.path.insert(0, str(BACKEND))

from app import app

client = app.test_client()


def post(text, answers=None):
    r = client.post(
        "/api/route",
        json={"text": text, "answers": answers or {}},
    )
    assert r.status_code == 200, (r.status_code, r.data)
    data = r.get_json()
    assert data["ok"] is True, data
    return data


# ------------------------------------------------------------
# Health
# ------------------------------------------------------------
r = client.get("/api/health")
assert r.status_code == 200
health = r.get_json()
assert health["status"] == "healthy"
assert health["specialized_services_loaded"] is True
assert health["api_phase"] == 2
print("PASS: health + specialized services")


# ------------------------------------------------------------
# Core routing
# ------------------------------------------------------------
data = post("ape pare loku walak thyenawa")
assert data["classification"]["label"] == "road_issue", data
assert data["routing"]["status"] in {"needs_clarification", "routed"}, data
print("PASS: core road routing")


# ------------------------------------------------------------
# Women / child safety
# ------------------------------------------------------------
data = post("mwa follow kranawa")
assert data["classification"]["label"] == "women_child_safety", data
assert data["routing"]["status"] == "needs_clarification", data
assert data["routing"]["needed_field"] == "safety_subtype", data

safety_options = data["routing"]["options"]
assert safety_options, data
safety_key = safety_options[0]["value"]

data = post(
    "mwa follow kranawa",
    {
        "safety_subtype": safety_key,
        "immediate_danger": False,
    },
)
assert data["routing"]["status"] == "routed", data
print("PASS: women/child safety API flow")


# ------------------------------------------------------------
# Disaster
# ------------------------------------------------------------
data = post("ape paththe flood wela")
assert data["classification"]["label"] == "disaster_alert", data
assert data["routing"]["status"] == "needs_clarification", data
assert data["routing"]["needed_field"] == "district", data

data = post(
    "ape paththe flood wela",
    {"district": "Matale"},
)
assert data["routing"]["status"] == "routed", data
print("PASS: disaster API flow")


# ------------------------------------------------------------
# Consumer
# ------------------------------------------------------------
data = post("shop eken broken item ekak dunna")
assert data["classification"]["label"] == "consumer_complaint", data
assert data["routing"]["status"] == "needs_clarification", data

consumer_options = data["routing"]["options"]
assert consumer_options, data
consumer_key = consumer_options[0]["value"]

data = post(
    "shop eken broken item ekak dunna",
    {
        "consumer_subtype": consumer_key,
        "district": "Matale",
    },
)
assert data["routing"]["status"] == "resolved", data
print("PASS: consumer API flow")


# ------------------------------------------------------------
# Lost document
# ------------------------------------------------------------
data = post("mage id ek nathi una")
assert data["classification"]["label"] == "lost_document", data
assert data["routing"]["status"] == "needs_clarification", data

doc_options = data["routing"]["options"]
assert doc_options, data
doc_key = doc_options[0]["value"]

data = post(
    "mage id ek nathi una",
    {
        "document_type": doc_key,
        "police_station_query": "skip",
    },
)
assert data["routing"]["status"] == "routed", data
print("PASS: lost-document API flow")


# ------------------------------------------------------------
# Bus
# ------------------------------------------------------------
data = post("bus conductor balance dunne na")
assert data["classification"]["label"] == "bus_complaint", data
assert data["routing"]["status"] == "needs_clarification", data
assert data["routing"]["needed_field"] == "bus_type", data

data = post(
    "bus conductor balance dunne na",
    {
        "bus_type": "private",
        "origin_district": "Matale",
        "destination_district": "Kandy",
    },
)
assert data["routing"]["status"] == "routed", data
print("PASS: bus jurisdiction API flow")


print("HARIMAGA FLASK BACKEND PHASE 2: PASSED")
