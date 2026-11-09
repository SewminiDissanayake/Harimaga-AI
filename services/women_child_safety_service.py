import json
from pathlib import Path


class WomenChildSafetyService:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        path = self.root / "data" / "routing" / "women_child_safety_routes.json"
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def subtype_options(self):
        return [(k, v["label"]) for k, v in self.data["subtypes"].items()]

    def resolve(self, subtype_key, immediate_danger=False):
        subtype = self.data["subtypes"].get(subtype_key)
        if not subtype:
            return {"status": "invalid_subtype"}

        keys = list(subtype["recommended_contacts"])

        if immediate_danger:
            keys = ["police_emergency", "children_women_bureau"] + keys

        seen = set()
        contacts = []
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            contact = self.data["contacts"].get(key)
            if contact:
                contacts.append(contact)

        return {
            "status": "resolved",
            "subtype_key": subtype_key,
            "subtype_label": subtype["label"],
            "immediate_danger": bool(immediate_danger),
            "contacts": contacts,
            "required_information": subtype["required_information"],
            "policy": self.data["policy"],
            "tell_igp": self.data["contacts"]["tell_igp"],
        }
