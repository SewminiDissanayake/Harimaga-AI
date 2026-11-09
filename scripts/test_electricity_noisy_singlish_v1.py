from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.provider_issue_channel_service import ProviderIssueChannelService

clf = RobustIssueClassifier()

tests = [
    "apit current na",
    "apita current naha",
    "apiṭa current nae",
    "gedara light na",
    "apita light ne",
    "ape paththe current na",
    "karant eka giya",
    "power na",
]

for text in tests:
    result = clf.predict(text)
    assert result["label"] == "electricity_issue", (text, result)

# Don't force an obvious street-light phrase into household/provider electricity.
street = clf.predict("ape pare light na")
assert not (
    street.get("label") == "electricity_issue"
    and street.get("method") == "high_precision_electricity_rule_v2"
), street

provider = ProviderIssueChannelService(ROOT)

ceb = provider.find("CEB", "electricity_issue")
assert ceb is not None
assert ceb["channels"][0]["value"] == "1987"

leco = provider.find("LECO", "electricity_issue")
assert leco is not None
assert leco["channels"][0]["value"] == "1910"

print("ELECTRICITY PROVIDER + NOISY SINGLISH TESTS: PASSED")
