from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.complaint_router import ComplaintRouter

router = ComplaintRouter(ROOT)

answers = {
    "district": "Matale",
    "ds_division": "Matale",
    "local_authority_choice": "Matale PS",
}

result = router.route("garbage_collection", answers)

print(json.dumps(result, ensure_ascii=False, indent=2))

assert result["status"] == "routed"
assert result["route_type"] == "local_authority"
assert result["local_authority"]["name"] == "Matale PS"

print("\nLOCAL AUTHORITY CHOICE FIX: PASSED")
