"""
check_contact_freshness.py
--------------------------
Hotlines, emails and websites change over time. This script finds every
verification date in the routing / contact data and lists the files that
were checked longer ago than the limit (default 180 days = about 6 months).

Run:
    python scripts/check_contact_freshness.py
    python scripts/check_contact_freshness.py --days 90

Exit code 1 means something is due for re-checking (useful in CI).
"""
import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIRS = [ROOT / "data" / "routing", ROOT / "data" / "contacts"]
DATE_KEYS = {"verified_at", "verified_on", "retrieved_at", "last_extended_on"}


def find_dates(obj, found):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in DATE_KEYS and isinstance(value, str):
                try:
                    found.append(datetime.fromisoformat(value[:10]).date())
                except ValueError:
                    pass
            find_dates(value, found)
    elif isinstance(obj, list):
        for item in obj:
            find_dates(item, found)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=180)
    args = parser.parse_args()

    today = date.today()
    report = defaultdict(list)
    for folder in DATA_DIRS:
        for path in sorted(folder.glob("*.json")):
            dates = []
            find_dates(json.loads(path.read_text(encoding="utf-8")), dates)
            if dates:
                report[path.relative_to(ROOT).as_posix()] = dates

    due = 0
    print(f"Contact data freshness (limit: {args.days} days, today: {today})\n")
    for name, dates in report.items():
        oldest = min(dates)
        age = (today - oldest).days
        status = "RE-CHECK" if age > args.days else "ok"
        due += status == "RE-CHECK"
        print(f"  [{status:8}] {name:62} oldest {oldest} ({age} days, {len(dates)} records)")

    print()
    if due:
        print(f"{due} file(s) need their official sources checked again.")
        sys.exit(1)
    print("All contact data is within the limit.")


if __name__ == "__main__":
    main()
