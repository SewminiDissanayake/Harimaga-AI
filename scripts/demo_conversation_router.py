from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.issue_classifier import HybridIssueClassifier
from services.complaint_router import ComplaintRouter


def pretty_result(result):
    print("\n" + "=" * 70)
    print("HariMaga result")
    print("=" * 70)

    if result.get("status") == "routed":
        print("Status       : routed")
        print("Issue        :", result.get("issue_key"))
        print("Route type   :", result.get("route_type"))

        if result.get("authority_name"):
            print("Authority    :", result.get("authority_name"))

        if result.get("local_authority"):
            la = result["local_authority"]
            print("Authority    :", la.get("name"))
            print("Authority type:", la.get("type"))

        if result.get("local_authorities"):
            print("Authorities  :")
            for la in result["local_authorities"]:
                print(" -", la.get("name"))

        if result.get("channels"):
            print("\nOfficial channels:")
            for ch in result["channels"]:
                print(f" - {ch.get('type')}: {ch.get('value')} ({ch.get('purpose')})")

        if result.get("required_information"):
            print("\nUseful information to prepare:")
            for item in result["required_information"]:
                print(" -", item)

        if result.get("note"):
            print("\nNote:", result["note"])

    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def ask_for_value(result):
    question = result.get("question", "Please provide more information:")
    needed_field = result.get("needed_field", "extra_info")
    options = result.get("options") or []

    print("\nHariMaga needs one more detail:")
    print(question)

    if options:
        for i, option in enumerate(options, start=1):
            print(f"  {i}. {option}")

        raw = input("> ").strip()

        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return needed_field, options[idx]

        return needed_field, raw

    return needed_field, input("> ").strip()


def normalize_answer(field, value):
    # Convert user-friendly option text to values expected by ComplaintRouter.
    v = value.strip()
    low = v.lower()

    if field == "electricity_provider":
        if "ceb" in low:
            return "CEB"
        if "leco" in low:
            return "LECO"

    if field == "service_provider_or_scheme":
        if "nwsdb" in low or "water board" in low:
            return "NWSDB"
        return v

    if field == "road_type_or_class":
        if "national" in low or "rda" in low or "highway" in low:
            return "national road"
        if "local" in low or "council" in low or "pradeshiya" in low:
            return "local road"
        return v

    if field == "issue_type":
        mapping = {
            "industrial pollution": "industrial pollution",
            "hazardous waste": "hazardous waste",
            "noise pollution": "noise pollution",
            "environmental damage": "environmental damage",
            "routine garbage collection": "routine garbage collection",
        }
        return mapping.get(low, v)

    return v


def main():
    classifier = HybridIssueClassifier()
    router = ComplaintRouter(ROOT)

    print("=" * 70)
    print("HariMaga AI - Interactive Routing Demo")
    print("=" * 70)

    problem = input("Describe your problem: ").strip()

    classification = classifier.predict(problem)

    print("\nDetected issue :", classification["label"])
    print("Confidence     :", round(classification["confidence"], 3))
    print("Method         :", classification["method"])

    answers = {}
    issue_key = classification["label"]

    # Guard against an endless clarification loop.
    for _ in range(8):
        result = router.route(issue_key, answers)

        if result.get("status") == "routed":
            pretty_result(result)
            return

        if result.get("status") != "needs_clarification":
            pretty_result(result)
            return

        field, value = ask_for_value(result)
        answers[field] = normalize_answer(field, value)

    print("\nHariMaga stopped because too many clarification steps were needed.")
    print("Collected answers:", answers)


if __name__ == "__main__":
    main()
