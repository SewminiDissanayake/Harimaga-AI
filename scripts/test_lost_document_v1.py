from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.lost_document_service import LostDocumentService

clf = RobustIssueClassifier()

tests = [
    "mage ID card eka nathi una",
    "NIC eka nathi wela",
    "driving license eka hoyaganna ba",
    "license eka lost",
    "passport eka nathi una",
    "mage passport eka missing",
]

for text in tests:
    r = clf.predict(text)
    assert r["label"] == "lost_document", (text, r)
    print("PASS:", text, "->", r["label"], f"({r['method']})")

svc = LostDocumentService(ROOT)

nic = svc.resolve("national_identity_card")
assert nic["status"] == "resolved"
assert nic["document"]["authority"] == "Department for Registration of Persons"

lic = svc.resolve("driving_licence")
assert any("police complaint" in s.lower() for s in lic["document"]["steps"])

passport = svc.resolve("passport")
assert any(c["value"] == "011 2101533" for c in passport["document"]["contacts"])

print("LOST DOCUMENT + POLICE ENTRY ROUTING: PASSED")
