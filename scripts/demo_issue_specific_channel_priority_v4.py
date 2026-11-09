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
        if "ceb" in low or "ceylon electricity" in low:
            return "CEB"
        if "leco" in low or "lanka electricity" in low:
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


def print_channels(record, heading):
    print("\n" + heading)
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
    classifier = RobustIssueClassifier()
    router = ComplaintRouter(ROOT)
    local_channels = LocalAuthorityIssueChannelService(ROOT)
    directory_contacts = LocalAuthorityContactService(ROOT)
    provider_channels = ProviderIssueChannelService(ROOT)

    print("=" * 70)
    print("HariMaga AI - Complaint Channel Priority Demo v4")
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
            gid = la.get("id") or la.get("geography_id")
            verified = local_channels.find(gid, issue_key)

            if verified:
                heading = (
                    "Verified complaint route:"
                    if verified.get("verification_level") == "verified_issue_specific_channel"
                    else "Verified general council complaint route:"
                )
                print_channels(verified, heading)
            else:
                print_directory_fallback(directory_contacts.find(la))

        else:
            authority_name = (
                result.get("authority_name")
                or result.get("authority")
                or result.get("provider")
            )

            if authority_name:
                print("Authority  :", authority_name)
                verified = provider_channels.find(authority_name, issue_key)

                if verified:
                    print_channels(
                        verified,
                        "Verified issue-specific/provider complaint route:"
                    )
                else:
                    print("\nNo additional verified provider-specific channel is stored.")
                    print("HariMaga keeps the original ComplaintRouter route and does not invent one.")

        if result.get("required_information"):
            print("\nUseful information to prepare:")
            for item in result["required_information"]:
                print(" -", item)
        return

    print("\nStopped after too many clarification steps.")


if __name__ == "__main__":
    main()
