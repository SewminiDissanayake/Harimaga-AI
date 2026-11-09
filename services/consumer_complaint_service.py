import json
import re
from pathlib import Path


class ConsumerComplaintService:
    DISTRICT_ALIASES = {
        "nuwaraeliya": "Nuwara Eliya",
        "nuwara eliya": "Nuwara Eliya",
        "moneragala": "Monaragala",
        "monaragala": "Monaragala",
        "kilinochi": "Kilinochchi",
        "kilinochchi": "Kilinochchi",
        "mullativu": "Mullaitivu",
        "mullaitivu": "Mullaitivu",
        "trinco": "Trincomalee",
        "batti": "Batticaloa",
        "putlam": "Puttalam",
    }

    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        path = self.root / "data" / "routing" / "consumer_complaint_routes.json"
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    @staticmethod
    def _norm(v):
        v = re.sub(r"[^a-zA-Z\s]", " ", str(v or "").lower())
        return " ".join(v.split())

    def canonical_district(self, value):
        n = self._norm(value)
        for d in self.data["district_contacts"]:
            if self._norm(d) == n:
                return d
        return self.DISTRICT_ALIASES.get(n)

    def resolve(self, district, subtype_key):
        d = self.canonical_district(district)
        if not d:
            return {"status":"invalid_district"}

        subtype = self.data["complaint_subtypes"].get(subtype_key)
        if not subtype:
            return {"status":"invalid_subtype"}

        return {
            "status":"resolved",
            "authority": self.data["authority"],
            "district": d,
            "district_office": self.data["district_contacts"][d],
            "subtype_key": subtype_key,
            "subtype_label": subtype["label"],
            "required_information": subtype["required_information"],
            "time_note": self.data["policy"]["time_note"],
            "safety": self.data["policy"]["safety"]
        }

    def subtype_options(self):
        return [
            (key, value["label"])
            for key, value in self.data["complaint_subtypes"].items()
        ]
