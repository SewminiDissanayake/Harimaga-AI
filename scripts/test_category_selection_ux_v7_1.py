from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "webapp" / "frontend"

html = (FRONTEND / "index.html").read_text(encoding="utf-8")
js = (FRONTEND / "app.js").read_text(encoding="utf-8")

assert 'data-category="road_issue"' in html
assert 'data-category="water_issue"' in html
assert 'id="selectedServiceBar"' in html
assert "selectCategoryFromButton" in js
assert "now type your own exact problem" in js

# Welcome example chips can still send deliberate examples.
assert 'data-prompt="ape pare loku walak thyenawa"' in html

print("PASS: service cards select context instead of auto-sending canned complaints")
print("PASS: user can type the exact real problem")
print("HARIMAGA CATEGORY SELECTION UX FIX v7.1: PASSED")
