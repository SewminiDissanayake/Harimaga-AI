from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.consumer_complaint_service import ConsumerComplaintService


def choose(question, options):
    print("\n" + question)
    for i, (_, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    raw = input("> ").strip()
    if raw.isdigit():
        i = int(raw)-1
        if 0 <= i < len(options):
            return options[i][0]
    return raw


def main():
    clf = RobustIssueClassifier()
    consumer = ConsumerComplaintService(ROOT)

    print("="*70)
    print("HariMaga AI - Consumer Complaint Demo v1")
    print("="*70)

    text = input("Describe your problem: ").strip()
    result = clf.predict(text)

    print("\nDetected issue :", result["label"])
    print("Confidence     :", round(float(result.get("confidence",0)),3))
    print("Method         :", result.get("method"))

    if result["label"] != "consumer_complaint":
        print("\nThis demo is only for consumer complaints.")
        return

    subtype = choose(
        "What best describes the consumer problem?",
        consumer.subtype_options()
    )

    district = input(
        "\nIn which district is the business / seller / service provider located "
        "or where did the transaction happen?\n> "
    ).strip()

    route = consumer.resolve(district, subtype)

    if route["status"] != "resolved":
        print("\nI couldn't match that district or complaint type safely.")
        return

    a = route["authority"]
    print("\n" + "="*70)
    print("HariMaga consumer complaint result")
    print("="*70)
    print("Authority :", a["name"])
    print("District  :", route["district"])
    print("Issue type:", route["subtype_label"])

    print("\nVerified national complaint routes:")
    print(" - Hotline:", a["hotline"])
    print(" - Consumer Complaint Unit:", a["consumer_complaint_unit"])
    print(" - Online complaint form:", a["online_complaint_form"])

    print("\nRelevant CAA District Unit:")
    print(" -", route["district_office"]["office"])
    print(" - Telephone:", route["district_office"]["telephone"])

    print("\nUseful information / evidence to prepare:")
    for item in route["required_information"]:
        print(" -", item)

    print("\nImportant timing note:")
    print(" -", route["time_note"])

    print("\nHariMaga safety note:")
    print(" -", route["safety"])


if __name__ == "__main__":
    main()
