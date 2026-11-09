import json
from pathlib import Path


class LocalAuthorityIssueChannelService:
    """
    Exact lookup for authority + issue-specific/public complaint routes.

    Priority order:
      1. verified_issue_specific_channel
      2. verified_general_complaint_channel
      3. caller may fall back to LocalAuthorityContactService
    """

    RANK = {
        "verified_issue_specific_channel": 1,
        "verified_general_complaint_channel": 2,
    }

    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.data_file = (
            self.root / "data" / "routing" / "local_authority_issue_channels.json"
        )

        if not self.data_file.exists():
            raise FileNotFoundError(self.data_file)

        with open(self.data_file, encoding="utf-8") as f:
            payload = json.load(f)

        self.records = payload.get("records", [])
        self.index = {}

        for record in self.records:
            key = (record.get("geography_id"), record.get("issue_key"))
            self.index.setdefault(key, []).append(record)

    def find(self, geography_id, issue_key):
        rows = self.index.get((geography_id, issue_key), [])

        if not rows:
            return None

        rows = sorted(
            rows,
            key=lambda r: self.RANK.get(r.get("verification_level"), 99)
        )

        return rows[0]
