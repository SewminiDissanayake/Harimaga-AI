from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.disaster_alert_service import DisasterAlertService


def main():
    clf = RobustIssueClassifier()
    svc = DisasterAlertService(ROOT)

    print("=" * 70)
    print("HariMaga AI - Flood / Landslide Alert Demo v1")
    print("=" * 70)

    text = input("Describe your concern: ").strip()
    result = clf.predict(text)

    print("\nDetected issue :", result["label"])
    print("Confidence     :", round(float(result.get("confidence", 0)), 3))
    print("Method         :", result.get("method"))

    if result["label"] != "disaster_alert":
        print("\nThis demo is only for flood/landslide alert concerns.")
        return

    subtype = result.get("disaster_subtype")
    district = input("\nWhich district are you asking about?\n> ").strip()
    route = svc.resolve(subtype, district)

    print("\n" + "=" * 70)
    print("HariMaga disaster alert route")
    print("=" * 70)
    print("Alert type :", route["label"])
    print("District   :", district)
    print("Authority  :", route["technical_authority"])

    print("\nIMPORTANT:")
    print(" - HariMaga does not guess whether your district is under a current warning.")
    print(" - Check the latest official warning below.")

    print("\nOfficial live warning sources:")
    for src in route["live_sources"]:
        print(f" - {src['label']}: {src['url']}")

    print("\nEmergency / information contacts:")
    for c in route["dmc_contacts"]:
        print(f" - {c['label']}: {c.get('phone')}")
    for c in route["technical_contacts"]:
        print(f" - {c['label']}: {c.get('phone')}")
        if c.get("email"):
            print(f"   Email: {c['email']}")

    print("\nUseful information to have ready:")
    for item in route["required_information"]:
        print(" -", item)


if __name__ == "__main__":
    main()
