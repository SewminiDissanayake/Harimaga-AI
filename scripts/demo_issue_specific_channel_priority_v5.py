from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.complaint_router import ComplaintRouter
from services.local_authority_contact_service import LocalAuthorityContactService
from services.local_authority_issue_channel_service import LocalAuthorityIssueChannelService
from services.provider_issue_channel_service import ProviderIssueChannelService
from services.bus_jurisdiction_service import BusJurisdictionService


def ask_choice(question, options):
    print("\n" + question)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    raw = input("> ").strip()
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    return raw


def print_channels(record):
    level = record.get("verification_level")

    if level == "verified_issue_specific_channel":
        print("\nVerified complaint route:")
    elif level == "verified_authority_contact":
        print("\nVerified responsible authority contact:")
        print("Note: a dedicated current complaint channel was not separately verified.")
    else:
        print("\nVerified authority route:")

    for ch in record.get("channels", []):
        print(f" - {ch.get('label')}: {ch.get('value')}")

    if record.get("guidance"):
        print("\nGuidance:", record["guidance"])


def print_ntc_fallback(provider_channels):
    ntc = provider_channels.find("National Transport Commission", "bus_complaint")
    if ntc:
        print("\nVerified NTC intake fallback:")
        for ch in ntc.get("channels", []):
            if ch.get("type") in {"hotline", "complaint_portal"}:
                print(f" - {ch.get('label')}: {ch.get('value')}")


def handle_bus(provider_channels, bus_jurisdiction):
    service = ask_choice(
        "What type of bus was it?",
        ["SLTB", "Private bus", "Not sure"]
    ).strip().lower()

    if service in {"sltb", "1"}:
        district = input("\nIn which district did the incident happen?\n> ").strip()
        resolved = bus_jurisdiction.resolve_sltb(district)

    elif service in {"private bus", "private", "2"}:
        origin = input("\nWhich district does this bus route start from?\n> ").strip()
        destination = input("\nWhich district does this bus route go to / end in?\n> ").strip()
        resolved = bus_jurisdiction.resolve_private(origin, destination)

    else:
        district = input("\nIn which district did the incident happen?\n> ").strip()
        resolved = bus_jurisdiction.resolve_unknown(district)

    if resolved.get("status") != "resolved":
        print("\nI couldn't match that district safely.")
        print("Please enter an official Sri Lankan district name, e.g. Matale, Kandy, Colombo.")
        return

    print("\n" + "=" * 70)
    print("HariMaga bus jurisdiction result")
    print("=" * 70)
    print("Jurisdiction :", resolved.get("jurisdiction"))
    print("Authority    :", resolved.get("authority_name"))

    if resolved.get("origin_district"):
        print("Route        :", resolved["origin_district"], "->", resolved["destination_district"])
        print("Province(s)  :", resolved["origin_province"], "->", resolved["destination_province"])
    else:
        print("District     :", resolved.get("incident_district"))
        print("Province     :", resolved.get("incident_province"))

    print("Why          :", resolved.get("reason"))

    record = provider_channels.find(resolved["authority_name"], "bus_complaint")

    if record:
        print_channels(record)
    else:
        print("\nNo stored verified channel was found for this authority.")
        print("HariMaga will not invent a contact.")

    regional = resolved.get("regional_sltb")
    if regional:
        print("\nSLTB regional complaint/support WhatsApp:")
        print(f" - {regional['region']} region: {regional['whatsapp']}")

    # For provincial authorities where only a general authority contact is verified,
    # also expose NTC's verified intake route.
    if record and record.get("verification_level") == "verified_authority_contact":
        print_ntc_fallback(provider_channels)

    print("\nUseful information to prepare:")
    for item in [
        "bus_number_or_registration",
        "route_number_or_route_name",
        "date_and_time",
        "exact_incident_location",
        "what_happened",
        "ticket_or_fare_details_if_relevant",
        "photo_or_video_if_available",
    ]:
        print(" -", item)


def ask_for_value(result):
    field = result.get("needed_field", "extra_info")
    options = result.get("options") or []
    print("\nHariMaga needs one more detail:")
    print(result.get("question", "Please provide more information:"))
    if options:
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        raw = input("> ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return field, options[idx]
        return field, raw
    return field, input("> ").strip()


def normalize_answer(field, value):
    value = value.strip()
    low = value.lower()
    if field == "electricity_provider":
        if "ceb" in low: return "CEB"
        if "leco" in low: return "LECO"
    if field == "service_provider_or_scheme":
        if "nwsdb" in low or "water board" in low: return "NWSDB"
    if field == "road_type_or_class":
        if "national" in low or "rda" in low: return "national road"
        if "local" in low or "council" in low: return "local road"
    return value


def main():
    classifier = RobustIssueClassifier()
    router = ComplaintRouter(ROOT)
    local_channels = LocalAuthorityIssueChannelService(ROOT)
    directory_contacts = LocalAuthorityContactService(ROOT)
    provider_channels = ProviderIssueChannelService(ROOT)
    bus_jurisdiction = BusJurisdictionService(ROOT)

    print("=" * 70)
    print("HariMaga AI - Complaint Channel Priority Demo v5")
    print("=" * 70)

    problem = input("Describe your problem: ").strip()
    classification = classifier.predict(problem)
    issue_key = classification["label"]

    print("\nDetected issue :", issue_key)
    print("Confidence     :", round(classification["confidence"], 3))
    print("Method         :", classification["method"])

    if issue_key == "bus_complaint":
        handle_bus(provider_channels, bus_jurisdiction)
        return

    # Existing non-bus flow remains unchanged.
    answers = {}
    for _ in range(8):
        result = router.route(issue_key, answers)

        if result.get("status") == "needs_clarification":
            field, value = ask_for_value(result)
            answers[field] = normalize_answer(field, value)
            continue

        if result.get("status") != "routed":
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        print("\n" + "=" * 70)
        print("HariMaga result")
        print("=" * 70)
        print("Issue      :", result.get("issue_key"))
        print("Route type :", result.get("route_type"))

        la = result.get("local_authority")
        if la:
            print("Authority  :", la.get("name"))
            gid = la.get("id") or la.get("geography_id")
            verified = local_channels.find(gid, issue_key)
            if verified:
                print_channels(verified)
            else:
                contact = directory_contacts.find(la)
                print("\nOfficial council contact (fallback):")
                if not contact:
                    print(" - No verified directory contact is available.")
                    print(" - HariMaga will not invent a contact.")
                else:
                    if contact.get("phones"): print(" Phone :", ", ".join(contact["phones"]))
                    if contact.get("emails"): print(" Email :", ", ".join(contact["emails"]))
        else:
            authority_name = result.get("authority_name") or result.get("authority") or result.get("provider")
            if authority_name:
                print("Authority  :", authority_name)
                verified = provider_channels.find(authority_name, issue_key)
                if verified:
                    print_channels(verified)

        if result.get("required_information"):
            print("\nUseful information to prepare:")
            for item in result["required_information"]:
                print(" -", item)
        return


if __name__ == "__main__":
    main()
