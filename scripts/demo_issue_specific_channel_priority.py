from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.issue_classifier import HybridIssueClassifier
from services.complaint_router import ComplaintRouter
from services.local_authority_contact_service import LocalAuthorityContactService
from services.local_authority_issue_channel_service import LocalAuthorityIssueChannelService


def ask_for_value(result):
    question = result.get("question", "Please provide more information:")
    field = result.get("needed_field", "extra_info")
    options = result.get("options") or []

    print("\nHariMaga needs one more detail:")
    print(question)

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
        if "ceb" in low:
            return "CEB"
        if "leco" in low:
            return "LECO"

    if field == "service_provider_or_scheme":
        if "nwsdb" in low or "water board" in low:
            return "NWSDB"

    if field == "road_type_or_class":
        if "national" in low or "rda" in low or "highway" in low:
            return "national road"
        if "local" in low or "council" in low or "pradeshiya" in low:
            return "local road"

    return value


def print_channels(record):
    level = record.get("verification_level")

    if level == "verified_issue_specific_channel":
        print("\nVerified complaint route:")
    else:
        print("\nVerified general council complaint route:")
        print("Note: this is not a dedicated issue-specific hotline.")

    for ch in record.get("channels", []):
        print(f" - {ch.get('label')}: {ch.get('value')}")

    if record.get("guidance"):
        print("\nGuidance:", record["guidance"])


def print_directory_fallback(contact):
    print("\nOfficial council contact (fallback):")

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
    print(" Source:", contact.get("source_url"))


def main():
    classifier = HybridIssueClassifier()
    router = ComplaintRouter(ROOT)
    issue_channels = LocalAuthorityIssueChannelService(ROOT)
    directory_contacts = LocalAuthorityContactService(ROOT)

    print("=" * 70)
    print("HariMaga AI - Complaint Channel Priority Demo")
    print("=" * 70)

    problem = input("Describe your problem: ").strip()
    classification = classifier.predict(problem)

    issue_key = classification["label"]

    print("\nDetected issue :", issue_key)
    print("Confidence     :", round(classification["confidence"], 3))
    print("Method         :", classification["method"])

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

            geography_id = la.get("id") or la.get("geography_id")
            verified = issue_channels.find(geography_id, issue_key)

            if verified:
                print_channels(verified)
            else:
                fallback = directory_contacts.find(la)
                print_directory_fallback(fallback)

        elif result.get("authority_name"):
            print("Authority  :", result.get("authority_name"))
            print("\nThis demo only adds the new priority layer to local-authority routes.")
            print("National/provider routes remain handled by ComplaintRouter.")

        if result.get("required_information"):
            print("\nUseful information to prepare:")
            for item in result["required_information"]:
                print(" -", item)

        return

    print("\nStopped after too many clarification steps.")


if __name__ == "__main__":
    main()
