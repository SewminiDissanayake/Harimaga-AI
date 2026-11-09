"""
HariMaga v9 classifier regression tests.

Run:  python scripts/test_classifier_fixes_v9.py
"""
from pathlib import Path
import sys
import warnings

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier

c = RobustIssueClassifier()

CASES = [
    # --- Bugs that were fixed (previously wrong) ---
    ("There is a flood threat in Ratnapura", "disaster_alert"),
    ("Someone is threatening to cut down trees near the river", "!women_child_safety"),
    ("වැස්ස ගහනවා පාරේ වතුර", "!women_child_safety"),
    ("kade eka business eka wahala", "!bus_complaint"),
    ("neighbour is burning plastic every night", "environment_issue"),
    ("ගෙදර ළඟ කුණු පුළුස්සනවා", "environment_issue"),
    ("is it advisable to complain about water supply", "water_issue"),

    # --- Safety must still be caught ---
    ("someone is threatening me every day", "women_child_safety"),
    ("my husband threatened to kill me", "women_child_safety"),
    ("mata kenek follow karanawa", "women_child_safety"),
    ("ළමයාට ගහනවා", "women_child_safety"),
    ("lamayata gahanawa", "women_child_safety"),
    ("child abuse in our area", "women_child_safety"),
    ("sexual harassment at bus stop", "women_child_safety"),

    # --- Other categories still work ---
    ("bus eke conductor balance dunne na", "bus_complaint"),
    ("para kadila loku walak", "road_issue"),
    ("apita wathura na dawas 3k", "water_issue"),
    ("current eka na", "electricity_issue"),
    ("I lost my passport", "lost_document"),
    ("garbage collect karanne na sathi dekak", "garbage_collection"),
    ("landslide warning in Badulla", "disaster_alert"),
]

failures = 0
for text, expected in CASES:
    label = c.predict(text)["label"]
    if expected.startswith("!"):
        ok = label != expected[1:]
    else:
        ok = label == expected
    mark = "PASS" if ok else "FAIL"
    if not ok:
        failures += 1
    print(f"{mark}  {label:26} expected {expected:26} | {text}")

print()
print(f"{len(CASES) - failures}/{len(CASES)} passed")
assert failures == 0
