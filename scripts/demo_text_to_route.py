from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.issue_classifier import HybridIssueClassifier
from services.complaint_router import ComplaintRouter

classifier = HybridIssueClassifier()
router = ComplaintRouter(ROOT)

problem = input("Describe your problem: ").strip()

classification = classifier.predict(problem)
print("\nDetected issue:", classification["label"])
print("Confidence:", round(classification["confidence"], 3))
print("Method:", classification["method"])

# At this stage we intentionally do not invent clarification answers.
result = router.route(classification["label"], {})
print("\nRouter result:")
print(result)
