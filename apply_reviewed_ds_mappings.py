import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "data" / "meta" / "ds_contact_match_report.json"
MAPPINGS = ROOT / "data" / "meta" / "Yomu_DS_Manual_Review_Resolved.json"
OUTPUT = ROOT / "data" / "meta" / "ds_contact_match_report_resolved.json"

with open(REPORT, encoding="utf-8") as f:
    report = json.load(f)
with open(MAPPINGS, encoding="utf-8") as f:
    mapping_payload = json.load(f)

approved = {
    (m["contact_district"], m["contact_division"]): m
    for m in mapping_payload["mappings"]
    if m["review_status"] == "APPROVED"
}

existing = report.get("matches", [])
unmatched = report.get("unmatched_contacts", report.get("unmatched", []))

manual_matches = [{
    "status": "approved_manual_review",
    "contact_district": m["contact_district"],
    "contact_division": m["contact_division"],
    "geography_name": m["approved_geography_name"],
    "geography_id": m["approved_geography_id"],
    "notes": m["notes"],
    "source_url": m["review_source_url"],
} for m in approved.values()]

remaining = [
    row for row in unmatched
    if (row.get("contact_district"), row.get("contact_division")) not in approved
]

approved_ids = {m["geography_id"] for m in manual_matches}
geo_without = report.get("geography_without_exact_contact", [])
remaining_geo = [g for g in geo_without if g.get("geography_id") not in approved_ids]

out = dict(report)
out["matches"] = existing + manual_matches
out["unmatched_contacts"] = remaining
out["geography_without_exact_contact"] = remaining_geo
out["counts"] = dict(out.get("counts", {}))
out["counts"]["exact_match_count"] = len(existing)
out["counts"]["approved_manual_match_count"] = len(manual_matches)
out["counts"]["total_mapped_contact_records"] = len(existing) + len(manual_matches)
out["counts"]["manual_review_count"] = len(remaining)
out["counts"]["geography_without_contact_count"] = len(remaining_geo)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("Saved:", OUTPUT)
print("Exact matches:", len(existing))
print("Approved manual matches:", len(manual_matches))
print("Still pending:", len(remaining))
print("Geography rows still without mapped contact:", len(remaining_geo))
