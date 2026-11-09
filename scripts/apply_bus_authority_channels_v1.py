import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "routing" / "provider_issue_channels.json"
PATCH = ROOT / "bus_authority_channels_patch_v1.json"

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    if not TARGET.exists():
        raise FileNotFoundError(
            f"Missing {TARGET}. Install the water/electricity provider-channel layer first."
        )
    if not PATCH.exists():
        raise FileNotFoundError(PATCH)

    data = load(TARGET)
    patch = load(PATCH)
    records = data.setdefault("records", [])

    keys = {(r["authority_key"], r["issue_key"]) for r in patch["records"]}
    kept = [
        r for r in records
        if (r.get("authority_key"), r.get("issue_key")) not in keys
    ]
    kept.extend(patch["records"])
    data["records"] = kept
    data["last_extended_on"] = patch.get("verified_on")

    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("HariMaga Bus Complaint Authority Patch")
    print("--------------------------------------")
    print("Bus authority records added/updated :", len(patch["records"]))
    print("Authority/provider issue records now:", len(kept))
    print("Saved                              :", TARGET)

if __name__ == "__main__":
    main()
