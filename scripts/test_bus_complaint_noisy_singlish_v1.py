from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.provider_issue_channel_service import ProviderIssueChannelService

clf = RobustIssueClassifier()

bus_tests = [
    "bus eka enne na",
    "ape bus eka wada karanne na",
    "bus eka nawaththanne na",
    "bus eke ticket dunne na",
    "bus conductor balance dunne na",
    "bus driver dangerous widihata drive karanawa",
    "bus eka godak late",
]

for text in bus_tests:
    result = clf.predict(text)
    assert result["label"] == "bus_complaint", (text, result)
    print(f"PASS: {text} -> {result['label']} ({result['method']})")

# Regression checks for previous fixes.
assert clf.predict("karant eka giya")["label"] == "electricity_issue"
assert clf.predict("ape pare lokuu walak thyenwa. wassata mada pirenawa")["label"] == "road_issue"

service = ProviderIssueChannelService(ROOT)
ntc = service.find("National Transport Commission", "bus_complaint")
assert ntc is not None
assert ntc["verification_level"] == "verified_issue_specific_channel"

values = {c["value"] for c in ntc["channels"]}
assert "1955" in values
assert "https://cms.ntc.gov.lk/complaint" in values

print("BUS COMPLAINT + NOISY SINGLISH TESTS: PASSED")
