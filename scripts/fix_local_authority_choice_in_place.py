from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "services" / "complaint_router.py"
BACKUP = ROOT / "services" / "complaint_router.py.bak"

if not TARGET.exists():
    print("ERROR: Cannot find:", TARGET)
    sys.exit(1)

text = TARGET.read_text(encoding="utf-8")

if "local_authority_choice" in text:
    print("This router already contains the local-authority-choice fix.")
    print("File:", TARGET)
    sys.exit(0)

shutil.copy2(TARGET, BACKUP)

old1 = '''        local_authorities = ds_matches[0].get("local_authorities", [])

        if len(local_authorities) == 1:
'''

new1 = '''        local_authorities = ds_matches[0].get("local_authorities", [])

        # Accept an explicit council choice shown by HariMaga.
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
'''

old2 = '''        if len(local_authorities) > 1:
            return self._clarify(
                issue_key,
                "This DS area overlaps more than one local authority. Please provide the Grama Niladhari Division or a more specific local area.",
                "gnd_name",
                [la["name"] for la in local_authorities],
            )
'''

new2 = '''        if len(local_authorities) > 1:
            return self._clarify(
                issue_key,
                (
                    "This DS area overlaps more than one local authority. "
                    "Choose your local authority from the options below."
                ),
                "local_authority_choice",
                [la["name"] for la in local_authorities],
            )
'''

if old1 not in text:
    print("ERROR: Could not find the first expected code block.")
    print("No changes made. Backup is at:", BACKUP)
    sys.exit(2)

if old2 not in text:
    print("ERROR: Could not find the second expected code block.")
    print("No changes made. Backup is at:", BACKUP)
    sys.exit(3)

text = text.replace(old1, new1, 1)
text = text.replace(old2, new2, 1)

TARGET.write_text(text, encoding="utf-8")

print("FIX APPLIED")
print("Updated:", TARGET)
print("Backup :", BACKUP)
print(r"Now rerun: python -u scripts\demo_conversation_router.py")
