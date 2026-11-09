import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GEO_FILE = ROOT / "data" / "geography" / "local_authorities.json"
OLD_REPORT = ROOT / "data" / "meta" / "local_authority_contact_match_report.json"

CONTACT_OUT = ROOT / "data" / "contacts" / "local_authority_official_directory_contacts_v3.json"
REPORT_OUT = ROOT / "data" / "meta" / "local_authority_contact_match_report_v3.json"
MANUAL_OUT = ROOT / "data" / "meta" / "local_authority_manual_review_v3.json"

DISTRICT_ALIASES = {
    "hambanthota": "hambantota",
    "rathnapura": "ratnapura",
    "monaragala": "moneragala",
}

# Conservative spelling/transliteration equivalences only.
# These do NOT change authority type or district.
NAME_ALIASES = {
    "dehiwalamtlavinia": "dehiwalamountlavinia",
    "boralasgamuwa": "boralesgamuwa",
    "kotikawattemulleriyawa": "kotikawattamullariyawa",
    "negambo": "negombo",
    "meerigama": "mirigama",
    "aththanagalla": "attanagalla",
    "bulathsinghala": "bulathsinhala",
    "walallawita": "walallavita",
    "waththegama": "wattegama",
    "harispaththuwa": "harispattuwa",
    "panwila": "panvila",
    "ududumbara": "udadumbara",
    "madadumbara": "medadumbara",
    "pathahewahaheta": "pathahewaheta",
    "kandyfourgravetsgangawatakorale": "kandyfourgravertsgangawatakorale",
    "thalawakalelidula": "thalawakalelindula",
    "bentota": "benthota",
    "pitabaddara": "pitadeddara",
    "waligama": "weligama",
    "angunalapalassa": "angunakolapelessa",
    "thissamaharamaya": "thissamaharama",
    "lunugamwehera": "lunugamvehera",
    "valvettithurai": "valvettiturai",
    "vadamaradchysouthwest": "vadamaradchisouthwest",
    "pachchileppalei": "pachchillaipalli",
    "poonagary": "poonakari",
    "vengalcheddikulam": "vengalacheddikulam",
    "puthukkudiyiruppu": "puthukudiyiruppu",
    "marritimepattu": "maritimepattu",
    "manmunaiwestvavunathivu": "manmunaiwestvavunativu",
    "addalachchenai": "addalachchanai",
    "karaitivu": "karathivu",
    "dehiaththakandiya": "dehiattakandiya",
    "thirukkovil": "thirukkovili",
    "seruwila": "seruvila",
    "kantale": "kanthale",
    "thampalakamam": "thambalagamuwa",
    "wanathavilluwa": "vanathawilluwa",
    "nawagaththegama": "nawagattegama",
    "naththandiya": "nattandiya",
    "elahara": "elahera",
    "walikanda": "welikanda",
    "meegahakivula": "meegahaivula",
    "kandeketiya": "kandaketiya",
    "ridimaliyadda": "rideemaliyadda",
    "soranatota": "soranathota",
    "monaragala": "moneragala",
    "bibile": "bibila",
    "thanamalwila": "thanamalvila",
    "madagama": "medagama",
    "rathnapura": "ratnapura",
    "palmadulla": "pelmadulla",
    "nivitigala": "nivithigala",
    "yatiyantota": "yatiyanthota",
    "dehiowita": "dehiovita",
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def compact(value):
    """Normalize punctuation and remove council-type labels/suffixes."""
    s = "" if value is None else str(value).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("–", " ").replace("—", " ").replace("&", " and ")

    # KEY FIX: also strip DCS abbreviations MC / UC / PS.
    s = re.sub(
        r"\b(municipal council|urban council|pradeshiya sabha|municipality|mc|uc|ps)\b",
        " ",
        s,
    )
    s = re.sub(r"\band\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def norm_name(value):
    x = compact(value)
    return NAME_ALIASES.get(x, x)

def norm_district(value):
    x = compact(value)
    return DISTRICT_ALIASES.get(x, x)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    if not GEO_FILE.exists():
        raise FileNotFoundError(GEO_FILE)
    if not OLD_REPORT.exists():
        raise FileNotFoundError(OLD_REPORT)

    geography = load_json(GEO_FILE)["records"]
    old_report = load_json(OLD_REPORT)

    # The v2 report contains all 250 harvested RTI rows in manual_review.
    rows = old_report.get("manual_review", [])
    if not rows:
        raise RuntimeError("No harvested RTI local-authority rows found in old report.")

    # DCS source can contain duplicate renderings that share the same geography ID.
    # Deduplicate by ID before matching.
    geo_by_id = {}
    for g in geography:
        geo_by_id[g["id"]] = g
    unique_geo = list(geo_by_id.values())

    index = defaultdict(list)
    for g in unique_geo:
        key = (
            norm_district(g.get("district")),
            g.get("type"),
            norm_name(g.get("name")),
        )
        index[key].append(g)

    matched_rows = []
    manual_rows = []

    for row in rows:
        area_name = row.get("area_name")
        if not area_name:
            manual_rows.append({
                **row,
                "v3_status": "manual_review",
                "v3_reason": "missing_area_name",
            })
            continue

        key = (
            norm_district(row.get("district")),
            row.get("la_type"),
            norm_name(area_name),
        )
        candidates = index.get(key, [])

        if len(candidates) == 1:
            g = candidates[0]
            matched_rows.append({
                **row,
                "v3_status": "safe_normalized_match",
                "geography_id": g["id"],
                "geography_name": g["name"],
                "geography_type": g["type"],
                "geography_district": g["district"],
            })
        else:
            manual_rows.append({
                **row,
                "v3_status": "manual_review",
                "v3_reason": (
                    "no_safe_normalized_match"
                    if not candidates
                    else "ambiguous_normalized_match"
                ),
                "v3_candidate_ids": [g["id"] for g in candidates],
            })

    # Aggregate officer/contact rows per unique local authority.
    grouped = {}
    for row in matched_rows:
        gid = row["geography_id"]
        rec = grouped.setdefault(gid, {
            "geography_id": gid,
            "name": row["geography_name"],
            "district": row["geography_district"],
            "type": row["geography_type"],
            "directory_contact_status": "official_rti_directory",
            "complaint_channel_status": "not_yet_issue_specific",
            "source_url": row.get("source_url"),
            "officer_records": [],
        })

        rec["officer_records"].append({
            "officer": row.get("officer"),
            "address": row.get("address", []),
            "telephone_01": row.get("telephone_01", []),
            "telephone_02": row.get("telephone_02", []),
            "fax": row.get("fax", []),
            "mobile": row.get("mobile", []),
            "email": row.get("email", []),
            "source_type": row.get("source_type"),
            "contact_purpose": row.get("contact_purpose"),
            "match_status": row.get("v3_status"),
        })

    contact_records = list(grouped.values())
    matched_ids = set(grouped)

    geography_without_contact = [
        {
            "geography_id": g["id"],
            "name": g["name"],
            "district": g["district"],
            "type": g["type"],
        }
        for g in unique_geo
        if g["id"] not in matched_ids
    ]

    CONTACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)

    with open(CONTACT_OUT, "w", encoding="utf-8") as f:
        json.dump({
            "dataset": "HariMaga official local-authority directory contacts v3",
            "warning": (
                "RTI Designated Officer / council directory contacts are official "
                "directory fallbacks, not automatically issue-specific complaint channels."
            ),
            "generated_at": now_iso(),
            "records": contact_records,
        }, f, ensure_ascii=False, indent=2)

    report = {
        "status": "completed",
        "method": (
            "district + authority_type + normalized authority name; "
            "DCS MC/UC/PS suffixes removed; conservative spelling aliases only; "
            "no fuzzy suggestion auto-accepted"
        ),
        "counts": {
            "rti_rows_rematched": len(rows),
            "dcs_local_authority_records_raw": len(geography),
            "dcs_unique_geography_ids": len(unique_geo),
            "safe_matched_rows": len(matched_rows),
            "unique_local_authorities_with_directory_contact": len(contact_records),
            "manual_review_rows": len(manual_rows),
            "unique_geography_ids_without_directory_contact": len(geography_without_contact),
        },
        "manual_review": manual_rows,
        "geography_without_directory_contact": geography_without_contact,
    }

    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(MANUAL_OUT, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(manual_rows),
            "records": manual_rows,
        }, f, ensure_ascii=False, indent=2)

    print("HariMaga Local Authority Re-matcher v3")
    print("-------------------------------------")
    print("RTI rows rematched                    :", len(rows))
    print("DCS raw local-authority rows          :", len(geography))
    print("DCS unique geography IDs              :", len(unique_geo))
    print("Safe matched RTI rows                 :", len(matched_rows))
    print("Unique LAs with directory contact     :", len(contact_records))
    print("Manual review rows                    :", len(manual_rows))
    print("Unique geography IDs without contact  :", len(geography_without_contact))
    print()
    print("Saved:")
    print(" -", CONTACT_OUT)
    print(" -", REPORT_OUT)
    print(" -", MANUAL_OUT)
    print()
    print("No fuzzy suggestion was auto-accepted.")

if __name__ == "__main__":
    main()
