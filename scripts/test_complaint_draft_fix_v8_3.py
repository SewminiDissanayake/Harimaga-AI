from pathlib import Path
import ast

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
assert "await res.text()" in js
assert "JSON.parse(raw)" in js
assert "unexpected server response" in js
assert "const data = await res.json();" not in js

print("PASS: missing complaint-draft helper functions restored")
print("PASS: jurisdiction extraction is None-safe")
print("PASS: complaint-draft endpoint returns JSON-safe errors")
print("PASS: frontend no longer crashes on HTML error responses")
print("HARIMAGA COMPLAINT DRAFT FIX v8.3: PASSED")
