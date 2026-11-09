from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.women_child_safety_service import WomenChildSafetyService


def choose(options):
    for i, (_, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    raw = input("> ").strip()
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx][0]
    return raw


def yes(value):
    return value.strip().lower() in {"y", "yes", "ow", "1", "true"}


def main():
    clf = RobustIssueClassifier()
    svc = WomenChildSafetyService(ROOT)

    print("=" * 70)
    print("HariMaga AI - Women & Child Safety Demo v1")
    print("=" * 70)

    text = input("Describe your problem: ").strip()
    result = clf.predict(text)

    print("\nDetected issue :", result["label"])
    print("Confidence     :", round(float(result.get("confidence", 0)), 3))
    print("Method         :", result.get("method"))

    if result["label"] != "women_child_safety":
        print("\nThis demo is only for women/child safety concerns.")
        return

    print("\nWhat best describes the concern?")
    subtype = choose(svc.subtype_options())
    danger = yes(input("\nIs anyone in immediate danger right now? (yes/no)\n> "))

    route = svc.resolve(subtype, danger)
    if route["status"] != "resolved":
        print("Could not resolve the safety subtype.")
        return

    print("\n" + "=" * 70)
    print("HariMaga safety route")
    print("=" * 70)
    print("Concern :", route["subtype_label"])

    if danger:
        print("\nIMMEDIATE DANGER:")
        print(" - Move to a safer place if possible.")
        print(" - Do not confront the person causing danger.")

    print("\nVerified contacts:")
    for c in route["contacts"]:
        if c.get("phone"):
            print(f" - {c['label']}: {c['phone']}")
        if c.get("email"):
            print(f"   Email: {c['email']}")
        if c.get("url"):
            print(f"   URL: {c['url']}")

    print("\nInformation to provide if safe:")
    for item in route["required_information"]:
        print(" -", item)

    print("\nSafety note:")
    print(" -", route["policy"]["evidence_safety"])


if __name__ == "__main__":
    main()
