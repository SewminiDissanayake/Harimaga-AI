from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

required_files = [
    "nlp/robust_issue_classifier.py",
    "services/complaint_router.py",
    "services/local_authority_contact_service.py",
    "services/local_authority_issue_channel_service.py",
    "services/provider_issue_channel_service.py",
    "services/bus_jurisdiction_service.py",
    "services/consumer_complaint_service.py",
    "services/lost_document_service.py",
    "services/police_station_contact_service.py",
    "services/women_child_safety_service.py",
    "services/disaster_alert_service.py",
    "data/routing/complaint_channels.json",
    "data/routing/routing_rules.json",
    "data/routing/required_fields.json",
    "data/routing/local_authority_issue_channels.json",
    "data/routing/provider_issue_channels.json",
    "data/routing/bus_jurisdiction.json",
    "data/routing/consumer_complaint_routes.json",
    "data/routing/lost_document_routes.json",
    "data/routing/women_child_safety_routes.json",
    "data/routing/disaster_alert_routes.json",
    "data/geography/ds_to_local_authorities.json",
    "data/geography/gnd_jurisdiction_lookup.json",
]

missing = [p for p in required_files if not (ROOT / p).exists()]

if missing:
    print("UNIFIED DEMO PREFLIGHT: FAILED")
    print("\nMissing files:")
    for p in missing:
        print(" -", p)
    raise SystemExit(1)

# Import check after file check.
from nlp.robust_issue_classifier import RobustIssueClassifier
from services.complaint_router import ComplaintRouter
from services.local_authority_contact_service import LocalAuthorityContactService
from services.local_authority_issue_channel_service import LocalAuthorityIssueChannelService
from services.provider_issue_channel_service import ProviderIssueChannelService
from services.bus_jurisdiction_service import BusJurisdictionService
from services.consumer_complaint_service import ConsumerComplaintService
from services.lost_document_service import LostDocumentService
from services.police_station_contact_service import PoliceStationContactService
from services.women_child_safety_service import WomenChildSafetyService
from services.disaster_alert_service import DisasterAlertService

# Instantiate services so JSON/data-path problems are caught before the demo.
RobustIssueClassifier()
ComplaintRouter(ROOT)
LocalAuthorityContactService(ROOT)
LocalAuthorityIssueChannelService(ROOT)
ProviderIssueChannelService(ROOT)
BusJurisdictionService(ROOT)
ConsumerComplaintService(ROOT)
LostDocumentService(ROOT)
PoliceStationContactService(ROOT)
WomenChildSafetyService(ROOT)
DisasterAlertService(ROOT)

print("UNIFIED DEMO PREFLIGHT: PASSED")
print("Run:")
print(r"  python -u scripts\demo_harimaga_unified_v1.py")
