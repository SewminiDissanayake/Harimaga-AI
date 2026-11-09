from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contacts" / "police_station_contacts.json"
URL = "https://www.police.lk/?page_id=1301"


def clean(v):
    if v is None:
        return ""
    return " ".join(str(v).replace("\xa0", " ").split())


def main():
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is required for this refresh script.")
        print("Install it or use the official Police Telephone Index directly:")
        print(URL)
        sys.exit(1)

    try:
        tables = pd.read_html(URL)
    except Exception as e:
        print("Could not read the live Sri Lanka Police Telephone Index.")
        print("Reason:", e)
        print("Use the official directory directly:")
        print(URL)
        sys.exit(1)

    records = []
    seen = set()

    for table in tables:
        table.columns = [clean(c) for c in table.columns]

        # Flexible lookup because the website may slightly change column names.
        colmap = {c.lower(): c for c in table.columns}

        station_col = None
        for c in table.columns:
            if "designation" in c.lower() or "station" in c.lower():
                station_col = c
                break

        if station_col is None:
            continue

        general_col = next((c for c in table.columns if c.lower() == "general"), None)
        mobile_col = next((c for c in table.columns if c.lower() == "mobile"), None)
        email_col = next((c for c in table.columns if c.lower() == "email"), None)

        for _, row in table.iterrows():
            station = clean(row.get(station_col, ""))

            if not re.search(r"\bPolice Station\b", station, flags=re.I):
                continue

            record = {
                "station": station,
                "general": clean(row.get(general_col, "")) if general_col else "",
                "mobile": clean(row.get(mobile_col, "")) if mobile_col else "",
                "email": clean(row.get(email_col, "")) if email_col else "",
                "source_url": URL,
            }

            key = (
                record["station"].lower(),
                record["general"],
                record["mobile"],
                record["email"].lower(),
            )

            if key in seen:
                continue

            seen.add(key)
            records.append(record)

    if not records:
        print("No police-station rows were parsed.")
        print("The website structure may have changed.")
        print("Use the official directory:")
        print(URL)
        sys.exit(1)

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": URL,
                "record_type": "Sri Lanka Police station contact directory snapshot",
                "count": len(records),
                "records": sorted(records, key=lambda x: x["station"].lower()),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("POLICE STATION DIRECTORY REFRESH: PASSED")
    print("Stations saved:", len(records))
    print("Saved:", OUT)


if __name__ == "__main__":
    main()
