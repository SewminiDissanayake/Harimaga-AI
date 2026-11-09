import json
import re
from pathlib import Path


class ComplaintRouter:
    def __init__(self, project_root=None):
        self.root = Path(project_root) if project_root else Path(__file__).resolve().parents[1]

        self.routing_dir = self.root / "data" / "routing"
        self.geo_dir = self.root / "data" / "geography"

        self.channels = self._load(self.routing_dir / "complaint_channels.json")["records"]
        self.rules = self._load(self.routing_dir / "routing_rules.json")["rules"]
        self.required_fields = self._load(self.routing_dir / "required_fields.json")

        self.ds_to_la = self._load(self.geo_dir / "ds_to_local_authorities.json")["records"]
        self.gnd_lookup = self._load(self.geo_dir / "gnd_jurisdiction_lookup.json")["records"]

    @staticmethod
    def _load(path):
        if not path.exists():
            raise FileNotFoundError(f"Missing Yomu data file: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _norm(value):
        value = "" if value is None else str(value)
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9]+", "", value)
        return value

    @staticmethod
    def _value(answers, *keys):
        for key in keys:
            value = answers.get(key)
            if value not in (None, ""):
                return value
        return None

    def _channel_result(self, authority_id, issue_key):
        authority = self.channels[authority_id]
        return {
            "status": "routed",
            "issue_key": issue_key,
            "route_type": "verified_authority",
            "authority_id": authority_id,
            "authority_name": authority["authority_name"],
            "authority_type": authority["authority_type"],
            "channels": authority["channels"],
            "source_urls": authority["source_urls"],
            "verified_at": authority["verified_at"],
            "required_information": self.required_fields.get(issue_key, []),
        }

    def _clarify(self, issue_key, question, needed_field=None, options=None):
        result = {
            "status": "needs_clarification",
            "issue_key": issue_key,
            "question": question,
            "required_information": self.required_fields.get(issue_key, []),
        }
        if needed_field:
            result["needed_field"] = needed_field
        if options:
            result["options"] = options
        return result

    def _ds_options(self, district):
        """v9.3: DS division names for a district, so the user can pick instead of type."""
        names = sorted({
            row.get("ds_name")
            for row in self.ds_to_la
            if row.get("ds_name") and self._norm(row.get("district")) == self._norm(district)
        })
        return names

    def _resolve_local_authority(self, issue_key, answers):
        district = self._value(answers, "district")
        ds_division = self._value(answers, "ds_division", "divisional_secretariat")
        gnd_name = self._value(answers, "gnd_name", "grama_niladhari_division")

        if not district:
            return self._clarify(
                issue_key,
                "Which district is the problem located in?",
                "district",
            )

        if not ds_division:
            return self._clarify(
                issue_key,
                "Which Divisional Secretariat area is the problem located in?",
                "ds_division",
                self._ds_options(district) or None,
            )

        ds_matches = [
            row for row in self.ds_to_la
            if self._norm(row.get("district")) == self._norm(district)
            and self._norm(row.get("ds_name")) == self._norm(ds_division)
        ]

        if not ds_matches:
            return self._clarify(
                issue_key,
                "I could not safely match that District + Divisional Secretariat combination. Please confirm the official DS area name.",
                "ds_division",
                self._ds_options(district) or None,
            )

        local_authorities = ds_matches[0].get("local_authorities", [])

        # If the user explicitly selected one of the local authorities presented
        # by HariMaga, accept that selection directly.
        selected_la = self._value(
            answers,
            "local_authority_choice",
            "local_authority",
        )
        if selected_la:
            selected_norm = self._norm(selected_la)
            selected_matches = [
                la for la in local_authorities
                if self._norm(la.get("name")) == selected_norm
                or self._norm(la.get("id")) == selected_norm
            ]
            if len(selected_matches) == 1:
                la = selected_matches[0]
                return {
                    "status": "routed",
                    "issue_key": issue_key,
                    "route_type": "local_authority",
                    "district": district,
                    "ds_division": ds_matches[0]["ds_name"],
                    "local_authority": la,
                    "required_information": self.required_fields.get(issue_key, []),
                    "note": (
                        "Local authority selected by the user from the valid "
                        "authorities for this DS area."
                    )
                }

        if len(local_authorities) == 1:
            la = local_authorities[0]
            return {
                "status": "routed",
                "issue_key": issue_key,
                "route_type": "local_authority",
                "district": district,
                "ds_division": ds_matches[0]["ds_name"],
                "local_authority": la,
                "required_information": self.required_fields.get(issue_key, []),
                "note": "Local-authority jurisdiction resolved from the DCS/GND geography backbone. Complaint-channel contact details are a separate verified layer."
            }

        if gnd_name:
            gnd_matches = [
                row for row in self.gnd_lookup
                if self._norm(row["district"]["name"]) == self._norm(district)
                and self._norm(row["divisional_secretariat"]["name"]) == self._norm(ds_division)
                and self._norm(row["grma_niladhari_division"]["name"]) == self._norm(gnd_name)
            ]

            if len(gnd_matches) == 1:
                return {
                    "status": "routed",
                    "issue_key": issue_key,
                    "route_type": "local_authority",
                    "district": district,
                    "ds_division": ds_division,
                    "gnd_name": gnd_name,
                    "local_authorities": gnd_matches[0].get("local_authorities", []),
                    "required_information": self.required_fields.get(issue_key, []),
                    "note": "Jurisdiction resolved using the GND-level geography record."
                }

        if len(local_authorities) > 1:
            return self._clarify(
                issue_key,
                (
                    "This DS area overlaps more than one local authority. "
                    "If you know your council, choose it below. "
                    "If not, type your Grama Niladhari Division or a more specific local area."
                ),
                "local_authority_choice",
                [la["name"] for la in local_authorities],
            )

        return self._clarify(
            issue_key,
            "No local-authority mapping was found for this location. Please provide a more specific area or GND.",
            "gnd_name",
        )

    def route(self, issue_key, answers=None):
        answers = answers or {}

        if issue_key not in self.rules:
            issue_key = "unknown_government_issue"

        if issue_key == "water_issue":
            provider = self._norm(self._value(answers, "service_provider_or_scheme", "provider"))
            if provider in {"nwsdb", "waterboard", "nationalwatersupplydrainageboard"}:
                return self._channel_result("nwsdb", issue_key)
            return self._clarify(
                issue_key,
                "Is this service provided by the National Water Supply and Drainage Board (NWSDB), or another/local water scheme?",
                "service_provider_or_scheme",
                ["NWSDB", "Other / local water scheme"],
            )

        if issue_key == "electricity_issue":
            provider = self._norm(self._value(answers, "electricity_provider", "provider"))
            if provider == "ceb":
                return self._channel_result("ceb", issue_key)
            if provider == "leco":
                return self._channel_result("leco", issue_key)
            return self._clarify(
                issue_key,
                "Who is your electricity provider?",
                "electricity_provider",
                ["CEB", "LECO"],
            )

        if issue_key == "road_issue":
            road_type = self._norm(self._value(answers, "road_type_or_class", "road_type"))
            if road_type in {"national", "nationalroad", "rdaroad", "highway", "mainnationalroad"}:
                return self._channel_result("rda", issue_key)
            if road_type in {"local", "localroad", "councilroad", "municipalroad", "pradeshiyasabharoad"}:
                return self._resolve_local_authority(issue_key, answers)
            return self._clarify(
                issue_key,
                "Is the damaged road a national/RDA road or a local council road?",
                "road_type_or_class",
                ["National / RDA road", "Local council road", "Not sure"],
            )

        if issue_key == "garbage_collection":
            return self._resolve_local_authority(issue_key, answers)

        if issue_key == "bus_complaint":
            return self._channel_result("ntc", issue_key)

        if issue_key == "consumer_complaint":
            return self._channel_result("caa", issue_key)

        if issue_key == "environment_issue":
            issue_type = self._norm(self._value(answers, "issue_type", "environment_issue_type"))
            if issue_type in {
                "industrialpollution",
                "hazardouswaste",
                "noisepollution",
                "environmentaldamage",
                "developmentprojectenvironmentalissue",
            }:
                return self._channel_result("cea", issue_key)
            if issue_type in {"routinegarbagecollection", "garbagecollection", "missedgarbage"}:
                return self._resolve_local_authority("garbage_collection", answers)
            return self._clarify(
                issue_key,
                "What type of environmental problem is this?",
                "issue_type",
                [
                    "Industrial pollution",
                    "Hazardous waste",
                    "Noise pollution",
                    "Environmental damage",
                    "Routine garbage collection",
                ],
            )

        if issue_key == "immigration_issue":
            return self._channel_result("immigration", issue_key)

        if issue_key == "unknown_government_issue":
            return self._channel_result("gic", issue_key)

        # Final rule-based fallback.
        rule = self.rules[issue_key]
        target = rule.get("routes", {}).get("default")

        if target == "local_authority_from_geography":
            return self._resolve_local_authority(issue_key, answers)

        if target in self.channels:
            return self._channel_result(target, issue_key)

        return self._clarify(
            issue_key,
            "I need more information before I can safely route this problem.",
        )
