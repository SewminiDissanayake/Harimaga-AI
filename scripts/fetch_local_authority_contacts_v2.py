import csv
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
GEO_FILE = ROOT / "data" / "geography" / "local_authorities.json"
CONTACT_OUT = ROOT / "data" / "contacts" / "local_authority_official_directory_contacts.json"
MATCH_OUT = ROOT / "data" / "meta" / "local_authority_contact_match_report.json"
REVIEW_OUT = ROOT / "data" / "meta" / "local_authority_manual_review.csv"

RTI_DO_URL = "https://rti.gov.lk/do-list/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HariMagaAI-StudentProject/1.0)"
}

LA_TYPES = {
    "municipal council": "municipal_council",
    "urban council": "urban_council",
    "pradeshiya sabha": "pradeshiya_sabha",
}

TYPE_SUFFIX = {
    "municipal_council": "MC",
    "urban_council": "UC",
    "pradeshiya_sabha": "PS",
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def clean(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in {"nan", "none", "null", "-"}:
        return None
    return re.sub(r"\s+", " ", s)

def ascii_norm(v):
    s = clean(v) or ""
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("–", "-").replace("—", "-").replace("&", " and ")
    s = s.lower()

    # spelling / transliteration normalizations seen in official directories
    replacements = {
        "negambo": "negombo",
        "meerigama": "mirigama",
        "aththanagalla": "attanagalla",
        "waththegama": "wattegama",
        "harispaththuwa": "harispattuwa",
        "madadumbara": "medadumbara",
        "ududumbara": "udadumbara",
        "panwila": "panvila",
        "walallawita": "walallavita",
        "bulathsinghala": "bulathsinhala",
        "pathahewahaheta": "pathahewaheta",
        "rajgama": "rathgama",
        "pachchileppalei": "pachchilaipalli",
        "marritimepattu": "maritimepattu",
        "karaitivu": "karaitheevu",
        "dehiaththakandiya": "dehiattakandiya",
        "ridimaliyadda": "rideemaliyadda",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)

    s = re.sub(
        r"\b(municipal|urban|pradeshiya|sabha|council|municipality)\b",
        " ",
        s,
    )
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def norm_district(v):
    s = ascii_norm(v)
    aliases = {
        "rathnapura": "ratnapura",
        "monaragala": "moneragala",
        "hambanthota": "hambantota",
        "nuwaraeliya": "nuwaraeliya",
    }
    return aliases.get(s, s)

def split_phones(v):
    s = clean(v)
    if not s:
        return []
    parts = [p.strip() for p in re.split(r"[,;/]+", s) if p.strip()]
    return list(dict.fromkeys(parts))

def split_emails(v):
    s = clean(v)
    if not s:
        return []
    # Preserve only syntactically plausible email strings.
    candidates = re.split(r"[,;/\s]+", s)
    out = []
    for item in candidates:
        item = item.strip(" .")
        if item.count("@") == 1 and "." in item.split("@", 1)[1]:
            out.append(item)
    return list(dict.fromkeys(out))

def fetch_tables():
    r = requests.get(RTI_DO_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return pd.read_html(StringIO(r.text))

def flatten_columns(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        cols = []
        for tup in df.columns:
            parts = [clean(x) for x in tup if clean(x)]
            cols.append(" ".join(parts))
        df.columns = cols
    else:
        df.columns = [clean(c) or "" for c in df.columns]
    return df

def find_col(cols, *names):
    lookup = {re.sub(r"\s+", " ", str(c).strip().lower()): c for c in cols}
    for name in names:
        key = name.strip().lower()
        if key in lookup:
            return lookup[key]
    return None

def infer_type(org_type, organization):
    blob = " ".join(x for x in [clean(org_type), clean(organization)] if x).lower()
    for human, machine in LA_TYPES.items():
        if human in blob:
            return machine
    return None

def area_from_row(row, cols, la_type):
    # IMPORTANT: RTI's council table stores the real local-authority name in
    # "MC/UC/PS area Name". The older HariMaga/Yomu parser mistakenly grouped
    # by the generic "Organization" value (e.g. "Pradeshiya Sabha").
    area_col = find_col(
        cols,
        "MC/UC/PS area Name",
        "MC / UC / PS area Name",
        "MC/UC/PS Area Name",
    )
    if area_col:
        area = clean(row.get(area_col))
        if area:
            return area, "rti_area_column"

    org_col = find_col(cols, "Organization")
    org = clean(row.get(org_col)) if org_col else None

    # Fallback only when the organization itself contains a real place name,
    # e.g. "Horana Urban Council". Reject generic values like "Urban Council".
    if org:
        generic = {"municipal council", "urban council", "pradeshiya sabha", "provincial council"}
        if org.lower() not in generic:
            stripped = re.sub(
                r"\b(municipal council|urban council|pradeshiya sabha)\b",
                "",
                org,
                flags=re.I,
            ).strip(" -–—")
            if stripped:
                return stripped, "organization_name_fallback"

    return None, "missing_area"

def harvest():
    tables = fetch_tables()
    harvested = []

    for table_index, raw in enumerate(tables):
        df = flatten_columns(raw)
        cols = list(df.columns)

        district_col = find_col(cols, "District")
        province_col = find_col(cols, "Province")
        org_col = find_col(cols, "Organization")
        org_type_col = find_col(cols, "Organization Type")
        title_col = find_col(cols, "Title")
        name_col = find_col(cols, "Name")
        designation_col = find_col(cols, "Designation")

        # Only tables with the required location/type structure.
        if not district_col or not org_type_col:
            continue

        for _, row in df.iterrows():
            la_type = infer_type(
                row.get(org_type_col),
                row.get(org_col) if org_col else None,
            )
            if not la_type:
                continue

            area, area_source = area_from_row(row, cols, la_type)
            district = clean(row.get(district_col))
            province = clean(row.get(province_col)) if province_col else None

            # We keep incomplete rows for manual review rather than guessing.
            if not district:
                continue

            addr = []
            for c_name in ("Address 01", "Address 02", "Address 03"):
                c = find_col(cols, c_name)
                if c:
                    v = clean(row.get(c))
                    if v:
                        addr.append(v)

            t1 = find_col(cols, "Telephone 01")
            t2 = find_col(cols, "Telephone 02")
            fax = find_col(cols, "Fax")
            mob = find_col(cols, "Moblie No", "Mobile No")
            email = find_col(cols, "Email")

            harvested.append({
                "area_name": area,
                "area_name_source": area_source,
                "la_type": la_type,
                "organization": clean(row.get(org_col)) if org_col else None,
                "organization_type_raw": clean(row.get(org_type_col)),
                "district": district,
                "province": province,
                "officer": {
                    "title": clean(row.get(title_col)) if title_col else None,
                    "name": clean(row.get(name_col)) if name_col else None,
                    "designation": clean(row.get(designation_col)) if designation_col else None,
                },
                "address": addr,
                "telephone_01": split_phones(row.get(t1)) if t1 else [],
                "telephone_02": split_phones(row.get(t2)) if t2 else [],
                "fax": split_phones(row.get(fax)) if fax else [],
                "mobile": split_phones(row.get(mob)) if mob else [],
                "email": split_emails(row.get(email)) if email else [],
                "source_url": RTI_DO_URL,
                "source_type": "Sri Lanka RTI Designated Officer directory",
                "contact_purpose": (
                    "Official council/office directory fallback. "
                    "Do not label this as an issue-specific complaint channel unless separately verified."
                ),
                "retrieved_at": now_iso(),
                "_source_table": table_index,
            })

    return harvested, len(tables)

def load_geography():
    if not GEO_FILE.exists():
        raise FileNotFoundError(f"Missing geography file: {GEO_FILE}")
    with open(GEO_FILE, encoding="utf-8") as f:
        payload = json.load(f)
    return payload["records"]

def similarity(a, b):
    return SequenceMatcher(None, ascii_norm(a), ascii_norm(b)).ratio()

def match_to_geography(rows, geo):
    by_district_type = {}
    by_type_name = {}

    for g in geo:
        dt = (norm_district(g["district"]), g["type"])
        by_district_type.setdefault(dt, []).append(g)
        key = (g["type"], ascii_norm(g["name"]))
        by_type_name.setdefault(key, []).append(g)

    matches = []
    manual = []

    for r in rows:
        if not r["area_name"]:
            manual.append({
                **r,
                "match_status": "manual_review",
                "reason": "missing_area_name_in_rti_row",
                "suggestions": [],
            })
            continue

        district_key = norm_district(r["district"])
        candidates = by_district_type.get((district_key, r["la_type"]), [])

        exact = [
            g for g in candidates
            if ascii_norm(g["name"]) == ascii_norm(r["area_name"])
        ]

        if len(exact) == 1:
            g = exact[0]
            matches.append({
                **r,
                "match_status": "exact",
                "geography_id": g["id"],
                "geography_name": g["name"],
                "geography_district": g["district"],
                "geography_type": g["type"],
            })
            continue

        # Safe second route: name + type is exact and nationally unique.
        national_exact = by_type_name.get((r["la_type"], ascii_norm(r["area_name"])), [])
        if len(national_exact) == 1:
            g = national_exact[0]
            matches.append({
                **r,
                "match_status": "exact_name_type_unique_national",
                "geography_id": g["id"],
                "geography_name": g["name"],
                "geography_district": g["district"],
                "geography_type": g["type"],
                "source_district_warning": (
                    None if norm_district(g["district"]) == district_key
                    else f"RTI district '{r['district']}' differs from geography district '{g['district']}'."
                ),
            })
            continue

        ranked = sorted(
            ((similarity(r["area_name"], g["name"]), g) for g in candidates),
            key=lambda x: x[0],
            reverse=True,
        )
        suggestions = [
            {
                "score": round(score, 3),
                "geography_id": g["id"],
                "geography_name": g["name"],
                "geography_type": g["type"],
                "geography_district": g["district"],
            }
            for score, g in ranked[:3]
        ]

        manual.append({
            **r,
            "match_status": "manual_review",
            "reason": "no_safe_exact_match",
            "suggestions": suggestions,
        })

    return matches, manual

def aggregate_matched(matches):
    grouped = {}

    for r in matches:
        gid = r["geography_id"]
        g = grouped.setdefault(gid, {
            "geography_id": gid,
            "name": r["geography_name"],
            "district": r["geography_district"],
            "type": r["geography_type"],
            "directory_contact_status": "official_rti_directory",
            "complaint_channel_status": "not_yet_issue_specific",
            "source_url": RTI_DO_URL,
            "officer_records": [],
        })

        g["officer_records"].append({
            "officer": r["officer"],
            "address": r["address"],
            "telephone_01": r["telephone_01"],
            "telephone_02": r["telephone_02"],
            "fax": r["fax"],
            "mobile": r["mobile"],
            "email": r["email"],
            "match_status": r["match_status"],
            "source_district": r["district"],
            "source_district_warning": r.get("source_district_warning"),
        })

    return list(grouped.values())

def write_manual_csv(path, manual):
    fields = [
        "contact_district",
        "contact_area_name",
        "contact_la_type",
        "reason",
        "top1_geography_name",
        "top1_score",
        "top2_geography_name",
        "top2_score",
        "top3_geography_name",
        "top3_score",
        "review_status",
        "approved_geography_id",
        "notes",
    ]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()

        for r in manual:
            suggestions = r.get("suggestions", [])
            out = {
                "contact_district": r.get("district"),
                "contact_area_name": r.get("area_name"),
                "contact_la_type": r.get("la_type"),
                "reason": r.get("reason"),
                "review_status": "",
                "approved_geography_id": "",
                "notes": "",
            }

            for i in range(3):
                s = suggestions[i] if i < len(suggestions) else {}
                out[f"top{i+1}_geography_name"] = s.get("geography_name", "")
                out[f"top{i+1}_score"] = s.get("score", "")

            w.writerow(out)

def main():
    print("HariMaga — Local Authority Official Directory Harvester v2")
    print("Source:", RTI_DO_URL)
    print()

    try:
        rows, table_count = harvest()
        geo = load_geography()
    except Exception as e:
        print("ERROR:", repr(e))
        sys.exit(1)

    matches, manual = match_to_geography(rows, geo)
    aggregated = aggregate_matched(matches)

    CONTACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    MATCH_OUT.parent.mkdir(parents=True, exist_ok=True)

    with open(CONTACT_OUT, "w", encoding="utf-8") as f:
        json.dump({
            "dataset": "HariMaga official local-authority directory contacts",
            "warning": (
                "These are official directory / RTI contacts. "
                "They are NOT automatically issue-specific complaint channels."
            ),
            "retrieved_at": now_iso(),
            "records": aggregated,
        }, f, ensure_ascii=False, indent=2)

    matched_ids = {x["geography_id"] for x in matches}
    geography_without_contact = [
        {
            "geography_id": g["id"],
            "name": g["name"],
            "district": g["district"],
            "type": g["type"],
        }
        for g in geo if g["id"] not in matched_ids
    ]

    report = {
        "status": "completed",
        "source": RTI_DO_URL,
        "counts": {
            "html_tables_found": table_count,
            "rti_local_authority_rows_harvested": len(rows),
            "dcs_local_authorities_total": len(geo),
            "safe_matched_rows": len(matches),
            "unique_local_authorities_with_directory_contact": len(aggregated),
            "manual_review_rows": len(manual),
            "geography_without_directory_contact": len(geography_without_contact),
        },
        "manual_review": manual,
        "geography_without_directory_contact": geography_without_contact,
    }

    with open(MATCH_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    write_manual_csv(REVIEW_OUT, manual)

    print("RTI LA rows harvested                 :", len(rows))
    print("DCS local authorities                :", len(geo))
    print("Safe matched rows                    :", len(matches))
    print("Unique LAs with directory contact    :", len(aggregated))
    print("Manual review rows                   :", len(manual))
    print("Geography without directory contact  :", len(geography_without_contact))
    print()
    print("Saved:")
    print(" -", CONTACT_OUT)
    print(" -", MATCH_OUT)
    print(" -", REVIEW_OUT)
    print()
    print("IMPORTANT:")
    print("These are official directory contacts, not automatically garbage/road complaint channels.")
    print("HariMaga will expose them only as an official council-contact fallback until a specific complaint route is verified.")

if __name__ == "__main__":
    main()
