import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "routing" / "local_authority_issue_channels.json"
PATCH = ROOT / "ukuwela_road_channel_patch_v1.json"

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)
    if not PATCH.exists():
        raise FileNotFoundError(PATCH)

    data = load(TARGET)
    patch = load(PATCH)
    records = data.setdefault("records", [])

    patch_keys = {(r["geography_id"], r["issue_key"]) for r in patch["records"]}
    kept = [
        r for r in records
        if (r.get("geography_id"), r.get("issue_key")) not in patch_keys
    ]
    kept.extend(patch["records"])
    data["records"] = kept

    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Ukuwela road channel patch applied.")
    print("Records now:", len(kept))
    print("Saved:", TARGET)

if __name__ == "__main__":
    main()
