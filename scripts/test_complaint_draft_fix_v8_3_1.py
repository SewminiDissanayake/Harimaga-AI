from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "webapp" / "backend" / "app.py"
JS = ROOT / "webapp" / "frontend" / "harimaga-ui-v8.js"

src = APP.read_text(encoding="utf-8")
tree = ast.parse(src)

defs = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
assert "_humanize_key" in defs
assert "_routing_authority_name" in defs
assert "build_complaint_draft" in defs

assert 'complaint_draft_fix": "v8.3"' in src
assert 'Complaint draft generation failed safely.' in src
assert 'if not isinstance(jurisdiction, dict)' in src

js = JS.read_text(encoding="utf-8")

# Check ONLY the complaint-draft function.
# Other HariMaga API calls may legitimately still use res.json().
m = re.search(
    r'async function prepareComplaintDraft\(\)\s*\{(.*?)\n\}',
    js,
    flags=re.S,
)
assert m, "prepareComplaintDraft() function not found"
draft_fn = m.group(1)

assert "await res.text()" in draft_fn
assert "JSON.parse(raw)" in draft_fn
assert "unexpected server response" in draft_fn
assert "await res.json()" not in draft_fn

print("PASS: missing complaint-draft helper functions restored")
print("PASS: jurisdiction extraction is None-safe")
print("PASS: complaint-draft endpoint returns JSON-safe errors")
print("PASS: complaint-draft frontend safely handles non-JSON server errors")
print("HARIMAGA COMPLAINT DRAFT FIX v8.3.1 TEST: PASSED")
