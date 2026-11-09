import json
from pathlib import Path


class DisasterAlertService:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        path = self.root / "data" / "routing" / "disaster_alert_routes.json"
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def alert_options(self):
        return [(k, v["label"]) for k, v in self.data["alert_types"].items()]

    def resolve(self, alert_key, district=None):
        alert = self.data["alert_types"].get(alert_key)
        if not alert:
            return {"status": "invalid_alert_type"}

        return {
            "status": "resolved",
            "alert_key": alert_key,
            "label": alert["label"],
            "district": district,
            "technical_authority": alert["technical_authority"],
            "live_sources": alert["live_sources"],
            "technical_contacts": alert["contacts"],
            "dmc_contacts": list(self.data["common_contacts"].values()),
            "required_information": alert["required_information"],
            "policy": self.data["policy"],
        }
