from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.lost_document_service import LostDocumentService
from services.police_station_contact_service import PoliceStationContactService


def choose(options):
    for i, (_, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    raw = input("> ").strip()
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx][0]
    return raw


def main():
    clf = RobustIssueClassifier()
    lost = LostDocumentService(ROOT)
    police = PoliceStationContactService(ROOT)

    print("=" * 70)
    print("HariMaga AI - Lost Document / Police Entry Demo v1")
    print("=" * 70)

    problem = input("Describe your problem: ").strip()
    result = clf.predict(problem)

    print("\nDetected issue :", result["label"])
    print("Confidence     :", round(float(result.get("confidence", 0)), 3))
    print("Method         :", result.get("method"))

    if result["label"] != "lost_document":
        print("\nThis demo is only for lost government documents.")
        return

    print("\nWhich document was lost?")
    key = choose(lost.document_options())
    route = lost.resolve(key)

    if route["status"] != "resolved":
        print("Unknown document type.")
        return

    doc = route["document"]
    police_info = route["police"]

    print("\n" + "=" * 70)
    print("HariMaga lost-document result")
    print("=" * 70)
    print("Document  :", doc["label"])
    print("Authority :", doc["authority"])

    print("\nWhat to do:")
    for i, step in enumerate(doc["steps"], 1):
        print(f" {i}. {step}")

    if doc.get("contacts"):
        print("\nVerified issuing-authority contacts:")
        for c in doc["contacts"]:
            print(f" - {c['label']}: {c['value']}")

    print("\nPolice entry / complaint:")
    station_query = input(
        "Type the nearest town or police station name (e.g. Matale, Kandy), "
        "or press Enter to skip:\n> "
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
            print("  python -u scripts\\fetch_police_station_contacts.py")

    print("\nOfficial Sri Lanka Police directory:")
    print(" -", police_info["telephone_index"])
    print("Tell IGP online complaint route:")
    print(" -", police_info["tell_igp"])
    print(" - Email:", police_info["tell_igp_email"])

    print("\nImportant:")
    print(" -", police_info["important_note"])

    print("\nInformation / documents to prepare:")
    for item in doc["required_information"]:
        print(" -", item)


if __name__ == "__main__":
    main()
