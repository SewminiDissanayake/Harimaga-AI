from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "webapp" / "frontend"

html = (FRONTEND / "index.html").read_text(encoding="utf-8")
css = (FRONTEND / "harimaga-ui-v8.css").read_text(encoding="utf-8")

assert "SRI LANKAN SIGNATURES" not in html
assert "Sri Lanka Blue Magpie" not in html

for text in [
    "ජල සම්පත සුරකිමු.",
    "මාර්ග අනතුරු වළකමු.",
    "ළමා හා කාන්තා හිංසනයට එරෙහි වෙමු.",
    "ස්වාභාවික ආපදා සඳහා සූදානම් වෙමු.",
]:
    assert text in html

for asset in [
    "civic-water-v8-2.svg",
    "civic-road-v8-2.svg",
    "civic-safety-v8-2.svg",
    "civic-disaster-v8-2.svg",
]:
    assert (FRONTEND / "assets" / asset).exists()

assert ".civic-card" in css
assert ".civic-tile" in css

print("PASS: endemic/signature panel removed")
print("PASS: four HariMaga-related civic reminder illustrations added")
print("HARIMAGA CIVIC QUOTES v8.2: PASSED")
