import json
from pathlib import Path


class LostDocumentService:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        path = self.root / "data" / "routing" / "lost_document_routes.json"
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def document_options(self):
        return [
            (key, value["label"])
            for key, value in self.data["document_types"].items()
        ]

    def resolve(self, document_key):
        doc = self.data["document_types"].get(document_key)
        if not doc:
            return {"status": "invalid_document_type"}

        return {
            "status": "resolved",
            "document_key": document_key,
            "document": doc,
            "police": self.data["police"],
        }
