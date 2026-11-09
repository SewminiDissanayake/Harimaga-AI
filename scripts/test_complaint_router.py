import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.complaint_router import ComplaintRouter

router = ComplaintRouter(ROOT)

tests = [
    (
        "WATER - NWSDB",
        "water_issue",
        {"service_provider_or_scheme": "NWSDB", "district": "Kandy"}
    ),
    (
        "ELECTRICITY - UNKNOWN PROVIDER",
        "electricity_issue",
        {}
    ),
    (
        "GARBAGE - KUNDASALE",
        "garbage_collection",
        {"district": "Kandy", "ds_division": "Kundasale"}
    ),
    (
        "ROAD - NATIONAL",
        "road_issue",
        {"road_type": "national road", "district": "Matale"}
    ),
]

for title, issue, answers in tests:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    result = router.route(issue, answers)
    print(json.dumps(result, indent=2, ensure_ascii=False))
