import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CONTACT_DIR = ROOT / "data" / "contacts"
META_DIR = ROOT / "data" / "meta"
CONTACT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

IO_URL = "https://rti.gov.lk/io-list/"
DO_URL = "https://rti.gov.lk/do-list/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; YomuAI-Research/1.0; +student-project)"
}

DS_GEO_FILE = ROOT / "data" / "geography" / "ds_divisions.json"
LA_GEO_FILE = ROOT / "data" / "geography" / "local_authorities.json"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def clean(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in {"nan", "none", "null", "-"}:
        return None
    return re.sub(r"\s+", " ", s)

def norm(v):
    s = clean(v) or ""
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\b(divisional|district|secretariat|municipal|urban|pradeshiya|sabha|council)\b", " ", s, flags=re.I)
    s = re.sub(r"[^a-z0-9]+", "", s.lower())
    return s

def split_emails(v):
    s = clean(v)
    if not s:
        return []
    parts = re.split(r"[,/;\s]+", s)
    out = []
    for p in parts:
        p = p.strip(" .")
        if "@" in p and "." in p.split("@")[-1]:
            out.append(p)
    return list(dict.fromkeys(out))

def split_phones(v):
    s = clean(v)
    if not s:
        return []
    # Keep readable source strings; do not invent E.164 conversions.
    parts = [p.strip() for p in re.split(r"[,;/]+", s) if p.strip()]
    return list(dict.fromkeys(parts))

def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text

def get_tables(url):
    html = fetch_html(url)
    tables = pd.read_html(StringIO(html))
    return tables

def normalize_columns(df):
    df = df.copy()
    df.columns = [clean(c) or "" for c in df.columns]
    return df

def choose_tables(tables, required_any):
    selected = []
    for idx, t in enumerate(tables):
        t = normalize_columns(t)
        cols = {str(c).strip().lower() for c in t.columns}
        if any(req.lower() in cols for req in required_any):
            selected.append((idx, t))
    return selected

def harvest_ds_contacts():
    tables = get_tables(IO_URL)
    rows = []

    for idx, df in choose_tables(tables, ["Divisional Secretariat", "Organization Type"]):
        cols = {c.lower(): c for c in df.columns}
        org_type_col = cols.get("organization type")
        ds_col = cols.get("divisional secretariat")
        district_col = cols.get("district")
        province_col = cols.get("province")

        if not (org_type_col and ds_col and district_col):
            continue

        for _, r in df.iterrows():
            org_type = clean(r.get(org_type_col))
            if not org_type or "divisional secretariat" not in org_type.lower():
                continue

            division = clean(r.get(ds_col))
            district = clean(r.get(district_col))
            province = clean(r.get(province_col)) if province_col else None
            if not division or not district:
                continue

            row = {
                "division": division,
                "district": district,
                "province": province,
                "organization": clean(r.get(cols.get("organization"))) if cols.get("organization") else None,
                "organization_type": org_type,
                "officer": {
                    "title": clean(r.get(cols.get("title"))) if cols.get("title") else None,
                    "name": clean(r.get(cols.get("name"))) if cols.get("name") else None,
                    "designation": clean(r.get(cols.get("designation"))) if cols.get("designation") else None,
                },
                "address": [
                    clean(r.get(cols.get("address 01"))) if cols.get("address 01") else None,
                    clean(r.get(cols.get("address 02"))) if cols.get("address 02") else None,
                    clean(r.get(cols.get("address 03"))) if cols.get("address 03") else None,
                ],
                "telephone_01": split_phones(r.get(cols.get("telephone 01"))) if cols.get("telephone 01") else [],
                "telephone_02": split_phones(r.get(cols.get("telephone 02"))) if cols.get("telephone 02") else [],
                "fax": split_phones(r.get(cols.get("fax"))) if cols.get("fax") else [],
                "mobile": split_phones(r.get(cols.get("moblie no"))) if cols.get("moblie no") else [],
                "email": split_emails(r.get(cols.get("email"))) if cols.get("email") else [],
                "source_url": IO_URL,
                "source_type": "RTI Information Officer directory",
                "contact_purpose": "RTI / office-directory verification; not automatically a general complaint channel",
                "retrieved_at": now_iso(),
                "_source_table": idx
            }
            row["address"] = [x for x in row["address"] if x]
            rows.append(row)

    # Aggregate by district + division.
    grouped = {}
    for row in rows:
        key = (norm(row["district"]), norm(row["division"]))
        g = grouped.setdefault(key, {
            "division": row["division"],
            "district": row["district"],
            "province": row["province"],
            "source_url": IO_URL,
            "source_type": "RTI Information Officer directory",
            "contact_purpose": "RTI / office-directory verification; not automatically a general complaint channel",
            "officer_records": []
        })
        g["officer_records"].append({
            k: v for k, v in row.items()
            if not k.startswith("_") and k not in {
                "division","district","province","source_url","source_type","contact_purpose"
            }
        })

    return list(grouped.values()), len(rows), len(tables)

def harvest_local_authorities():
    tables = get_tables(DO_URL)
    rows = []
    wanted = ("municipal council", "urban council", "pradeshiya sabha")

    for idx, df in choose_tables(tables, ["Organization", "Organization Type"]):
        cols = {c.lower(): c for c in df.columns}
        org_col = cols.get("organization")
        org_type_col = cols.get("organization type")
        district_col = cols.get("district")
        province_col = cols.get("province")

        if not (org_col and org_type_col):
            continue

        for _, r in df.iterrows():
            org_type = (clean(r.get(org_type_col)) or "").lower()
            if not any(x in org_type for x in wanted):
                continue

            organization = clean(r.get(org_col))
            if not organization:
                continue

            row = {
                "organization": organization,
                "organization_type": clean(r.get(org_type_col)),
                "district": clean(r.get(district_col)) if district_col else None,
                "province": clean(r.get(province_col)) if province_col else None,
                "provincial_council_area": clean(r.get(cols.get("provincial council area"))) if cols.get("provincial council area") else None,
                "officer": {
                    "title": clean(r.get(cols.get("title"))) if cols.get("title") else None,
                    "name": clean(r.get(cols.get("name"))) if cols.get("name") else None,
                    "designation": clean(r.get(cols.get("designation"))) if cols.get("designation") else None,
                },
                "address": [
                    clean(r.get(cols.get("address 01"))) if cols.get("address 01") else None,
                    clean(r.get(cols.get("address 02"))) if cols.get("address 02") else None,
                    clean(r.get(cols.get("address 03"))) if cols.get("address 03") else None,
                ],
                "telephone_01": split_phones(r.get(cols.get("telephone 01"))) if cols.get("telephone 01") else [],
                "telephone_02": split_phones(r.get(cols.get("telephone 02"))) if cols.get("telephone 02") else [],
                "fax": split_phones(r.get(cols.get("fax"))) if cols.get("fax") else [],
                "mobile": split_phones(r.get(cols.get("moblie no"))) if cols.get("moblie no") else [],
                "email": split_emails(r.get(cols.get("email"))) if cols.get("email") else [],
                "source_url": DO_URL,
                "source_type": "RTI Designated Officer directory",
                "contact_purpose": "RTI / office-directory verification; not automatically a general complaint channel",
                "retrieved_at": now_iso(),
                "_source_table": idx
            }
            row["address"] = [x for x in row["address"] if x]
            rows.append(row)

    grouped = {}
    for row in rows:
        key = (norm(row.get("district")), norm(row["organization"]))
        g = grouped.setdefault(key, {
            "organization": row["organization"],
            "organization_type": row["organization_type"],
            "district": row["district"],
            "province": row["province"],
            "source_url": DO_URL,
            "source_type": "RTI Designated Officer directory",
            "contact_purpose": "RTI / office-directory verification; not automatically a general complaint channel",
            "officer_records": []
        })
        g["officer_records"].append({
            k: v for k, v in row.items()
            if not k.startswith("_") and k not in {
                "organization","organization_type","district","province",
                "source_url","source_type","contact_purpose"
            }
        })

    return list(grouped.values()), len(rows), len(tables)

def similarity(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()

def match_ds_to_geography(ds_contacts):
    if not DS_GEO_FILE.exists():
        return {
            "status": "geography_file_not_found",
            "expected_path": str(DS_GEO_FILE),
            "matches": [],
            "unmatched": []
        }

    with open(DS_GEO_FILE, encoding="utf-8") as f:
        geo = json.load(f)
    geo_records = geo.get("records", [])

    by_district = {}
    for g in geo_records:
        by_district.setdefault(norm(g.get("district")), []).append(g)

    matches = []
    unmatched = []
    for c in ds_contacts:
        candidates = by_district.get(norm(c.get("district")), [])
        exact = [g for g in candidates if norm(g.get("name")) == norm(c.get("division"))]
        if len(exact) == 1:
            matches.append({
                "status": "exact",
                "contact_division": c["division"],
                "contact_district": c["district"],
                "geography_id": exact[0].get("id"),
                "geography_name": exact[0].get("name")
            })
            continue

        ranked = sorted(
            ((similarity(c["division"], g.get("name")), g) for g in candidates),
            key=lambda x: x[0],
            reverse=True
        )
        suggestions = [
            {
                "score": round(score, 3),
                "geography_id": g.get("id"),
                "geography_name": g.get("name")
            }
            for score, g in ranked[:3]
        ]
        unmatched.append({
            "contact_division": c["division"],
            "contact_district": c["district"],
            "suggestions": suggestions,
            "action": "manual_review_required"
        })

    return {
        "status": "completed",
        "exact_match_count": len(matches),
        "manual_review_count": len(unmatched),
        "matches": matches,
        "unmatched": unmatched
    }

def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def main():
    print("Yomu Step 3A — harvesting official RTI directory contacts...\n")

    try:
        ds_contacts, ds_rows, io_table_count = harvest_ds_contacts()
        print(f"DS offices harvested: {len(ds_contacts)}")
        print(f"DS officer rows read : {ds_rows}")
    except Exception as e:
        print("ERROR while reading RTI Information Officer directory:")
        print(repr(e))
        sys.exit(1)

    try:
        la_contacts, la_rows, do_table_count = harvest_local_authorities()
        print(f"Local authorities harvested: {len(la_contacts)}")
        print(f"Local authority officer rows : {la_rows}")
    except Exception as e:
        print("ERROR while reading RTI Designated Officer directory:")
        print(repr(e))
        sys.exit(1)

    ds_payload = {
        "dataset": "Yomu Divisional Secretariat official-directory contacts",
        "warning": (
            "These contacts are harvested from the official Sri Lanka RTI directory. "
            "They verify office/contact information but are NOT automatically the correct "
            "channel for an ordinary service complaint. Yomu must keep complaint routes separate."
        ),
        "retrieved_at": now_iso(),
        "records": ds_contacts
    }

    la_payload = {
        "dataset": "Yomu Local Authority official-directory contacts",
        "warning": (
            "These contacts are harvested from the official Sri Lanka RTI directory. "
            "They verify office/contact information but are NOT automatically the correct "
            "channel for an ordinary service complaint."
        ),
        "retrieved_at": now_iso(),
        "records": la_contacts
    }

    match_report = match_ds_to_geography(ds_contacts)

    report = {
        "generated_at": now_iso(),
        "sources": {
            "divisional_secretariats": IO_URL,
            "local_authorities": DO_URL
        },
        "counts": {
            "io_html_tables_found": io_table_count,
            "do_html_tables_found": do_table_count,
            "unique_ds_offices_harvested": len(ds_contacts),
            "ds_officer_rows_harvested": ds_rows,
            "unique_local_authorities_harvested": len(la_contacts),
            "local_authority_officer_rows_harvested": la_rows,
        },
        "matching": {
            "ds_to_dcs_geography_status": match_report.get("status"),
            "exact_match_count": match_report.get("exact_match_count"),
            "manual_review_count": match_report.get("manual_review_count"),
        }
    }

    write_json(CONTACT_DIR / "divisional_secretariat_rti_contacts.json", ds_payload)
    write_json(CONTACT_DIR / "local_authority_rti_contacts.json", la_payload)
    write_json(META_DIR / "ds_contact_match_report.json", match_report)
    write_json(META_DIR / "contact_harvest_report.json", report)

    print("\nSaved:")
    print(" - data/contacts/divisional_secretariat_rti_contacts.json")
    print(" - data/contacts/local_authority_rti_contacts.json")
    print(" - data/meta/ds_contact_match_report.json")
    print(" - data/meta/contact_harvest_report.json")
    print("\nIMPORTANT:")
    print("RTI contacts are a verified directory layer, NOT a general complaint-route layer.")
    print("Any unmatched DS name remains manual-review only; the script never silently guesses.")

if __name__ == "__main__":
    main()
