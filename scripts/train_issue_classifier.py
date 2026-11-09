"""
train_issue_classifier.py (v2)
------------------------------
Trains the HariMaga ML issue classifier.

Changes from v1 (see reports/model_evaluation.md for the evidence):
  - Uses the original dataset + v2 additions (safety, disaster, lost documents,
    Tamil and more English). Each row has an `origin` so it is clear what was
    written by the developer and what was AI-drafted.
  - C=30 instead of the default C=1. With C=1 the probabilities were so flat
    (median top probability 0.17) that the 0.30 confidence threshold sent
    92% of predictions to "unknown". Chosen by repeated 5-fold CV.
  - The final model is trained on ALL rows. v1 kept 25% aside for a single
    test split and never used it for training. Quality is now measured with
    cross-validation instead, which uses every row for both.

Run:
    python scripts/train_issue_classifier.py
"""
from pathlib import Path
import json

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA_V1 = ROOT / "data" / "training" / "harimaga_issue_training_v1.csv"
DATA_V2 = ROOT / "data" / "training" / "harimaga_issue_training_v2_additions.csv"
MODEL = ROOT / "models" / "issue_classifier.joblib"
REPORT = ROOT / "models" / "issue_classifier_metrics.json"

C = 30


def load_data():
    v1 = pd.read_csv(DATA_V1, encoding="utf-8-sig").assign(origin="developer_v1")
    v2 = pd.read_csv(DATA_V2, encoding="utf-8")
    return pd.concat([v1, v2], ignore_index=True)


def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, sublinear_tf=True)),
        ("clf", LogisticRegression(C=C, max_iter=5000, class_weight="balanced", random_state=42)),
    ])


def main():
    data = load_data()
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
    scores = cross_validate(build_pipeline(), data.text, data.label, cv=cv, scoring=["accuracy", "f1_macro"])

    model = build_pipeline().fit(data.text, data.label)
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL)

    metrics = {
        "model_version": 2,
        "sklearn_version": sklearn.__version__,
        "C": C,
        "rows": len(data),
        "rows_by_origin": data.origin.value_counts().to_dict(),
        "rows_by_label": data.label.value_counts().to_dict(),
        "cv": "repeated stratified 5-fold, 3 repeats",
        "cv_accuracy_mean": float(scores["test_accuracy"].mean()),
        "cv_accuracy_std": float(scores["test_accuracy"].std()),
        "cv_macro_f1_mean": float(scores["test_f1_macro"].mean()),
        "cv_macro_f1_std": float(scores["test_f1_macro"].std()),
        "note": "Developer-written and AI-drafted examples, not real user queries. "
                "See reports/model_evaluation.md for held-out results.",
    }
    REPORT.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print("HariMaga issue classifier v2 trained")
    print(f"  rows: {len(data)}  {metrics['rows_by_origin']}")
    print(f"  CV accuracy: {metrics['cv_accuracy_mean']:.3f} ± {metrics['cv_accuracy_std']:.3f}")
    print(f"  CV macro-F1: {metrics['cv_macro_f1_mean']:.3f} ± {metrics['cv_macro_f1_std']:.3f}")
    print(f"  saved: {MODEL.relative_to(ROOT)} (scikit-learn {sklearn.__version__})")


if __name__ == "__main__":
    main()
