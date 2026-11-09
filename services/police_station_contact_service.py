import json
import re
from pathlib import Path


class PoliceStationContactService:
    OFFICIAL_INDEX = "https://www.police.lk/?page_id=1301"

    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.snapshot = self.root / "data" / "contacts" / "police_station_contacts.json"
        self.records = []

        if self.snapshot.exists():
            with open(self.snapshot, encoding="utf-8") as f:
                payload = json.load(f)
            self.records = payload.get("records", [])

    @staticmethod
    def _norm(value):
        value = re.sub(r"[^a-zA-Z0-9\s]", " ", str(value or "").lower())
        return " ".join(value.split())

    def search(self, station_or_town, limit=5):
        q = self._norm(station_or_town)
        if not q or not self.records:
            return []

        scored = []
        for row in self.records:
            station = self._norm(row.get("station"))
            if q == station or q == station.replace(" police station", ""):
                score = 100
            elif q in station:
                score = 80
            else:
                q_words = set(q.split())
                s_words = set(station.split())
                overlap = len(q_words & s_words)
                score = overlap * 10

            if score > 0:
                scored.append((score, row))

        scored.sort(key=lambda x: (-x[0], self._norm(x[1].get("station"))))
        return [row for _, row in scored[:limit]]
