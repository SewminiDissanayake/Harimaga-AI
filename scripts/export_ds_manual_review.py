import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "meta" / "ds_contact_match_report.json"
OUT = ROOT / "data" / "meta" / "ds_manual_review.csv"

with open(REPORT, encoding="utf-8") as f:
    data = json.load(f)

rows = data.get("unmatched_contacts", [])

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "contact_district",
        "contact_division",
        "top1_geography_name",
        "top1_score",
        "top2_geography_name",
        "top2_score",
        "top3_geography_name",
        "top3_score",
        "review_status",
        "approved_geography_id",
        "notes"
    ])

    for row in rows:
        suggestions = row.get("suggestions", [])
        def get(i, key):
            return suggestions[i].get(key, "") if i < len(suggestions) else ""

        writer.writerow([
            row.get("contact_district", ""),
            row.get("contact_division", ""),
            get(0, "geography_name"),
            get(0, "score"),
            get(1, "geography_name"),
            get(1, "score"),
            get(2, "geography_name"),
            get(2, "score"),
            "",
            "",
            ""
        ])

print(f"Created: {OUT}")
print(f"Rows for manual review: {len(rows)}")
print()
print("Open the CSV in Excel. Do not auto-approve rows only from similarity score.")
print("For each row, compare the RTI contact division with the DCS geography candidate.")
