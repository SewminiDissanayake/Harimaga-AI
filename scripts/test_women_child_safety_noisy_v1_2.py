from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier

clf = RobustIssueClassifier()

tests = [
    "mt ehapththe ekkena mawa follow kranawa",
    "mwa follow kranawa",
    "mwa follow karanawa",
    "mawa kenek follow karanawa",
    "manussyek kradara kranawa",
    "manussyek karadara karanawa",
    "sexual harrashment",
    "sexual harassment",
    "child abused",
    "child abuse",
    "lamayekta karadara karanawa",
]

for text in tests:
    r = clf.predict(text)
    assert r["label"] == "women_child_safety", (text, r)
    print("PASS:", text, "->", r["label"], f"({r['method']})")

# Regression guards
assert clf.predict("mage id ek nathi una")["label"] == "lost_document"
assert clf.predict("passport eka delay wela")["label"] == "immigration_issue"
assert clf.predict("karant eka giya")["label"] == "electricity_issue"
assert clf.predict("ape pare lokuu walak thyenwa. wassata mada pirenawa")["label"] == "road_issue"

print("WOMEN/CHILD SAFETY NOISY-SINGLISH FIX v1.2: PASSED")
