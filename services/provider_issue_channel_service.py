import json
from pathlib import Path


class ProviderIssueChannelService:
    """Exact/alias lookup for verified provider-specific issue channels."""

    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.data_file = self.root / "data" / "routing" / "provider_issue_channels.json"

        if not self.data_file.exists():
            raise FileNotFoundError(self.data_file)

        with open(self.data_file, encoding="utf-8") as f:
            payload = json.load(f)

        self.records = payload.get("records", [])

    @staticmethod
    def _norm(value):
        return " ".join(str(value or "").strip().lower().replace("&", "and").split())

    def find(self, authority_name, issue_key):
        wanted = self._norm(authority_name)

        matches = []
        for record in self.records:
            if record.get("issue_key") != issue_key:
                continue

            names = [record.get("authority_name")] + list(record.get("aliases") or [])
            normalized = {self._norm(x) for x in names if x}

            if wanted in normalized:
                matches.append(record)

        return matches[0] if len(matches) == 1 else None
