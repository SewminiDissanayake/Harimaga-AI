import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "meta" / "ds_contact_match_report_resolved.json"
SUPPLEMENTAL = ROOT / "data" / "contacts" / "supplemental_official_ds_contacts.json"
OUTPUT = ROOT / "data" / "meta" / "ds_contact_coverage_final.json"

with open(REPORT, encoding="utf-8") as f:
    report = json.load(f)
with open(SUPPLEMENTAL, encoding="utf-8") as f:
    supplemental = json.load(f)["records"]

gaps = {g["geography_id"]: g for g in report.get("geography_without_exact_contact", [])}
supp = {r["geography_id"]: r for r in supplemental}

missing = set(gaps) - set(supp)
extra = set(supp) - set(gaps)
if missing or extra:
    raise RuntimeError(f"Gap mismatch. missing={sorted(missing)} extra={sorted(extra)}")

supplemental_matches = []
for r in supplemental:
    supplemental_matches.append({
        "status": "supplemental_official_source",
        "contact_division": r["name"],
        "contact_district": r["district"],
        "geography_id": r["geography_id"],
        "geography_name": r["name"],
        "source_url": r["source_url"],
        "source_note": r["source_note"],
        "contact": r["contact"]
    })

existing = report.get("matches", [])
all_matches = existing + supplemental_matches

out = {
    "status": "complete",
    "coverage_policy": (
        "RTI directory mappings are retained where available. DS geography records "
        "missing from RTI are supplemented only from official Ministry of Home Affairs "
        "or equivalent official government sources."
    ),
    "counts": {
        "dcs_geography_total": report["counts"]["dcs_geography_total"],
        "rti_contact_offices_total": report["counts"]["rti_contact_offices_total"],
        "exact_rti_matches": report["counts"]["exact_match_count"],
        "approved_manual_rti_matches": report["counts"]["approved_manual_match_count"],
        "supplemental_official_matches": len(supplemental_matches),
        "total_ds_geography_covered": len({m["geography_id"] for m in all_matches}),
        "unresolved_geography_count": 0
    },
    "matches": all_matches,
    "unresolved": []
}

if out["counts"]["total_ds_geography_covered"] != out["counts"]["dcs_geography_total"]:
    raise RuntimeError("Coverage did not reach the DCS geography total.")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("Saved:", OUTPUT)
print("Exact RTI matches:", out["counts"]["exact_rti_matches"])
print("Approved manual RTI matches:", out["counts"]["approved_manual_rti_matches"])
print("Supplemental official matches:", out["counts"]["supplemental_official_matches"])
print("Total DS geography covered:", out["counts"]["total_ds_geography_covered"])
print("Unresolved:", out["counts"]["unresolved_geography_count"])
