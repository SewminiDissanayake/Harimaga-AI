from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.local_authority_issue_channel_service import LocalAuthorityIssueChannelService

clf = RobustIssueClassifier()

x = clf.predict("ape pare lokuu walak thyenwa. wassata mada pirenawa")
assert x["label"] == "road_issue", x

service = LocalAuthorityIssueChannelService(ROOT)
ukuwela = service.find("central__matale__39__ukuwela_ps", "road_issue")
assert ukuwela is not None
assert ukuwela["verification_level"] == "verified_general_complaint_channel"

print("ROAD ROBUSTNESS + UKUWELA CHANNEL: PASSED")
