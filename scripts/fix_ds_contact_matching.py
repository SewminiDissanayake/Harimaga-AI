import json
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[1]
GEO_FILE = ROOT / "data" / "geography" / "ds_divisions.json"
CONTACT_FILE = ROOT / "data" / "contacts" / "divisional_secretariat_rti_contacts.json"
REPORT_FILE = ROOT / "data" / "meta" / "ds_contact_match_report.json"

def clean(v):
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()

def nested_name(v):
    # The DCS geography backbone stores province/district as objects:
    # {"code": "...", "name": "..."}
    if isinstance(v, dict):
        return clean(v.get("name"))
    return clean(v)

def norm(v):
    s = nested_name(v)
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("–", "-").replace("—", "-").replace("&", " and ")

    # Safe administrative wording cleanup only.
    s = re.sub(r"\bdivisional\s+secretariat\b", " ", s, flags=re.I)
    s = re.sub(r"\bdivision\b", " ", s, flags=re.I)
    s = re.sub(r"\bsecretariat\b", " ", s, flags=re.I)
    s = re.sub(r"\bdsd\b", " ", s, flags=re.I)
    s = re.sub(r"\bds\b", " ", s, flags=re.I)

    return re.sub(r"[^a-z0-9]+", "", s.lower())

def similarity(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()

def load_records(path):
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("records", payload if isinstance(payload, list) else [])

def main():
    if not GEO_FILE.exists():
        raise FileNotFoundError(f"Missing geography file: {GEO_FILE}")
    if not CONTACT_FILE.exists():
        raise FileNotFoundError(f"Missing contact file: {CONTACT_FILE}")

    geo_records = load_records(GEO_FILE)
    contact_records = load_records(CONTACT_FILE)

    print("Yomu DS contact re-matcher")
    print(f"DCS geography rows : {len(geo_records)}")
    print(f"RTI contact offices: {len(contact_records)}")
    print()

    # Group DCS geography by normalized district.
    by_district = {}
    for g in geo_records:
        district_name = nested_name(g.get("district"))
        by_district.setdefault(norm(district_name), []).append(g)

    exact_matches = []
    manual_review = []

    for c in contact_records:
        c_district = nested_name(c.get("district"))
        c_division = nested_name(c.get("division"))

        candidates = by_district.get(norm(c_district), [])

        exact = [
            g for g in candidates
            if norm(g.get("name")) == norm(c_division)
        ]

        if len(exact) == 1:
            g = exact[0]
            exact_matches.append({
                "status": "exact",
                "contact_division": c_division,
                "contact_district": c_district,
                "geography_id": g.get("id"),
                "geography_name": g.get("name"),
                "geography_district": nested_name(g.get("district")),
                "geography_province": nested_name(g.get("province")),
            })
            continue

        ranked = sorted(
            (
                (similarity(c_division, g.get("name")), g)
                for g in candidates
            ),
            key=lambda x: x[0],
            reverse=True
        )

        manual_review.append({
            "contact_division": c_division,
            "contact_district": c_district,
            "reason": (
                "multiple_exact_candidates" if len(exact) > 1
                else "no_exact_normalized_match"
            ),
            "suggestions": [
                {
                    "score": round(score, 3),
                    "geography_id": g.get("id"),
                    "geography_name": g.get("name"),
                    "geography_district": nested_name(g.get("district")),
                }
                for score, g in ranked[:5]
            ],
            "action": "manual_review_required"
        })

    matched_geo_ids = {m["geography_id"] for m in exact_matches}
    geography_without_exact_contact = [
        {
            "geography_id": g.get("id"),
            "name": g.get("name"),
            "district": nested_name(g.get("district")),
            "province": nested_name(g.get("province")),
        }
        for g in geo_records
        if g.get("id") not in matched_geo_ids
    ]

    report = {
        "status": "completed",
        "note": (
            "Corrected matcher: DCS geography stores district/province as nested "
            "objects, while the earlier matcher treated them as plain strings."
        ),
        "counts": {
            "dcs_geography_total": len(geo_records),
            "rti_contact_offices_total": len(contact_records),
            "exact_match_count": len(exact_matches),
            "manual_review_count": len(manual_review),
            "geography_without_exact_contact_count": len(geography_without_exact_contact),
        },
        "matches": exact_matches,
        "unmatched_contacts": manual_review,
        "geography_without_exact_contact": geography_without_exact_contact,
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Exact matches : {len(exact_matches)}")
    print(f"Manual review : {len(manual_review)}")
    print(f"DCS rows without exact RTI match: {len(geography_without_exact_contact)}")
    print()
    print(f"Saved corrected report: {REPORT_FILE}")
    print()
    print("No fuzzy suggestion was auto-accepted.")

if __name__ == "__main__":
    main()
