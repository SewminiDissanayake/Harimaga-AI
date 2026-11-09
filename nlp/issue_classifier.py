import re
from pathlib import Path
import joblib


class HybridIssueClassifier:
    """
    HariMaga AI issue classifier (v2 model, v10 rules).

    Strategy:
    1. High-precision keyword/rule scoring.
    2. Character n-gram ML classifier for Sinhala, English and Singlish.
    3. Low-confidence ML predictions fall back to unknown_government_issue.
    """

    RULES = {
        "water_issue": [
            "water leak", "water supply", "water pipe", "wathura", "nwsdb",
            # v10: the bare "ජල" also matched inside "අපජලය" (wastewater)
            "ජල සැපයුම", "ජල නල", "ජල බිල", "ජල සම්පාදන", "වතුර", "නලයක්", "නලයෙන්"
        ],
        "electricity_issue": [
            "power cut", "power failure", "electricity", "current eka", "ceb", "leco",
            "voltage", "transformer", "විදුලි", "කරන්ට්", "වෝල්ටේජ්"
        ],
        "road_issue": [
            "pothole", "road damage", "road eka kadila", "loku walak",
            "walak thiyenawa", "rda road", "highway", "asphalt",
            "පාර කැඩිලා", "මාර්ගයේ", "වළක්", "තාර ගැලවිලා"
        ],
        "garbage_collection": [
            "garbage", "rubbish", "trash", "waste collection", "kunu",
            "garbage truck", "කුණු", "කසළ", "කුණු ලොරිය"
        ],
        "bus_complaint": [
            "bus", "conductor", "bus ticket", "bus fare", "bus route",
            "බස්", "කොන්දොස්තර", "ටිකට්"
        ],
        "consumer_complaint": [
            "refund", "warranty", "defective", "seller", "shop", "expired product",
            "වගකීම්", "මුදල් ආපසු", "භාණ්ඩ", "වෙළඳසැල"
        ],
        "environment_issue": [
            "pollution", "factory smoke", "chemical waste", "hazardous waste",
            "noise pollution", "industrial pollution", "දූෂණ", "රසායනික", "අපද්‍රව්‍ය", "අධික දුම"
        ],
        "immigration_issue": [
            "passport", "visa", "immigration", "පාස්පෝට්", "වීසා", "ආගමන"
        ],
        "unknown_government_issue": [
            "which government office", "where to complain", "correct authority",
            "government information", "kohetada kiyanna", "right authority",
            "කොහෙට කියන්න", "රාජ්‍ය ආයතනය", "නිවැරදි දෙපාර්තමේන්තුව"
        ],
    }

    # v10: a single keyword hit no longer overrides a confident ML prediction
    # of a different category (e.g. "rain ... wathura enawa" is a flood, not water supply).
    ML_OVERRIDES_SINGLE_KEYWORD_AT = 0.50

    def __init__(self, model_path=None, low_confidence_threshold=0.25):
        root = Path(__file__).resolve().parents[1]
        self.model_path = Path(model_path) if model_path else root / "models" / "issue_classifier.joblib"
        self.low_confidence_threshold = low_confidence_threshold
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}. Run scripts/train_issue_classifier.py first."
            )
        self.model = joblib.load(self.model_path)

    @staticmethod
    def _normalize(text):
        return re.sub(r"\s+", " ", str(text).strip().lower())

    @staticmethod
    def _phrase_in(phrase, text):
        """
        Fix v9: English/Singlish phrases must match whole words.
        Before, "bus" matched inside "business" and "abuse",
        and "visa" matched inside "advisable".
        Sinhala phrases keep substring matching because Sinhala words
        take suffixes (e.g. වතුර -> වතුරට) and regex \\b is unreliable there.
        """
        if phrase.isascii():
            return re.search(rf"\b{re.escape(phrase)}\b", text) is not None
        return phrase in text

    def _rule_scores(self, text):
        normalized = self._normalize(text)
        scores = {}
        for label, phrases in self.RULES.items():
            score = 0
            hits = []
            for phrase in phrases:
                if self._phrase_in(phrase, normalized):
                    score += 1
                    hits.append(phrase)
            if score:
                scores[label] = {"score": score, "hits": hits}
        return scores

    def predict(self, text):
        if not str(text).strip():
            return {
                "label": "unknown_government_issue",
                "confidence": 0.0,
                "method": "empty_input",
                "needs_clarification": True,
            }

        rule_scores = self._rule_scores(text)
        if rule_scores:
            ranked = sorted(
                rule_scores.items(),
                key=lambda item: item[1]["score"],
                reverse=True
            )
            top_label, top_info = ranked[0]
            second_score = ranked[1][1]["score"] if len(ranked) > 1 else 0

            # Strong rule: at least 2 hits, or one hit with no competing category.
            single_hit_overruled = False
            if top_info["score"] == 1 and second_score == 0:
                proba = self.model.predict_proba([text])[0]
                best = int(proba.argmax())
                single_hit_overruled = (
                    self.model.classes_[best] != top_label
                    and proba[best] >= self.ML_OVERRIDES_SINGLE_KEYWORD_AT
                )
            if not single_hit_overruled and (
                top_info["score"] >= 2 or (top_info["score"] == 1 and second_score == 0)
            ):
                return {
                    "label": top_label,
                    "confidence": min(0.99, 0.72 + 0.09 * top_info["score"]),
                    "method": "rule",
                    "rule_hits": top_info["hits"],
                    "needs_clarification": False,
                }

        probabilities = self.model.predict_proba([text])[0]
        classes = self.model.classes_
        best_idx = int(probabilities.argmax())
        label = str(classes[best_idx])
        confidence = float(probabilities[best_idx])

        if confidence < self.low_confidence_threshold:
            return {
                "label": "unknown_government_issue",
                "confidence": confidence,
                "method": "ml_low_confidence_fallback",
                "model_prediction": label,
                "needs_clarification": True,
            }

        return {
            "label": label,
            "confidence": confidence,
            "method": "ml",
            "needs_clarification": False,
        }
