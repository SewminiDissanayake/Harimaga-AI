
import json
from pathlib import Path

class LocalAuthorityContactService:
    def __init__(self, root=None):
        self.root=Path(root) if root else Path(__file__).resolve().parents[1]
        candidates=[
          self.root/"data"/"contacts"/"local_authority_official_directory_contacts_final.json",
          self.root/"data"/"contacts"/"local_authority_official_directory_contacts_v3.json"
        ]
        self.data_file=next((p for p in candidates if p.exists()),None)
        if self.data_file is None:
            raise FileNotFoundError("No local-authority contact file found.")
        with open(self.data_file,encoding="utf-8") as f: payload=json.load(f)
        self.records=payload.get("records",[])
        self.by_id={r.get("geography_id"):r for r in self.records if r.get("geography_id")}

    @staticmethod
    def _norm(v): return " ".join(str(v or "").strip().lower().split())

    @staticmethod
    def _unique(vals):
        out=[]; seen=set()
        for v in vals:
            v=str(v or "").strip()
            if v and v not in seen: seen.add(v); out.append(v)
        return out

    def find(self, local_authority):
        if not local_authority: return None
        gid=local_authority.get("id") or local_authority.get("geography_id")
        if gid and gid in self.by_id: return self._summarize(self.by_id[gid])
        name=self._norm(local_authority.get("name"))
        district=self._norm(local_authority.get("district"))
        la_type=self._norm(local_authority.get("type"))
        ms=[]
        for r in self.records:
            if self._norm(r.get("name"))!=name: continue
            if district and self._norm(r.get("district"))!=district: continue
            if la_type and self._norm(r.get("type"))!=la_type: continue
            ms.append(r)
        return self._summarize(ms[0]) if len(ms)==1 else None

    def _summarize(self,r):
        phones=[]; mobiles=[]; emails=[]; faxes=[]; addresses=[]; officers=[]
        for x in r.get("officer_records",[]):
            phones += x.get("telephone_01",[]) or []
            phones += x.get("telephone_02",[]) or []
            mobiles += x.get("mobile",[]) or []
            emails += x.get("email",[]) or []
            faxes += x.get("fax",[]) or []
            if x.get("address"): addresses.append(", ".join(x["address"]))
            o=x.get("officer") or {}
            if any(o.get(k) for k in ("title","name","designation")):
                officers.append({"title":o.get("title"),"name":o.get("name"),"designation":o.get("designation")})
        return {
          "status":"found","geography_id":r.get("geography_id"),"name":r.get("name"),
          "district":r.get("district"),"type":r.get("type"),
          "directory_contact_status":r.get("directory_contact_status"),
          "complaint_channel_status":r.get("complaint_channel_status"),
          "phones":self._unique(phones),"mobiles":self._unique(mobiles),
          "emails":self._unique(emails),"faxes":self._unique(faxes),
          "addresses":self._unique(addresses),"officers":officers,
          "source_url":r.get("source_url"),
          "notice":"Official council/RTI directory contact. Use as a fallback contact unless an issue-specific complaint channel has been separately verified."
        }
