from pathlib import Path
import sys
import uuid
import time
import sqlite3
import re
import os

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "webapp" / "frontend"          # old HTML/CSS/JS UI
REACT_DIST = ROOT / "frontend" / "dist"           # new React UI after `npm run build`
sys.path.insert(0, str(ROOT))

from nlp.robust_issue_classifier import RobustIssueClassifier
from services.complaint_router import ComplaintRouter
from services.local_authority_contact_service import LocalAuthorityContactService
from services.local_authority_issue_channel_service import LocalAuthorityIssueChannelService
from services.provider_issue_channel_service import ProviderIssueChannelService
from services.bus_jurisdiction_service import BusJurisdictionService
from services.consumer_complaint_service import ConsumerComplaintService
from services.lost_document_service import LostDocumentService
from services.police_station_contact_service import PoliceStationContactService
from services.women_child_safety_service import WomenChildSafetyService
from services.disaster_alert_service import DisasterAlertService


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB per upload request
# v9: only allow the React dev server (and anything listed in
# HARIMAGA_CORS_ORIGINS, comma-separated) instead of every website.
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "HARIMAGA_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]
CORS(app, origins=CORS_ORIGINS)
DEBUG = os.environ.get("HARIMAGA_DEBUG") == "1"

# v9.3: when deployed behind a hosting proxy (Render, Railway...), trust its
# X-Forwarded-For header so rate limiting sees the real visitor IP.
if os.environ.get("HARIMAGA_BEHIND_PROXY") == "1":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# v9.3: rate limiting, so one person cannot flood the server or fill the disk.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour"],
    storage_uri=os.environ.get("HARIMAGA_LIMITER_STORAGE", "memory://"),
    enabled=os.environ.get("HARIMAGA_RATE_LIMIT", "1") != "0",
)

# Evidence storage v7:
# - no user account or identity profile
# - conversation text / routing answers are NOT persisted
# - only anonymous evidence metadata + the evidence file are stored
# - evidence automatically expires after 24 hours
# Can be moved with HARIMAGA_RUNTIME_DIR (tests use a temporary folder)
RUNTIME_DIR = Path(os.environ.get("HARIMAGA_RUNTIME_DIR", ROOT / "data" / "harimaga_runtime"))
EVIDENCE_DIR = RUNTIME_DIR / "evidence"
EVIDENCE_DB = RUNTIME_DIR / "evidence.sqlite3"
EVIDENCE_TTL_SECONDS = 24 * 60 * 60

RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

