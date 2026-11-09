from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "webapp" / "frontend"

html = (FRONTEND / "index.html").read_text(encoding="utf-8")
css = (FRONTEND / "style.css").read_text(encoding="utf-8")
js = (FRONTEND / "app.js").read_text(encoding="utf-8")

for marker in [
    'id="conversation"',
    'id="composer"',
    'id="evidenceInput"',
    'id="sendEvidenceBtn"',
    'id="pendingEvidenceTray"',
    'id="draftModal"',
]:
    assert marker in html, marker

assert "HariMaga Deep Island UI v7" in css
assert "request_id" in js
assert "Attach selected evidence" in html
assert "No account. No identity profile." in html

print("HARIMAGA DEEP ISLAND FRONTEND v7: PASSED")
