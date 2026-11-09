import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGET = ROOT / "data" / "routing" / "local_authority_issue_channels.json"
PATCH = ROOT / "local_road_channels_patch_v1.json"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    if not TARGET.exists():
        raise FileNotFoundError(
            f"Missing {TARGET}. Install HariMaga Issue-Specific Local Authority Channels v1 first."
        )

    if not PATCH.exists():
        raise FileNotFoundError(PATCH)

    data = load(TARGET)
    patch = load(PATCH)

    records = data.setdefault("records", [])
    before = len(records)

    # Replace any existing record with same authority + issue key.
    patch_keys = {
        (r["geography_id"], r["issue_key"])
        for r in patch.get("records", [])
    }

    kept = [
        r for r in records
        if (r.get("geography_id"), r.get("issue_key")) not in patch_keys
    ]

    kept.extend(patch.get("records", []))
    data["records"] = kept
    data["last_extended_on"] = patch.get("verified_on")

    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    after = len(kept)

    print("HariMaga Local Road Channel Patch")
    print("--------------------------------")
    print("Records before :", before)
    print("Road records added/updated :", len(patch.get("records", [])))
    print("Records after  :", after)
    print("Saved          :", TARGET)


if __name__ == "__main__":
    main()
