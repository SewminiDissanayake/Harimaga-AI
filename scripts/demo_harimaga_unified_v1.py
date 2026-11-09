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
from services.consumer_complaint_service import ConsumerComplaintService
from services.lost_document_service import LostDocumentService
from services.police_station_contact_service import PoliceStationContactService
from services.women_child_safety_service import WomenChildSafetyService
from services.disaster_alert_service import DisasterAlertService


# ---------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------

def line():
    print("=" * 72)


def ask_choice(question, options):
    """
    options can be:
      ["A", "B"]
    or
      [("key_a", "Label A"), ("key_b", "Label B")]
    Returns the selected string/key.
    """
    print("\n" + question)

    pair_mode = bool(options and isinstance(options[0], (tuple, list)))

    for i, option in enumerate(options, 1):
        label = option[1] if pair_mode else option
        print(f"  {i}. {label}")

    raw = input("> ").strip()

    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx][0] if pair_mode else options[idx]

    # Allow typed key/label.
    if pair_mode:
        low = raw.lower()
        for key, label in options:
            if low == str(key).lower() or low == str(label).lower():
                return key

    return raw


def ask_yes_no(question):
    raw = input("\n" + question + "\n> ").strip().lower()
    return raw in {"y", "yes", "ow", "1", "true"}


def print_channels(record, title=None):
    if not record:
        return

    if title:
        print("\n" + title)
    else:
        level = record.get("verification_level")
        if level == "verified_issue_specific_channel":
            print("\nVerified complaint route:")
        elif level == "verified_general_complaint_channel":
            print("\nVerified general complaint route:")
            print("Note: this is not necessarily a dedicated issue-specific hotline.")
        elif level == "verified_authority_contact":
            print("\nVerified responsible authority contact:")
            print("Note: a dedicated current complaint channel was not separately verified.")
        else:
            print("\nVerified authority route:")

    for ch in record.get("channels", []):
        label = ch.get("label") or ch.get("type") or "Channel"
        value = ch.get("value")
        if value:
            print(f" - {label}: {value}")

    if record.get("guidance"):
        print("\nGuidance:", record["guidance"])


def print_router_channels(result):
    channels = result.get("channels") or []
    if not channels:
        return

    print("\nOfficial channels:")
    for ch in channels:
        label = ch.get("label") or ch.get("type") or "Channel"
        value = ch.get("value")
        purpose = ch.get("purpose")
        if purpose:
            print(f" - {label}: {value} ({purpose})")
        else:
            print(f" - {label}: {value}")


def print_required(items, heading="Useful information / evidence to prepare:"):
    if not items:
        return
    print("\n" + heading)
    for item in items:
        print(" -", item)


def print_directory_fallback(contact):
    print("\nOfficial council directory contact (fallback):")

    if not contact:
        print(" - No verified directory contact is available in the current dataset.")
        print(" - HariMaga will not invent a phone number, email, or website.")
        return

    if contact.get("phones"):
        print(" Phone :", ", ".join(contact["phones"]))
    if contact.get("mobiles"):
        print(" Mobile:", ", ".join(contact["mobiles"]))
    if contact.get("emails"):
        print(" Email :", ", ".join(contact["emails"]))
    if contact.get("addresses"):
        print(" Address:", contact["addresses"][0])
    if contact.get("source_url"):
        print(" Source:", contact["source_url"])
    print(" Note  : fallback directory contact; not automatically an issue-specific complaint channel.")


# ---------------------------------------------------------------------
# ComplaintRouter clarification flow
# ---------------------------------------------------------------------

def normalize_answer(field, value):
    value = value.strip()
    low = value.lower()

    if field == "electricity_provider":
        if "ceb" in low:
            return "CEB"
        if "leco" in low:
            return "LECO"

    if field == "service_provider_or_scheme":
        if "nwsdb" in low or "water board" in low or "national water" in low:
            return "NWSDB"

    if field == "road_type_or_class":
        if "national" in low or "rda" in low or "highway" in low:
            return "national road"
        if "local" in low or "council" in low or "pradeshiya" in low:
            return "local road"

    return value


def ask_for_router_value(result):
    field = result.get("needed_field", "extra_info")
    options = result.get("options") or []

    print("\nHariMaga needs one more detail:")
    print(result.get("question", "Please provide more information:"))

    if options:
        value = ask_choice("", options)
    else:
        value = input("> ").strip()

    return field, normalize_answer(field, value)


def show_local_authority_result(result, issue_key, local_channels, directory_contacts):
    authorities = []

    if result.get("local_authority"):
        authorities = [result["local_authority"]]
    elif result.get("local_authorities"):
        authorities = result["local_authorities"]

    for la in authorities:
        print("\nAuthority  :", la.get("name"))
        if la.get("type"):
            print("Type       :", la.get("type"))

        gid = la.get("id") or la.get("geography_id")
        verified = local_channels.find(gid, issue_key) if gid else None

        if verified:
            print_channels(verified)
        else:
            print_directory_fallback(directory_contacts.find(la))