def _db():
    conn = sqlite3.connect(EVIDENCE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def _init_evidence_db():
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                uploaded_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                privacy_processed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_request ON evidence(request_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_expires ON evidence(expires_at)"
        )
        # v9.3: anonymous feedback. Only category, yes/no and the day.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_key TEXT NOT NULL,
                helpful INTEGER NOT NULL,
                day TEXT NOT NULL
            )
            """
        )

_init_evidence_db()
ALLOWED_EVIDENCE_EXTENSIONS = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".pdf"}
ALLOWED_EVIDENCE_MIMES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
    # Some Windows/browser combinations send a generic MIME for a valid
    # extension. We still validate the extension before allowing it.
    "application/octet-stream",
    "",
}

classifier = RobustIssueClassifier()

try:
    router = ComplaintRouter(ROOT)
except TypeError:
    router = ComplaintRouter()

local_authority_contacts = LocalAuthorityContactService(ROOT)
local_authority_issue_channels = LocalAuthorityIssueChannelService(ROOT)
provider_issue_channels = ProviderIssueChannelService(ROOT)
bus_jurisdiction = BusJurisdictionService(ROOT)
consumer_service = ConsumerComplaintService(ROOT)
lost_document_service = LostDocumentService(ROOT)
police_station_contacts = PoliceStationContactService(ROOT)
women_child_safety_service = WomenChildSafetyService(ROOT)
disaster_alert_service = DisasterAlertService(ROOT)

CORE_ROUTER_CATEGORIES = {
    "road_issue",
    "garbage_collection",
    "water_issue",
    "electricity_issue",
    "environment_issue",
    "immigration_issue",
    "unknown_government_issue",
}


# ---------------------------------------------------------------------
# v9.1: category hint from the UI
# ---------------------------------------------------------------------
VALID_CATEGORY_HINTS = CORE_ROUTER_CATEGORIES | {
    "bus_complaint",
    "consumer_complaint",
    "lost_document",
    "women_child_safety",
    "disaster_alert",
}


def classify_with_hint(text, hint=None):
    """
    Classify text, optionally helped by the category the user tapped.

    The user's choice is used when:
      - the classifier is unsure (unknown, or confidence below 0.50), or
      - the user chose Women & Child Safety (always err on the side of safety).
    Otherwise the classifier's confident answer is kept.
    """
    result = classifier.predict(text)
    hint = str(hint or "").strip()

    if hint not in VALID_CATEGORY_HINTS or hint == result.get("label"):
        return result

    unsure = (
        result.get("label") == "unknown_government_issue"
        or float(result.get("confidence", 0) or 0) < 0.50
    )

    if unsure or hint == "women_child_safety":
        return {
            "label": hint,
            "confidence": 0.90,
            "method": "user_selected_category",
            "classifier_suggestion": result.get("label"),
        }

    result = dict(result)
    result["user_selected_category"] = hint
    return result


def error(message, status=400, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    return jsonify(payload), status


def clarification(issue_key, field, question, options=None, **extra):
    payload = {
        "status": "needs_clarification",
        "issue_key": issue_key,
        "needed_field": field,
        "question": question,
        "options": options or [],
    }
    payload.update(extra)
    return payload


def value(answers, *keys):
    for key in keys:
        if key in answers:
            val = answers[key]
            if isinstance(val, str):
                val = val.strip()
            if val not in (None, ""):
                return val
    return None



def normalize_core_answers(answers):
    """
    Convert human-facing clarification labels into the canonical values
    expected by the existing ComplaintRouter.

    This fixes loops such as:
      "Local council road" -> router asks the same road question again.
    """
    normalized = dict(answers or {})

    # Road ownership / class
    if "road_type_or_class" in normalized:
        raw = str(normalized["road_type_or_class"] or "").strip().lower()

        if any(token in raw for token in (
            "national", "rda", "highway", "trunk"
        )):
            normalized["road_type_or_class"] = "national road"

        elif any(token in raw for token in (
            "local council",
            "local road",
            "local authority",
            "municipal",
            "urban council",
            "pradeshiya",
        )):
            normalized["road_type_or_class"] = "local road"

        elif raw in {
            "not sure", "unsure", "unknown", "don't know",
            "dont know", "dan ne", "danne na", "danne naha"
        }:
            normalized["road_type_or_class"] = "not sure"

    # Electricity provider
    if "electricity_provider" in normalized:
        raw = str(normalized["electricity_provider"] or "").strip().lower()

        if "leco" in raw:
            normalized["electricity_provider"] = "LECO"
        elif "ceb" in raw or "electricity board" in raw:
            normalized["electricity_provider"] = "CEB"

    # Water provider / scheme
    if "service_provider_or_scheme" in normalized:
        raw = str(normalized["service_provider_or_scheme"] or "").strip().lower()

        if (
            "nwsdb" in raw
            or "water board" in raw
            or "national water" in raw
        ):
            normalized["service_provider_or_scheme"] = "NWSDB"

    return normalized


def bool_answer(raw):
    if isinstance(raw, bool):
        return raw
    s = str(raw or "").strip().lower()
    if s in {"yes", "y", "ow", "1", "true"}:
        return True
    if s in {"no", "n", "naha", "na", "0", "false"}:
        return False
    return None


def options_to_json(options):
    result = []
    for item in options or []:
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            result.append({"value": item[0], "label": item[1]})
        else:
            result.append({"value": item, "label": str(item)})
    return result


def enrich_local_authority(issue_key, routing):
    authorities = []
    if routing.get("local_authority"):
        authorities = [routing["local_authority"]]
    elif routing.get("local_authorities"):
        authorities = routing["local_authorities"]

    enriched = []

    for la in authorities:
        row = {"authority": la}
        gid = la.get("id") or la.get("geography_id")

        if gid:
            verified = local_authority_issue_channels.find(gid, issue_key)
            if verified:
                row["verified_issue_channel"] = verified

        if "verified_issue_channel" not in row:
            fallback = local_authority_contacts.find(la)
            if fallback:
                row["directory_fallback"] = fallback
                row["directory_fallback_note"] = (
                    "Official directory fallback only; not automatically an "
                    "issue-specific complaint channel."
                )
        enriched.append(row)

    return enriched


def enrich_provider(issue_key, routing):
    candidates = [
        routing.get("authority_name"),
        routing.get("authority"),
        routing.get("provider"),
    ]
    for name in candidates:
        if isinstance(name, str) and name.strip():
            record = provider_issue_channels.find(name.strip(), issue_key)
            if record:
                return record
    return None


def route_core(issue_key, answers):
    normalized_answers = normalize_core_answers(answers)
    routing = router.route(issue_key, normalized_answers)

    if routing.get("status") != "routed":
        return routing

    result = dict(routing)
    routed_issue = result.get("issue_key") or issue_key

    local = enrich_local_authority(routed_issue, result)
    if local:
        result["verified_local_authority_routes"] = local

    provider = enrich_provider(routed_issue, result)
    if provider:
        result["verified_provider_route"] = provider

    return result


def route_bus(answers):
    issue_key = "bus_complaint"

    bus_type = value(answers, "bus_type", "operator_type")
    if not bus_type:
        return clarification(
            issue_key,
            "bus_type",
            "What type of bus was involved?",
            [
                {"value": "sltb", "label": "SLTB"},
                {"value": "private", "label": "Private bus"},
                {"value": "unknown", "label": "Not sure"},
            ],
        )

    bus_type_norm = str(bus_type).strip().lower()

    if bus_type_norm in {"sltb", "1"}:
        district = value(answers, "incident_district", "district")
        if not district:
            return clarification(
                issue_key,
                "incident_district",
                "In which district did the incident happen?",
            )
        resolved = bus_jurisdiction.resolve_sltb(district)

    elif bus_type_norm in {"private", "private bus", "2"}:
        origin = value(answers, "origin_district")
        if not origin:
            return clarification(
                issue_key,
                "origin_district",
                "Which district does this private bus route start from?",
            )

        destination = value(answers, "destination_district")
        if not destination:
            return clarification(
                issue_key,
                "destination_district",
                "Which district does this private bus route go to / end in?",
            )

        resolved = bus_jurisdiction.resolve_private(origin, destination)

    else:
        district = value(answers, "incident_district", "district")
        if not district:
            return clarification(
                issue_key,
                "incident_district",
                "In which district did the incident happen?",
            )
        resolved = bus_jurisdiction.resolve_unknown(district)

    if resolved.get("status") != "resolved":
        return resolved

    result = {
        "status": "routed",
        "issue_key": issue_key,
        "route_type": "bus_jurisdiction",
        "jurisdiction": resolved,
        "required_information": [
            "bus_number_or_registration",
            "route_number_or_route_name",
            "date_and_time",
            "exact_incident_location",
            "what_happened",
            "ticket_or_fare_details_if_relevant",
            "photo_or_video_if_available",
        ],
    }

    authority_name = resolved.get("authority_name")
    if authority_name:
        verified = provider_issue_channels.find(authority_name, issue_key)
        if verified:
            result["verified_authority_route"] = verified

    if (
        result.get("verified_authority_route", {}).get("verification_level")
        == "verified_authority_contact"
    ):
        ntc = provider_issue_channels.find("National Transport Commission", issue_key)
        if ntc:
            result["verified_ntc_fallback"] = ntc

    return result


def route_consumer(answers):
    issue_key = "consumer_complaint"

    subtype = value(answers, "consumer_subtype", "subtype")
    if not subtype:
        return clarification(
            issue_key,
            "consumer_subtype",
            "What best describes the consumer problem?",
            options_to_json(consumer_service.subtype_options()),
        )

    district = value(answers, "district", "business_district")
    if not district:
        return clarification(
            issue_key,
            "district",
            (
                "In which district is the business / seller / service provider "
                "located, or where did the transaction happen?"
            ),
        )

    return consumer_service.resolve(district, subtype)


def route_lost_document(answers):
    issue_key = "lost_document"

    document_type = value(answers, "document_type")
    if not document_type:
        return clarification(
            issue_key,
            "document_type",
            "Which government document was lost?",
            options_to_json(lost_document_service.document_options()),
        )

    resolved = lost_document_service.resolve(document_type)

    if resolved.get("status") != "resolved":
        return resolved

    if "police_station_query" not in answers:
        return clarification(
            issue_key,
            "police_station_query",
            (
                "Type the nearest town or police station name for an official "
                "station-contact lookup, or enter 'skip'."
            ),
            allow_skip=True,
            partial_result=resolved,
        )

    query = str(answers.get("police_station_query") or "").strip()

    result = dict(resolved)
    result["status"] = "routed"
    result["issue_key"] = issue_key
    result["route_type"] = "lost_document"

    if query and query.lower() not in {"skip", "none", "no"}:
        result["police_station_query"] = query
        result["police_station_matches"] = police_station_contacts.search(query)
    else:
        result["police_station_matches"] = []

    return result


def route_women_child_safety(answers):
    issue_key = "women_child_safety"

    subtype = value(answers, "safety_subtype", "subtype")
    if not subtype:
        return clarification(
            issue_key,
            "safety_subtype",
            "What best describes the women / child safety concern?",
            options_to_json(women_child_safety_service.subtype_options()),
        )

    if "immediate_danger" not in answers:
        return clarification(
            issue_key,
            "immediate_danger",
            "Is anyone in immediate danger right now?",
            [
                {"value": True, "label": "Yes"},
                {"value": False, "label": "No"},
            ],
        )

    danger = bool_answer(answers.get("immediate_danger"))
    if danger is None:
        return clarification(
            issue_key,
            "immediate_danger",
            "Please answer whether anyone is in immediate danger right now.",
            [
                {"value": True, "label": "Yes"},
                {"value": False, "label": "No"},
            ],
        )

    resolved = women_child_safety_service.resolve(subtype, danger)

    if resolved.get("status") == "resolved":
        resolved = dict(resolved)
        resolved["status"] = "routed"
        resolved["issue_key"] = issue_key
        resolved["route_type"] = "women_child_safety"

    return resolved


def route_disaster(classification, answers):
    issue_key = "disaster_alert"

    subtype = classification.get("disaster_subtype") or value(
        answers,
        "disaster_subtype",
        "subtype",
    )

    if not subtype:
        return clarification(
            issue_key,
            "disaster_subtype",
            "What type of disaster concern is this?",
            options_to_json(disaster_alert_service.alert_options()),
        )

    district = value(answers, "district")
    if not district:
        return clarification(
            issue_key,
            "district",
            "Which district are you asking about?",
        )

    resolved = disaster_alert_service.resolve(subtype, district)

    if resolved.get("status") == "resolved":
        resolved = dict(resolved)
        resolved["status"] = "routed"
        resolved["issue_key"] = issue_key
        resolved["route_type"] = "disaster_alert"

    return resolved


def dispatch_route(classification, answers):
    issue_key = classification.get("label", "unknown_government_issue")

    if issue_key == "bus_complaint":
        return route_bus(answers)
    if issue_key == "consumer_complaint":
        return route_consumer(answers)
    if issue_key == "lost_document":
        return route_lost_document(answers)
    if issue_key == "women_child_safety":
        return route_women_child_safety(answers)
    if issue_key == "disaster_alert":
        return route_disaster(classification, answers)
    if issue_key in CORE_ROUTER_CATEGORIES:
        return route_core(issue_key, answers)

    return {
        "status": "unsupported_category",
        "issue_key": issue_key,
        "message": "HariMaga has no safe routing flow for this category.",
    }



# ---------------------------------------------------------------------
# Evidence + complaint-draft helpers
# ---------------------------------------------------------------------

def _valid_request_id(value):
    value = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,96}", value):
        return None
    return value


def _purge_expired_evidence():
    now = int(time.time())

    with _db() as conn:
        rows = conn.execute(
            "SELECT id, stored_name FROM evidence WHERE expires_at <= ?",
            (now,),
        ).fetchall()

        for row in rows:
            path = EVIDENCE_DIR / row["stored_name"]

            try:
                path.unlink(missing_ok=True)
            except PermissionError:
                # Windows can temporarily keep a served image/PDF open.
                # Leave the row expired so the file is no longer accessible;
                # a later request will retry physical cleanup.
                continue

            conn.execute(
                "DELETE FROM evidence WHERE id = ?",
                (row["id"],),
            )


def _evidence_row(evidence_id, request_id=None):
    _purge_expired_evidence()

    now = int(time.time())

    with _db() as conn:
        if request_id:
            return conn.execute(
                """
                SELECT *
                FROM evidence
                WHERE id = ?
                  AND request_id = ?
                  AND expires_at > ?
                """,
                (evidence_id, request_id, now),
            ).fetchone()

        return conn.execute(
            """
            SELECT *
            FROM evidence
            WHERE id = ?
              AND expires_at > ?
            """,
            (evidence_id, now),
        ).fetchone()


def _generic_evidence_name(row):
    mime = row["mime_type"]
    if mime == "application/pdf":
        return "PDF evidence"
    return "Photo evidence"


def _safe_evidence_meta(evidence_id, request_id=None):
    row = _evidence_row(evidence_id, request_id)
    if not row:
        return None

    req = row["request_id"]

    return {
        "id": row["id"],
        "filename": _generic_evidence_name(row),
        "mime_type": row["mime_type"],
        "size_bytes": row["size_bytes"],
        "uploaded_at": row["uploaded_at"],
        "expires_at": row["expires_at"],
        "privacy_processed": bool(row["privacy_processed"]),
        "preview_url": f"/api/evidence/{row['id']}?request_id={req}",
    }


def _evidence_rows(evidence_ids, request_id=None):
    rows = []

    for evidence_id in evidence_ids or []:
        meta = _safe_evidence_meta(str(evidence_id), request_id)
        if meta:
            rows.append(meta)

    return rows


def _evidence_for_request(request_id):
    _purge_expired_evidence()

    with _db() as conn:
        rows = conn.execute(
            """
            SELECT id
            FROM evidence
            WHERE request_id = ?
              AND expires_at > ?
            ORDER BY uploaded_at ASC
            """,
            (request_id, int(time.time())),
        ).fetchall()

    return [
        _safe_evidence_meta(row["id"], request_id)
        for row in rows
        if row["id"]
    ]


def _humanize_key(value):
    """Turn internal keys such as road_issue into readable draft text."""
    text = str(value or "").strip().replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    if not text:
        return "government issue"

    acronyms = {
        "rda": "RDA",
        "ceb": "CEB",
        "leco": "LECO",
        "nwsdb": "NWSDB",
        "ntc": "NTC",
        "nic": "NIC",
    }

    words = []
    for word in text.split():
        lower = word.lower()
        words.append(acronyms.get(lower, word.capitalize()))

    return " ".join(words)


def _routing_authority_name(routing):
    """Safely extract a human-readable authority name from any HariMaga route."""
    routing = routing if isinstance(routing, dict) else {}

    technical = routing.get("technical_authority")
    if isinstance(technical, str) and technical.strip():
        return technical.strip()

    jurisdiction = routing.get("jurisdiction")
    if isinstance(jurisdiction, dict):
        name = jurisdiction.get("authority_name")
        if isinstance(name, str) and name.strip():
            return name.strip()

    document = routing.get("document")
    if isinstance(document, dict):
        authority = document.get("authority")
        if isinstance(authority, str) and authority.strip():
            return authority.strip()
        if isinstance(authority, dict):
            name = authority.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()

    authority = routing.get("authority")
    if isinstance(authority, str) and authority.strip():
        return authority.strip()
    if isinstance(authority, dict):
        name = authority.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()

    name = routing.get("authority_name")
    if isinstance(name, str) and name.strip():
        return name.strip()

    verified = routing.get("verified_authority_route")
    if isinstance(verified, dict):
        for key in ("authority_name", "name", "label"):
            value = verified.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    provider = routing.get("verified_provider_route")
    if isinstance(provider, dict):
        for key in ("authority_name", "name", "label"):
            value = provider.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def build_complaint_draft(original_text, classification, routing, answers, evidence_rows):
    issue_key = classification.get("label", "government_issue")
    authority = _routing_authority_name(routing)
    jurisdiction = routing.get("jurisdiction")
    if not isinstance(jurisdiction, dict):
        jurisdiction = {}

    district = (
        routing.get("district")
        or jurisdiction.get("incident_district")
        or jurisdiction.get("origin_district")
        or answers.get("district")
        or answers.get("incident_district")
        or ""
    )

    subject = f"Complaint / request regarding {_humanize_key(issue_key)}"

    lines = [
        subject,
        "",
    ]

    if authority:
        lines.append(f"To: {authority}")
    if district:
        lines.append(f"Area / District: {district}")

    lines.extend([
        "",
        "Dear Sir/Madam,",
        "",
        "I would like to report the following issue:",
        original_text.strip(),
        "",
    ])

    public_answer_items = []
    skip_fields = {
        "immediate_danger",
        "police_station_query",
    }
    for key, val in (answers or {}).items():
        if key in skip_fields or val in (None, "", [], {}):
            continue
        public_answer_items.append(f"- {_humanize_key(key)}: {val}")

    if public_answer_items:
        lines.append("Additional details:")
        lines.extend(public_answer_items)
        lines.append("")

    if evidence_rows:
        lines.append("Evidence prepared:")
        for row in evidence_rows:
            lines.append(f"- {row['filename']}")
        lines.append("")

    lines.extend([
        "Please review this matter and advise or take the appropriate action through the relevant official process.",
        "",
        "Thank you.",
    ])

    return {
        "subject": subject,
        "body": "\n".join(lines),
        "review_note": (
            "Review this draft before submitting. HariMaga prepares the text, "
            "but the citizen remains responsible for the final complaint."
        ),
    }

# ---------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------

def _no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.get("/")
def frontend_home():
    # v9.3: serve the new React UI when it has been built (npm run build),
    # otherwise fall back to the old HTML UI.
    if (REACT_DIST / "index.html").exists():
        return _no_cache(send_from_directory(REACT_DIST, "index.html", max_age=0))
    return _no_cache(send_from_directory(FRONTEND, "index.html", max_age=0))


@app.get("/classic")
def classic_home():
    """The old HTML/CSS/JS interface, kept for comparison."""
    return _no_cache(send_from_directory(FRONTEND, "index.html", max_age=0))


@app.get("/frontend/<path:filename>")
def frontend_asset(filename):
    return _no_cache(send_from_directory(FRONTEND, filename, max_age=0))


@app.get("/<path:filename>")
@limiter.exempt
def react_file(filename):
    """Files of the built React app (JS, CSS, fonts, images)."""
    if filename.startswith("api/") or not REACT_DIST.exists():
        return error("Page or API endpoint not found.", status=404)
    target = (REACT_DIST / filename).resolve()
    if REACT_DIST.resolve() not in target.parents or not target.is_file():
        return error("Page or API endpoint not found.", status=404)
    # Vite puts a content hash in asset names, so they can be cached for a year
    max_age = 31536000 if filename.startswith("assets/") else 3600
    return send_from_directory(REACT_DIST, filename, max_age=max_age)


# ---------------------------------------------------------------------
# API
# ---------------------------------------------------------------------

@app.get("/api/health")
@limiter.exempt
def health():
    return jsonify({
        "ok": True,
        "service": "HariMaga AI Backend",
        "status": "healthy",
        "classifier_loaded": True,
        "router_loaded": True,
        "specialized_services_loaded": True,
        "api_phase": 5,
        "frontend_loaded": FRONTEND.exists(),
        "evidence_upload_enabled": True,
        "complaint_draft_enabled": True,
        "core_answer_normalization_fix": True,
        "evidence_upload_fix": "v7",
        "evidence_storage": "anonymous_sqlite_ttl_24h",
        "conversation_persistence": False,
        "identity_profile_storage": False,
        "windows_evidence_delete_fix": "v7.2",
        "frontend_build": "clean-professional-v8",
        "complaint_draft_fix": "v8.3",
    })


@app.post("/api/classify")
@limiter.limit("60 per minute")
def classify():
    body = request.get_json(silent=True) or {}
    text = str(body.get("text", "")).strip()

    if not text:
        return error("Field 'text' is required.")

    return jsonify({
        "ok": True,
        "input": text,
        "classification": classifier.predict(text),
    })


@app.post("/api/route")
@limiter.limit("60 per minute")
def route():
    body = request.get_json(silent=True) or {}

    text = str(body.get("text", "")).strip()
    answers = body.get("answers") or {}

    if not text:
        return error("Field 'text' is required.")

    if not isinstance(answers, dict):
        return error("Field 'answers' must be a JSON object.")

    classification = classify_with_hint(text, body.get("category_hint"))
    routing = dispatch_route(classification, answers)

    # v9: if the user already answered this exact field but the router is
    # asking it again, the answer was not understood (e.g. typing "Kandy"
    # for "NWSDB or local scheme?"). Tell the frontend so it can explain.
    if (
        isinstance(routing, dict)
        and routing.get("status") == "needs_clarification"
        and routing.get("needed_field") in answers
    ):
        routing = dict(routing)
        routing["previous_answer_not_understood"] = True
        routing["hint"] = (
            "Sorry, I didn't understand that answer. "
            "Please choose one of the options below."
            if routing.get("options")
            else "Sorry, I didn't understand that answer. Please try again."
        )

    return jsonify({
        "ok": True,
        "input": text,
        "classification": classification,
        "answers": answers,
        "routing": routing,
    })



@app.post("/api/evidence")
@limiter.limit("30 per hour")
def upload_evidence():
    _purge_expired_evidence()

    file = request.files.get("file")
    request_id = _valid_request_id(request.form.get("request_id"))

    if not request_id:
        return error("A valid anonymous request_id is required.")

    if not file or not file.filename:
        return error("A file is required in multipart field 'file'.")

    original_name = secure_filename(file.filename)
    suffix = Path(original_name).suffix.lower()

    if suffix not in ALLOWED_EVIDENCE_EXTENSIONS:
        return error(
            "Unsupported evidence file type. Use JPG, JPEG, JFIF, PNG, WEBP, or PDF."
        )

    mime_type = (file.mimetype or "").lower()

    if mime_type not in ALLOWED_EVIDENCE_MIMES:
        return error(
            (
                "Unsupported evidence file format. Use JPG, JPEG, JFIF, PNG, "
                "WEBP, or PDF. HEIC/HEIF is not supported in this prototype yet."
            )
        )

    if suffix in {".jpg", ".jpeg", ".jfif"}:
        mime_type = "image/jpeg"
    elif suffix == ".png":
        mime_type = "image/png"
    elif suffix == ".webp":
        mime_type = "image/webp"
    elif suffix == ".pdf":
        mime_type = "application/pdf"

    evidence_id = uuid.uuid4().hex
    stored_name = f"{evidence_id}{suffix}"
    stored_path = EVIDENCE_DIR / stored_name

    file.save(stored_path)
    size_bytes = stored_path.stat().st_size

    if size_bytes > 10 * 1024 * 1024:
        stored_path.unlink(missing_ok=True)
        return error("Evidence file is larger than 10 MB.")

    privacy_processed = str(
        request.form.get("privacy_processed", "")
    ).strip().lower() in {"1", "true", "yes"}

    uploaded_at = int(time.time())
    expires_at = uploaded_at + EVIDENCE_TTL_SECONDS

    with _db() as conn:
        conn.execute(
            """
            INSERT INTO evidence (
                id,
                request_id,
                stored_name,
                mime_type,
                size_bytes,
                uploaded_at,
                expires_at,
                privacy_processed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                request_id,
                stored_name,
                mime_type,
                size_bytes,
                uploaded_at,
                expires_at,
                int(privacy_processed),
            ),
        )

    return jsonify({
        "ok": True,
        "evidence": _safe_evidence_meta(evidence_id, request_id),
        "storage": "anonymous_sqlite_ttl_24h",
        "privacy": {
            "identity_profile_saved": False,
            "conversation_saved": False,
            "original_filename_saved": False,
            "auto_delete_hours": 24,
        },
        "note": (
            "Evidence is attached to this anonymous HariMaga request and is "
            "scheduled for automatic deletion after 24 hours."
        ),
    })


