import json
import re
from pathlib import Path


class BusJurisdictionService:
    DISTRICT_ALIASES = {
        "nuwaraeliya": "Nuwara Eliya",
        "nuwara eliya": "Nuwara Eliya",
        "moneragala": "Monaragala",
        "monaragala": "Monaragala",
        "kilinochchi": "Kilinochchi",
        "kilinochi": "Kilinochchi",
        "mullaitivu": "Mullaitivu",
        "mullativu": "Mullaitivu",
        "trinco": "Trincomalee",
        "trincomalee": "Trincomalee",
        "batti": "Batticaloa",
        "batticaloa": "Batticaloa",
        "putlam": "Puttalam",
        "puttalam": "Puttalam",
        "anuradhapura": "Anuradhapura",
        "polonnaruwa": "Polonnaruwa",
    }

    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        path = self.root / "data" / "routing" / "bus_jurisdiction.json"
        if not path.exists():
            raise FileNotFoundError(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.district_to_province = data["district_to_province"]
        self.province_authorities = data["province_authorities"]
        self.sltb_region_by_district = data["sltb_region_by_district"]

    @staticmethod
    def _norm(value):
        value = re.sub(r"[^a-zA-Z\s]", " ", str(value or "").lower())
        return " ".join(value.split())

    def canonical_district(self, value):
        n = self._norm(value)

        # Exact canonical names first.
        for d in self.district_to_province:
            if self._norm(d) == n:
                return d

        if n in self.DISTRICT_ALIASES:
            return self.DISTRICT_ALIASES[n]

        return None

    def province_for(self, district):
        d = self.canonical_district(district)
        return self.district_to_province.get(d) if d else None

    def resolve_private(self, origin_district, destination_district):
        origin = self.canonical_district(origin_district)
        dest = self.canonical_district(destination_district)

        if not origin:
            return {"status": "invalid_district", "field": "origin_district"}
        if not dest:
            return {"status": "invalid_district", "field": "destination_district"}

        op = self.district_to_province[origin]
        dp = self.district_to_province[dest]

        if op != dp:
            return {
                "status": "resolved",
                "service_type": "private",
                "jurisdiction": "inter_provincial_private",
                "origin_district": origin,
                "destination_district": dest,
                "origin_province": op,
                "destination_province": dp,
                "authority_name": "National Transport Commission",
                "reason": "Private bus route crosses provincial boundaries."
            }

        return {
            "status": "resolved",
            "service_type": "private",
            "jurisdiction": "intra_provincial_private",
            "origin_district": origin,
            "destination_district": dest,
            "origin_province": op,
            "destination_province": dp,
            "authority_name": self.province_authorities[op],
            "reason": "Private bus route remains within one province."
        }

    def resolve_sltb(self, incident_district):
        district = self.canonical_district(incident_district)
        if not district:
            return {"status": "invalid_district", "field": "incident_district"}

        regional = self.sltb_region_by_district.get(district)

        return {
            "status": "resolved",
            "service_type": "sltb",
            "jurisdiction": "sltb",
            "incident_district": district,
            "incident_province": self.district_to_province[district],
            "authority_name": "Sri Lanka Transport Board",
            "regional_sltb": regional,
            "reason": "Complaint concerns an SLTB-operated bus."
        }

    def resolve_unknown(self, incident_district):
        district = self.canonical_district(incident_district)
        if not district:
            return {"status": "invalid_district", "field": "incident_district"}

        return {
            "status": "resolved",
            "service_type": "not_sure",
            "jurisdiction": "unknown_operator_ntc_intake",
            "incident_district": district,
            "incident_province": self.district_to_province[district],
            "authority_name": "National Transport Commission",
            "reason": (
                "Operator type is unknown. NTC is used as a verified complaint intake route; "
                "NTC can forward provincial-bus and SLTB complaints to the appropriate body."
            )
        }
