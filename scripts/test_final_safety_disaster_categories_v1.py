from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.women_child_safety_service import WomenChildSafetyService
from services.disaster_alert_service import DisasterAlertService

clf = RobustIssueClassifier()

safety_tests = [
    "mawa follow karanawa",
    "pare kenek mawa harass karanawa",
    "lamayekta karadara karanawa",
    "child abuse ekak gana complain karanna oni",
]

for text in safety_tests:
    r = clf.predict(text)
    assert r["label"] == "women_child_safety", (text, r)
    print("PASS:", text, "->", r["label"])

flood_tests = [
    "ape paththe flood wela",
    "ganga pita dala",
    "wathurata yata wela",
]

for text in flood_tests:
    r = clf.predict(text)
    assert r["label"] == "disaster_alert", (text, r)
    assert r.get("disaster_subtype") == "flood_alert", (text, r)
    print("PASS:", text, "-> flood_alert")

landslide_tests = [
    "ape paththe landslide warning ekak thiyenawada",
    "pas kanda bihinawa",
    "naaya yanna wage",
]

for text in landslide_tests:
    r = clf.predict(text)
    assert r["label"] == "disaster_alert", (text, r)
    assert r.get("disaster_subtype") == "landslide_alert", (text, r)
    print("PASS:", text, "-> landslide_alert")

# Regression guards for previous work
assert clf.predict("mage id ek nathi una")["label"] == "lost_document"
assert clf.predict("passport eka delay wela")["label"] == "immigration_issue"
assert clf.predict("karant eka giya")["label"] == "electricity_issue"
assert clf.predict("ape pare lokuu walak thyenwa. wassata mada pirenawa")["label"] == "road_issue"

safety = WomenChildSafetyService(ROOT)
r = safety.resolve("child_abuse_neglect_or_exploitation", True)
phones = {c.get("phone") for c in r["contacts"]}
assert "119" in phones
assert "109" in phones
assert "1929" in phones

disaster = DisasterAlertService(ROOT)
r = disaster.resolve("flood_alert", "Matale")
assert r["status"] == "resolved"
assert any(c["phone"] == "117" for c in r["dmc_contacts"])

print("FINAL SAFETY + DISASTER CATEGORY TESTS: PASSED")