@app.get("/api/evidence/request/<request_id>")
def list_request_evidence(request_id):
    request_id = _valid_request_id(request_id)

    if not request_id:
        return error("Invalid request_id.")

    return jsonify({
        "ok": True,
        "evidence": _evidence_for_request(request_id),
        "auto_delete_hours": 24,
    })


@app.get("/api/evidence/<evidence_id>")
def view_evidence(evidence_id):
    request_id = _valid_request_id(request.args.get("request_id"))

    if not request_id:
        return error("A valid request_id is required.", status=403)

    row = _evidence_row(evidence_id, request_id)

    if not row:
        return error("Evidence file not found.", status=404)

    path = EVIDENCE_DIR / row["stored_name"]

    if not path.exists():
        with _db() as conn:
            conn.execute(
                "DELETE FROM evidence WHERE id = ? AND request_id = ?",
                (evidence_id, request_id),
            )
        return error("Evidence file is no longer available.", status=404)

    return send_file(
        path,
        mimetype=row["mime_type"],
        as_attachment=False,
        download_name=_generic_evidence_name(row),
        max_age=0,
    )


@app.delete("/api/evidence/<evidence_id>")
def delete_evidence(evidence_id):
    body = request.get_json(silent=True) or {}
    request_id = _valid_request_id(
        body.get("request_id") or request.args.get("request_id")
    )

    if not request_id:
        return error("A valid request_id is required.", status=403)

    row = _evidence_row(evidence_id, request_id)

    if not row:
        return jsonify({"ok": True, "deleted": False})

    path = EVIDENCE_DIR / row["stored_name"]

    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        # Mark it expired immediately. It disappears from the user's request
        # now, and physical cleanup is retried automatically once Windows
        # releases the file handle.
        with _db() as conn:
            conn.execute(
                """
                UPDATE evidence
                SET expires_at = ?
                WHERE id = ? AND request_id = ?
                """,
                (int(time.time()), evidence_id, request_id),
            )

        return jsonify({
            "ok": True,
            "deleted": False,
            "delete_pending": True,
            "evidence_id": evidence_id,
            "note": (
                "Windows still has the preview file open. HariMaga has "
                "expired it immediately and will retry physical deletion "
                "automatically."
            ),
        })

    with _db() as conn:
        conn.execute(
            "DELETE FROM evidence WHERE id = ? AND request_id = ?",
            (evidence_id, request_id),
        )

    return jsonify({
        "ok": True,
        "deleted": True,
        "delete_pending": False,
        "evidence_id": evidence_id,
    })


