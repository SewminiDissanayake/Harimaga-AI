from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.local_authority_issue_channel_service import LocalAuthorityIssueChannelService

service = LocalAuthorityIssueChannelService(ROOT)

colombo = service.find(
    "western__colombo__11__colombo_mc",
    "garbage_collection"
)
assert colombo is not None
assert colombo["verification_level"] == "verified_issue_specific_channel"

kandy = service.find(
    "central__kandy__11__kandy_mc",
    "garbage_collection"
)
assert kandy is not None
assert kandy["verification_level"] == "verified_issue_specific_channel"

moratuwa = service.find(
    "western__colombo__13__moratuwa_mc",
    "garbage_collection"
)
assert moratuwa is not None
assert moratuwa["verification_level"] == "verified_general_complaint_channel"

missing = service.find(
    "central__kandy__35__kundasale_ps",
    "garbage_collection"
)
assert missing is None

print("ISSUE-SPECIFIC CHANNEL PRIORITY SERVICE: PASSED")
