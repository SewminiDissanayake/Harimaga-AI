from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.issue_classifier import HybridIssueClassifier

classifier = HybridIssueClassifier()

tests = [
    "ape pare kunu aran yanne na",
    "current eka giya hours 3k",
    "pare loku walak thiyenawa",
    "water pipe eka leak wenawa",
    "bus conductor ticket ekak dunne na",
    "shop eken gatta item eka defective",
    "factory eken chemical waste river ekata danawa",
    "mage passport eka delay wela",
    "me problem eka kohetada kiyanna oni danne na",
    "අපේ පාරේ කුණු අරන් යන්නේ නැහැ",
    "මගේ පාස්පෝට් එක තාම ආවේ නැහැ",
]

for text in tests:
    result = classifier.predict(text)
    print("\nTEXT:", text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