@app.post("/api/complaint-draft")
@limiter.limit("20 per minute")
def complaint_draft():
    body = request.get_json(silent=True) or {}

    text = str(body.get("text", "")).strip()
    answers = body.get("answers") or {}
    evidence_ids = body.get("evidence_ids") or []
    request_id = _valid_request_id(body.get("request_id"))

    if not text:
        return error("Field 'text' is required.")

    if not isinstance(answers, dict):
        return error("Field 'answers' must be a JSON object.")

    if not isinstance(evidence_ids, list):
        return error("Field 'evidence_ids' must be a JSON array.")

    if evidence_ids and not request_id:
        return error("A valid request_id is required when evidence is attached.")

    classification = classify_with_hint(text, body.get("category_hint"))
    routing = dispatch_route(classification, answers)

    if routing.get("status") not in {"routed", "resolved"}:
        return error(
            "Complete the HariMaga routing questions before preparing a complaint draft.",
            status=409,
            routing=routing,
        )

    rows = _evidence_rows(evidence_ids, request_id)

    try:
        draft = build_complaint_draft(
            text,
            classification,
            routing,
            answers,
            rows,
        )
    except Exception as exc:
        app.logger.exception("Complaint draft generation failed")
        return error("Complaint draft generation failed safely.", status=500)

    return jsonify({
        "ok": True,
        "classification": classification,
        "routing_status": routing.get("status"),
        "evidence": rows,
        "draft": draft,
    })



