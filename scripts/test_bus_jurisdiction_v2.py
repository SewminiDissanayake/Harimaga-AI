from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.bus_jurisdiction_service import BusJurisdictionService
from services.provider_issue_channel_service import ProviderIssueChannelService

bus = BusJurisdictionService(ROOT)
channels = ProviderIssueChannelService(ROOT)

# Intra-provincial private: Matale -> Kandy = Central Province
r = bus.resolve_private("Matale", "Kandy")
assert r["authority_name"] == "Central Province Transport Services Authority", r
assert r["jurisdiction"] == "intra_provincial_private", r

# Inter-provincial private: Matale -> Colombo = NTC
r = bus.resolve_private("Matale", "Colombo")
assert r["authority_name"] == "National Transport Commission", r
assert r["jurisdiction"] == "inter_provincial_private", r

# Western intra-provincial
r = bus.resolve_private("Colombo", "Kalutara")
assert r["authority_name"] == "Road Passenger Transport Authority-Western Province", r

# SLTB incident in Matale => Kandy regional WhatsApp
r = bus.resolve_sltb("Matale")
assert r["authority_name"] == "Sri Lanka Transport Board", r
assert r["regional_sltb"]["whatsapp"] == "070 477 5039", r

# Unknown operator => NTC verified intake
r = bus.resolve_unknown("Jaffna")
assert r["authority_name"] == "National Transport Commission", r

# Channel records
assert channels.find("Central Province Transport Services Authority", "bus_complaint") is not None
assert channels.find("Sri Lanka Transport Board", "bus_complaint") is not None
assert channels.find("Road Passenger Transport Authority-Western Province", "bus_complaint") is not None

print("BUS JURISDICTION + DISTRICT/PROVINCE ROUTING: PASSED")
