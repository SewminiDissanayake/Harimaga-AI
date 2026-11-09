from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.consumer_complaint_service import ConsumerComplaintService

clf = RobustIssueClassifier()

tests = [
    "kade price eka wadi ganak gaththa",
    "shop eken broken item ekak dunna",
    "warranty eka accept karanne na",
    "refund denne na",
    "expired badu sell karanawa",
    "online order eka awe na",
]

for text in tests:
    r = clf.predict(text)
    assert r["label"] == "consumer_complaint", (text, r)
    print("PASS:", text, "->", r["label"], f"({r['method']})")

svc = ConsumerComplaintService(ROOT)
r = svc.resolve("Matale", "defective_product_or_warranty")
assert r["status"] == "resolved"
assert r["district_office"]["telephone"] == "+94 66 2230959"

r = svc.resolve("Colombo", "overpricing_or_price_display")
assert r["status"] == "resolved"
assert r["authority"]["hotline"] == "1977"

print("CONSUMER COMPLAINT + DISTRICT ROUTING: PASSED")
