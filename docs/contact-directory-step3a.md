# Yomu AI — Step 3A: Official Contact Directory Layer

This step builds a **verified directory-contact layer** for:

- Divisional Secretariats
- Municipal Councils
- Urban Councils
- Pradeshiya Sabhas

Source:
- Sri Lanka Right to Information (RTI) official Information Officer directory
- Sri Lanka RTI official Designated Officer directory

## Important design rule

RTI officer contacts are **official**, but they are not automatically the correct
channel for an ordinary complaint such as garbage collection, a broken road,
or a water leak.

Yomu therefore keeps three different concepts separate:

1. **Jurisdiction** — which authority/office is responsible?
2. **Official directory contact** — verified office/contact data.
3. **Complaint route** — the issue-specific hotline/portal/form/email that
   should actually be shown to the citizen.

This prevents Yomu from sending every local problem to an RTI officer.

## How to run

Copy this Step 3A content into the root of your current Yomu project so that
your existing geography files remain under:

`data/geography/`

Then:

```bat
pip install -r requirements.txt
python -u scripts\fetch_rti_contacts.py
```

Expected outputs:

- `data/contacts/divisional_secretariat_rti_contacts.json`
- `data/contacts/local_authority_rti_contacts.json`
- `data/meta/ds_contact_match_report.json`
- `data/meta/contact_harvest_report.json`

## Safe matching

If your existing DCS geography file is present at
`data/geography/ds_divisions.json`, the script attempts exact normalized
matching **within the same district**.

Names that do not match exactly are NOT auto-merged. They are placed in the
manual-review report with suggestions.

## Next step

Step 3B will build the **issue-specific complaint-channel layer**:
national hotlines, complaint portals, provider-specific channels, and
local-authority service routes.
