"""HariMaga v9.1: category hint tests.  Run: python scripts/test_category_hint_v9_1.py"""
from pathlib import Path
import sys, warnings
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "webapp" / "backend"))
import app as harimaga

c = harimaga.app.test_client()

def label(text, hint=None):
    body = {"text": text, "answers": {}}
    if hint: body["category_hint"] = hint
    return c.post("/api/route", json=body).get_json()["classification"]["label"]

# Unsure text + hint -> hint wins
assert label("I need some help") == "unknown_government_issue"
assert label("I need some help", "electricity_issue") == "electricity_issue"
# Confident classifier keeps its answer
assert label("para kadila loku walak", "water_issue") == "road_issue"
# Safety hint always wins
assert label("bus stop eke kenek", "women_child_safety") == "women_child_safety"
# Invalid hint is ignored
assert label("para kadila loku walak", "hacker") == "road_issue"
# No hint -> same as before
assert label("apita wathura na dawas 3k") == "water_issue"
print("category hint tests: all passed")