@app.post("/api/feedback")
@limiter.limit("30 per hour")
def feedback():
    """v9.3: anonymous 'was this helpful?' answer."""
    body = request.get_json(silent=True) or {}
    issue_key = str(body.get("issue_key", "")).strip()
    helpful = body.get("helpful")

    if issue_key not in VALID_CATEGORY_HINTS or not isinstance(helpful, bool):
        return error("Send issue_key (a HariMaga category) and helpful (true/false).")

    with _db() as conn:
        conn.execute(
            "INSERT INTO feedback (issue_key, helpful, day) VALUES (?, ?, ?)",
            (issue_key, int(helpful), time.strftime("%Y-%m-%d", time.gmtime())),
        )
    return jsonify({"ok": True})


@app.get("/api/feedback/summary")
def feedback_summary():
    """Counts per category, e.g. to find where the classifier struggles."""
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT issue_key,
                   SUM(helpful) AS helpful,
                   COUNT(*) - SUM(helpful) AS not_helpful
            FROM feedback
            GROUP BY issue_key
            ORDER BY issue_key
            """
        ).fetchall()
    return jsonify({"ok": True, "categories": [dict(r) for r in rows]})


@app.errorhandler(429)
def too_many_requests(_):
    return error("Too many requests. Please wait a minute and try again.", status=429)


@app.errorhandler(404)
def not_found(_):
    return error("Page or API endpoint not found.", status=404)


@app.errorhandler(500)
def server_error(exc):
    # v9: details go to the server log only, never to the browser.
    app.logger.exception("Internal server error: %s", exc)
    return error("Internal server error.", status=500)


if __name__ == "__main__":
    print("=" * 72)
    print("HariMaga AI backend v9")
    print("API:            http://127.0.0.1:5000/api/health")
    print("Old HTML UI:    http://127.0.0.1:5000")
    print("New React UI:   run 'npm run dev' in /frontend, then open http://localhost:5173")
    print("Debug mode:     " + ("ON" if DEBUG else "OFF (set HARIMAGA_DEBUG=1 to enable)"))
    print("=" * 72)

    app.run(host="127.0.0.1", port=5000, debug=DEBUG)
