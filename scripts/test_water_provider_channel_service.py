from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.provider_issue_channel_service import ProviderIssueChannelService

service = ProviderIssueChannelService(ROOT)

for name in [
    "NWSDB",
    "National Water Supply and Drainage Board",
    "Water Board",
]:
    r = service.find(name, "water_issue")
    assert r is not None, name
    assert r["verification_level"] == "verified_issue_specific_channel"

assert service.find("CEB", "water_issue") is None

print("WATER PROVIDER CHANNEL SERVICE: PASSED")
