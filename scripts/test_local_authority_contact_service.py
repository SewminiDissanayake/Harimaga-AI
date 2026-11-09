from pathlib import Path
import json
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.local_authority_contact_service import LocalAuthorityContactService

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    p = root / "data" / "contacts"
    p.mkdir(parents=True)

    sample = {
        "records": [
            {
                "geography_id": "central__kandy__35__kundasale_ps",
                "name": "Kundasale PS",
                "district": "Kandy",
                "type": "pradeshiya_sabha",
                "directory_contact_status": "official_rti_directory",
                "complaint_channel_status": "not_yet_issue_specific",
                "source_url": "https://rti.gov.lk/do-list/",
                "officer_records": [
                    {
                        "officer": {"name": "Example Officer", "designation": "Secretary"},
                        "address": ["Kundasale"],
                        "telephone_01": ["081 000 0000"],
                        "telephone_02": [],
                        "mobile": [],
                        "fax": [],
                        "email": ["example@gov.lk"],
                    }
                ],
            }
        ]
    }

    with open(p / "local_authority_official_directory_contacts_v3.json", "w", encoding="utf-8") as f:
        json.dump(sample, f)

    service = LocalAuthorityContactService(root)
    result = service.find({
        "id": "central__kandy__35__kundasale_ps",
        "name": "Kundasale PS",
        "type": "pradeshiya_sabha",
    })

    assert result is not None
    assert result["phones"] == ["081 000 0000"]
    assert result["emails"] == ["example@gov.lk"]

print("LOCAL AUTHORITY CONTACT SERVICE: PASSED")
