from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier

clf = RobustIssueClassifier()

lost_tests = [
    "mage id ek nathi una",
    "mage id eka nathi una",
    "id eka missing",
    "my id lost",
    "mage ID card eka nathi una",
    "NIC eka nathi wela",
    "driving license eka hoyaganna ba",
    "license eka lost",
    "passport eka nathi una",
    "mage passport eka missing",
]

for text in lost_tests:
    r = clf.predict(text)
    assert r["label"] == "lost_document", (text, r)
    print("PASS:", text, "->", r["label"], f"({r['method']})")

# Regression guards
assert clf.predict("passport eka delay wela")["label"] == "immigration_issue"
assert clf.predict("karant eka giya")["label"] == "electricity_issue"
assert clf.predict("ape pare lokuu walak thyenwa. wassata mada pirenawa")["label"] == "road_issue"

print("LOST DOCUMENT ID SHORT-FORM FIX: PASSED")