def handle_core_router(
    issue_key,
    router,
    local_channels,
    directory_contacts,
    provider_channels,
):
    answers = {}

    for _ in range(10):
        result = router.route(issue_key, answers)

        if result.get("status") == "needs_clarification":
            field, value = ask_for_router_value(result)
            answers[field] = value
            continue

        if result.get("status") != "routed":
            print("\nHariMaga could not safely complete this route:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        line()
        print("HariMaga verified routing result")
        line()
        print("Issue      :", result.get("issue_key"))
        print("Route type :", result.get("route_type"))

        routed_issue = result.get("issue_key") or issue_key

        if result.get("local_authority") or result.get("local_authorities"):
            show_local_authority_result(
                result,
                routed_issue,
                local_channels,
                directory_contacts,
            )
        else:
            authority_name = (
                result.get("authority_name")
                or result.get("authority")
                or result.get("provider")
            )

            if authority_name:
                print("Authority  :", authority_name)

                # Prefer separately verified provider/authority complaint channels.
                verified = provider_channels.find(authority_name, routed_issue)
                if verified:
                    print_channels(verified)
                else:
                    # Fall back to ComplaintRouter's already verified channel payload.
                    print_router_channels(result)
            else:
                print_router_channels(result)

        print_required(result.get("required_information"))

        if result.get("note"):
            print("\nNote:", result["note"])

        return

    print("\nStopped after too many clarification steps.")


# ---------------------------------------------------------------------
# Bus
# ---------------------------------------------------------------------

def print_ntc_fallback(provider_channels):
    ntc = provider_channels.find("National Transport Commission", "bus_complaint")
    if not ntc:
        return

    print("\nVerified NTC intake fallback:")
    for ch in ntc.get("channels", []):
        if ch.get("type") in {"hotline", "complaint_portal"}:
            print(f" - {ch.get('label')}: {ch.get('value')}")


def handle_bus(provider_channels, bus_jurisdiction):
    service = ask_choice(
        "What type of bus was it?",
        ["SLTB", "Private bus", "Not sure"],
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

    line()
    print("HariMaga bus jurisdiction result")
    line()
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
        print("\nNo stored verified complaint channel was found for this authority.")
        print("HariMaga will not invent a contact.")

    regional = resolved.get("regional_sltb")
    if regional:
        print("\nSLTB regional complaint/support WhatsApp:")
        print(f" - {regional['region']} region: {regional['whatsapp']}")

    if record and record.get("verification_level") == "verified_authority_contact":
        print_ntc_fallback(provider_channels)

    print_required([
        "bus_number_or_registration",
        "route_number_or_route_name",
        "date_and_time",
        "exact_incident_location",
        "what_happened",
        "ticket_or_fare_details_if_relevant",
        "photo_or_video_if_available",
    ])


# ---------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------

def handle_consumer(consumer):
    subtype = ask_choice(
        "What best describes the consumer problem?",
        consumer.subtype_options(),
    )

    district = input(
        "\nIn which district is the business / seller / service provider located "
        "or where did the transaction happen?\n> "
    ).strip()

    route = consumer.resolve(district, subtype)

    if route.get("status") != "resolved":
        print("\nI couldn't match that district or complaint type safely.")
        return

    authority = route["authority"]

    line()
    print("HariMaga consumer complaint result")
    line()
    print("Authority :", authority["name"])
    print("District  :", route["district"])
    print("Issue type:", route["subtype_label"])

    print("\nVerified national complaint routes:")
    print(" - Hotline:", authority["hotline"])
    print(" - Consumer Complaint Unit:", authority["consumer_complaint_unit"])
    print(" - Online complaint form:", authority["online_complaint_form"])

    print("\nRelevant CAA District Unit:")
    print(" -", route["district_office"]["office"])
    print(" - Telephone:", route["district_office"]["telephone"])

    print_required(route["required_information"])

    print("\nImportant timing note:")
    print(" -", route["time_note"])

    print("\nHariMaga safety note:")
    print(" -", route["safety"])


# ---------------------------------------------------------------------
# Lost government document
# ---------------------------------------------------------------------

def handle_lost_document(lost, police):
    key = ask_choice(
        "Which government document was lost?",
        lost.document_options(),
    )

    route = lost.resolve(key)

    if route.get("status") != "resolved":
        print("\nUnknown document type.")
        return

    doc = route["document"]
    police_info = route["police"]

    line()
    print("HariMaga lost-document result")
    line()
    print("Document  :", doc["label"])
    print("Authority :", doc["authority"])

    print("\nWhat to do:")
    for i, step in enumerate(doc["steps"], 1):
        print(f" {i}. {step}")

    if doc.get("contacts"):
        print("\nVerified issuing-authority contacts:")
        for c in doc["contacts"]:
            print(f" - {c['label']}: {c['value']}")

    station_query = input(
        "\nType the nearest town or police station name, "
        "or press Enter to skip local-station lookup:\n> "
    ).strip()

    if station_query:
        matches = police.search(station_query)

        if matches:
            print("\nMatching official police contacts:")
            for row in matches:
                print(f" - {row.get('station')}")
                if row.get("general"):
                    print("   General:", row["general"])
                if row.get("mobile"):
                    print("   Mobile :", row["mobile"])
                if row.get("email"):
                    print("   Email  :", row["email"])
        else:
            print("\nNo local police-station snapshot match was found.")
            print("Refresh the official directory with:")
            print(r"  python -u scripts\fetch_police_station_contacts.py")

    print("\nOfficial Sri Lanka Police directory:")
    print(" -", police_info["telephone_index"])
    print("Tell IGP online complaint route:")
    print(" -", police_info["tell_igp"])
    print(" - Email:", police_info["tell_igp_email"])

    print("\nImportant:")
    print(" -", police_info["important_note"])

    print_required(doc["required_information"])


# ---------------------------------------------------------------------
# Women / child safety
# ---------------------------------------------------------------------

def handle_women_child_safety(safety):
    subtype = ask_choice(
        "What best describes the safety concern?",
        safety.subtype_options(),
    )

    danger = ask_yes_no("Is anyone in immediate danger right now? (yes/no)")
    route = safety.resolve(subtype, danger)

    if route.get("status") != "resolved":
        print("\nCould not safely match the concern type.")
        return

    line()
    print("HariMaga women / child safety route")
    line()
    print("Concern :", route["subtype_label"])

    if danger:
        print("\nIMMEDIATE DANGER:")
        print(" - Move to a safer place if possible.")
        print(" - Do not confront the person causing danger.")

    print("\nVerified contacts:")
    for contact in route["contacts"]:
        if contact.get("phone"):
            print(f" - {contact['label']}: {contact['phone']}")
        if contact.get("email"):
            print(f"   Email: {contact['email']}")
        if contact.get("url"):
            print(f"   URL: {contact['url']}")

    print_required(
        route["required_information"],
        heading="Information to provide if safe:",
    )

    print("\nSafety note:")
    print(" -", route["policy"]["evidence_safety"])


# ---------------------------------------------------------------------
# Flood / landslide
# ---------------------------------------------------------------------

def handle_disaster(classification, disaster):
    subtype = classification.get("disaster_subtype")

    if subtype not in {"flood_alert", "landslide_alert"}:
        subtype = ask_choice(
            "What type of disaster concern is this?",
            disaster.alert_options(),
        )

    district = input("\nWhich district are you asking about?\n> ").strip()
    route = disaster.resolve(subtype, district)

    if route.get("status") != "resolved":
        print("\nCould not safely match the disaster alert type.")
        return

    line()
    print("HariMaga disaster alert route")
    line()
    print("Alert type :", route["label"])
    print("District   :", district)
    print("Authority  :", route["technical_authority"])

    print("\nIMPORTANT:")
    print(" - HariMaga does not guess whether this district is under a current warning.")
    print(" - Current status must be checked from the official live warning sources below.")

    print("\nOfficial live warning sources:")
    for src in route["live_sources"]:
        print(f" - {src['label']}: {src['url']}")

    print("\nEmergency / information contacts:")
    for contact in route["dmc_contacts"]:
        print(f" - {contact['label']}: {contact.get('phone')}")
    for contact in route["technical_contacts"]:
        print(f" - {contact['label']}: {contact.get('phone')}")
        if contact.get("email"):
            print(f"   Email: {contact['email']}")

    print_required(
        route["required_information"],
        heading="Useful information to have ready:",
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    classifier = RobustIssueClassifier()

    router = ComplaintRouter(ROOT)
    local_channels = LocalAuthorityIssueChannelService(ROOT)
    directory_contacts = LocalAuthorityContactService(ROOT)
    provider_channels = ProviderIssueChannelService(ROOT)

    bus_jurisdiction = BusJurisdictionService(ROOT)
    consumer = ConsumerComplaintService(ROOT)
    lost = LostDocumentService(ROOT)
    police = PoliceStationContactService(ROOT)
    safety = WomenChildSafetyService(ROOT)
    disaster = DisasterAlertService(ROOT)

    line()
    print("HariMaga AI | හරිමග AI")
    print("Unified Problem-to-Authority Routing Demo v1")
    print("ප්‍රශ්නය කියන්න. හරිමග අපි පෙන්වන්නම්.")
    line()

    problem = input("Describe your problem: ").strip()
    classification = classifier.predict(problem)

    issue_key = classification.get("label", "unknown_government_issue")

    print("\nDetected issue :", issue_key)
    print("Confidence     :", round(float(classification.get("confidence", 0.0)), 3))
    print("Method         :", classification.get("method"))

    # Specialized flows first.
    if issue_key == "women_child_safety":
        handle_women_child_safety(safety)
        return

    if issue_key == "disaster_alert":
        handle_disaster(classification, disaster)
        return

    if issue_key == "lost_document":
        handle_lost_document(lost, police)
        return

    if issue_key == "consumer_complaint":
        handle_consumer(consumer)
        return

    if issue_key == "bus_complaint":
        handle_bus(provider_channels, bus_jurisdiction)
        return

    # Core ComplaintRouter handles:
    # road, garbage, water, electricity, environment, immigration, unknown/fallback.
    handle_core_router(
        issue_key,
        router,
        local_channels,
        directory_contacts,
        provider_channels,
    )


if __name__ == "__main__":
    main()
