from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "webapp" / "frontend"

html = (FRONTEND / "index.html").read_text(encoding="utf-8")
css = (FRONTEND / "style.css").read_text(encoding="utf-8")
js = (FRONTEND / "app.js").read_text(encoding="utf-8")

required_ids = [
    'id="conversation"',
    'id="choiceArea"',
    'id="composer"',
    'id="input"',
    'id="sendBtn"',
    'id="newBtn"',
    'id="evidenceToolbarBtn"',
    'id="evidenceInput"',
    'id="draftModal"',
]

for marker in required_ids:
    assert marker in html, marker

assert "HariMaga Sri Lanka Identity UI v6.0" in css
assert "sri-lanka-landscape.svg" in html
assert "sri-lanka-navigator.svg" in html
assert "ප්‍රශ්නය කියන්න." in html
assert "යන මග අපි පෙන්වන්නම්." in html
assert "/api/evidence" in js
assert "/api/complaint-draft" in js

for asset in [
    FRONTEND / "assets" / "harimaga-logo.svg",
    FRONTEND / "assets" / "sri-lanka-landscape.svg",
    FRONTEND / "assets" / "sri-lanka-navigator.svg",
]:
    assert asset.exists() and asset.stat().st_size > 500, asset

print("PASS: all working UI IDs preserved")
print("PASS: evidence + complaint-draft JS preserved")
print("PASS: Sri Lanka landscape, navigator and logo assets present")
print("PASS: 'ප්‍රශ්නය කියන්න. යන මග අපි පෙන්වන්නම්.' identity applied")
print("HARIMAGA SRI LANKA IDENTITY UI v6.0: PASSED")
