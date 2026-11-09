import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTING = ROOT / "data" / "routing"

with open(ROUTING / "complaint_channels.json", encoding="utf-8") as f:
    channels = json.load(f)["records"]

with open(ROUTING / "routing_rules.json", encoding="utf-8") as f:
    rules = json.load(f)["rules"]

errors = []

for issue, rule in rules.items():
    for key, target in rule["routes"].items():
        if target.startswith("ask_") or target == "local_authority_from_geography":
            continue
        if target not in channels:
            errors.append(f"{issue} -> {key}: unknown target '{target}'")

for authority_id, rec in channels.items():
    if not rec.get("source_urls"):
        errors.append(f"{authority_id}: missing source_urls")
    if not rec.get("verified_at"):
        errors.append(f"{authority_id}: missing verified_at")
    if not rec.get("channels"):
        errors.append(f"{authority_id}: no complaint/contact channel")

print("Authorities:", len(channels))
print("Issue rules:", len(rules))

if errors:
    print("\nVALIDATION FAILED")
    for e in errors:
        print("-", e)
else:
    print("\nVALIDATION PASSED")
    print("All routing targets point to known verified authorities or explicit clarification/local-authority actions.")
