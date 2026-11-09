
import json
from pathlib import Path
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT/"data"/"geography"/"local_authorities.json"
MANUAL = ROOT/"data"/"meta"/"local_authority_manual_review_v3.json"
V3 = ROOT/"data"/"contacts"/"local_authority_official_directory_contacts_v3.json"
RES = ROOT/"data"/"meta"/"local_authority_manual_review_resolutions_v1.json"
FINAL_CONTACTS = ROOT/"data"/"contacts"/"local_authority_official_directory_contacts_final.json"
FINAL_REPORT = ROOT/"data"/"meta"/"local_authority_contact_resolution_final.json"

def load(p):
    with open(p,encoding="utf-8") as f: return json.load(f)

def norm(v): return " ".join(str(v or "").strip().lower().split())

def matches(rule,row):
    m=rule["match"]
    if "area_name" in m:
        w=m["area_name"]
        if w is None:
            if row.get("area_name") is not None: return False
        elif norm(row.get("area_name"))!=norm(w): return False
    if "district" in m and norm(row.get("district"))!=norm(m["district"]): return False
    if "la_type" in m and norm(row.get("la_type"))!=norm(m["la_type"]): return False
    if "email_contains" in m and m["email_contains"].lower() not in " ".join(row.get("email") or []).lower(): return False
    return True

def fp(row):
    def vals(k): return tuple(sorted(str(x).strip() for x in (row.get(k) or []) if str(x).strip()))
    return (tuple(row.get("address") or []),vals("telephone_01"),vals("telephone_02"),vals("fax"),vals("mobile"),vals("email"))

def main():
    geo=load(GEO)["records"]
    manual=load(MANUAL)["records"]
    v3=load(V3)
    rules=load(RES)["rules"]

    geo_by_id={g["id"]:g for g in geo}
    final=deepcopy(v3.get("records",[]))
    by_id={r["geography_id"]:r for r in final}

    audit=[]; unresolved=[]; added=0; dup=0; newly=set()

    for idx,row in enumerate(manual,1):
        rs=[r for r in rules if matches(r,row)]
        if len(rs)!=1:
            unresolved.append({"record":idx,"area_name":row.get("area_name"),"district":row.get("district"),"matching_rules":len(rs)})
            continue
        rule=rs[0]; tid=rule["target_geography_id"]; g=geo_by_id.get(tid)
        if not g: raise RuntimeError(f"Missing geography target: {tid}")

        rec=by_id.get(tid)
        if rec is None:
            rec={
              "geography_id":tid,"name":g["name"],"district":g["district"],"type":g["type"],
              "directory_contact_status":"official_rti_directory_manual_resolution",
              "complaint_channel_status":"not_yet_issue_specific",
              "source_url":row.get("source_url"),"officer_records":[]
            }
            final.append(rec); by_id[tid]=rec; newly.add(tid)

        existing={fp(x) for x in rec.get("officer_records",[])}
        if fp(row) in existing:
            action="duplicate_contact_skipped"; dup+=1
        else:
            rec.setdefault("officer_records",[]).append({
              "officer":row.get("officer"),
              "address":row.get("address",[]),
              "telephone_01":row.get("telephone_01",[]),
              "telephone_02":row.get("telephone_02",[]),
              "fax":row.get("fax",[]),
              "mobile":row.get("mobile",[]),
              "email":row.get("email",[]),
              "source_type":row.get("source_type"),
              "contact_purpose":row.get("contact_purpose"),
              "source_original_area_name":row.get("area_name"),
              "source_original_district":row.get("district"),
              "source_original_la_type":row.get("la_type"),
              "manual_resolution":rule["decision"],
              "manual_resolution_rule":rule["key"]
            })
            action="contact_added"; added+=1

        audit.append({
          "record":idx,"source_area_name":row.get("area_name"),"source_district":row.get("district"),
          "target_geography_id":tid,"target_name":g["name"],"target_district":g["district"],
          "target_type":g["type"],"decision":rule["decision"],"action":action
        })

    geo_ids=set(geo_by_id)
    covered={r["geography_id"] for r in final}
    missing=sorted(geo_ids-covered)

    FINAL_CONTACTS.parent.mkdir(parents=True,exist_ok=True)
    with open(FINAL_CONTACTS,"w",encoding="utf-8") as f:
        json.dump({
          "dataset":"HariMaga official local-authority directory contacts - final reviewed layer",
          "warning":"Official directory fallback contacts; not automatically issue-specific complaint channels.",
          "records":final
        },f,ensure_ascii=False,indent=2)

    report={
      "status":"completed",
      "manual_records_reviewed":len(manual),
      "manual_records_resolved":len(audit),
      "manual_records_unresolved":len(unresolved),
      "contact_rows_added":added,
      "duplicate_contact_rows_skipped":dup,
      "new_unique_local_authorities_covered":len(newly),
      "final_unique_local_authorities_with_directory_contact":len(covered),
      "unique_geography_ids_total":len(geo_ids),
      "unique_geography_ids_without_directory_contact":len(missing),
      "audit":audit,"unresolved":unresolved,
      "geography_ids_without_directory_contact":missing
    }
    with open(FINAL_REPORT,"w",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2)

    print("HariMaga Local Authority Manual Review - FINAL")
    print("Manual records reviewed                 :",len(manual))
    print("Manual records resolved                 :",len(audit))
    print("Manual records unresolved               :",len(unresolved))
    print("Contact rows added                      :",added)
    print("Duplicate contact rows skipped          :",dup)
    print("New unique LAs covered                  :",len(newly))
    print("Final unique LAs with directory contact :",len(covered))
    print("Unique geography IDs total              :",len(geo_ids))
    print("Unique geography IDs without contact    :",len(missing))
    if unresolved:
        print("WARNING: unresolved records remain.")
    else:
        print("MANUAL REVIEW RESOLUTION: PASSED (0 unresolved)")

if __name__=="__main__":
    main()
