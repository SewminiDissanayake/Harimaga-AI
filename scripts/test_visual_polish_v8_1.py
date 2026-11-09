from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "webapp" / "frontend"

html = (FRONTEND / "index.html").read_text(encoding="utf-8")
css = (FRONTEND / "harimaga-ui-v8.css").read_text(encoding="utf-8")

assert "palette-card" not in html
assert "SRI LANKAN SIGNATURES" in html
assert "Sri Lanka Blue Magpie" in html
assert "Sri Lanka Junglefowl" in html
assert "Purple-faced Langur" in html
assert "Sri Lanka Hanging Parrot" in html

assert ".service-nav button:nth-of-type(1) .service-icon" in css
assert ".service-nav button:nth-of-type(9) .service-icon" in css
assert ".signature-card" in css

print("PASS: palette block replaced with Sri Lankan identity content")
print("PASS: sidebar service icons now use category-specific colours")
print("HARIMAGA VISUAL POLISH v8.1: PASSED")
