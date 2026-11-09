"""
evaluate_models.py
------------------
HariMaga AI evaluation. Produces reports/model_evaluation.md + figures.

Three experiments:

1. Cross-validation (repeated stratified 5-fold) of several ML models on the
   training set, to pick the best text representation and classifier.
2. Ablation on a held-out challenge set (data/eval/harimaga_challenge_v1.csv):
   how much does each layer of the system contribute?
     - ML model only
     - keyword rules + ML (v1 hybrid)
     - full system (high-precision safety/disaster/document rules + hybrid)
3. Learning curve: does more training data still help?

Run:
    python scripts/evaluate_models.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nlp.issue_classifier import HybridIssueClassifier  # noqa: E402
from nlp.robust_issue_classifier import RobustIssueClassifier  # noqa: E402

TRAIN = ROOT / "data" / "training" / "harimaga_issue_training_v1.csv"
CHALLENGE = ROOT / "data" / "eval" / "harimaga_challenge_v1.csv"      # dev set: used for error analysis
TEST = ROOT / "data" / "eval" / "harimaga_test_v2_sealed.csv"         # sealed test set: final numbers only
OUT = ROOT / "reports"
FIG = OUT / "figures"
SEED = 42

SHORT = {
    "road_issue": "road",
    "water_issue": "water",
    "electricity_issue": "power",
    "garbage_collection": "garbage",
    "bus_complaint": "bus",
    "consumer_complaint": "consumer",
    "environment_issue": "environ.",
    "immigration_issue": "immigr.",
    "lost_document": "lost doc",
    "women_child_safety": "safety",
    "disaster_alert": "disaster",
    "unknown_government_issue": "unknown",
}


# ---------------------------------------------------------------------------
# Models compared in experiment 1
# ---------------------------------------------------------------------------

def char_tfidf():
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)


def word_tfidf():
    return TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b")


def models():
    lr = dict(max_iter=3000, class_weight="balanced", random_state=SEED)
    return {
        "Majority-class baseline": Pipeline([("v", word_tfidf()), ("c", DummyClassifier(strategy="most_frequent"))]),
        "Word TF-IDF + LogReg": Pipeline([("v", word_tfidf()), ("c", LogisticRegression(**lr))]),
        "Char TF-IDF + LogReg (C=1, v1 setting)": Pipeline([("v", char_tfidf()), ("c", LogisticRegression(**lr))]),
        "Char TF-IDF + LogReg (C=30, deployed)": Pipeline([("v", char_tfidf()), ("c", LogisticRegression(**{**lr, "C": 30}))]),
        "Char TF-IDF + Linear SVM": Pipeline([("v", char_tfidf()), ("c", LinearSVC(class_weight="balanced", random_state=SEED))]),
        "Char TF-IDF + Complement NB": Pipeline([("v", char_tfidf()), ("c", ComplementNB())]),
        "Word+Char TF-IDF + LogReg": Pipeline([
            ("v", FeatureUnion([("w", word_tfidf()), ("ch", char_tfidf())])),
            ("c", LogisticRegression(**lr)),
        ]),
    }


# ---------------------------------------------------------------------------

TRAIN_V2 = ROOT / "data" / "training" / "harimaga_issue_training_v2_additions.csv"


def load():
    # Same data the deployed model is trained on (see scripts/train_issue_classifier.py)
    train = pd.read_csv(TRAIN, encoding="utf-8-sig")
    if TRAIN_V2.exists():
        train = pd.concat([train, pd.read_csv(TRAIN_V2, encoding="utf-8")], ignore_index=True)
    chal = pd.read_csv(CHALLENGE, encoding="utf-8")
    return train, chal


def exp1_cross_validation(train):
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    rows = []
    for name, model in models().items():
        s = cross_validate(model, train.text, train.label, cv=cv, scoring=["accuracy", "f1_macro"])
        rows.append({
            "model": name,
            "accuracy_mean": s["test_accuracy"].mean(),
            "accuracy_std": s["test_accuracy"].std(),
            "macro_f1_mean": s["test_f1_macro"].mean(),
            "macro_f1_std": s["test_f1_macro"].std(),
        })
    return pd.DataFrame(rows)


def exp1_generalisation(train, chal):
    """Train each ML model on ALL training data, test on the unseen challenge set.
    Only categories present in the training data are used here."""
    known = set(train.label)
    sub = chal[chal.label.isin(known)]
    rows = []
    for name, model in models().items():
        model.fit(train.text, train.label)
        pred = model.predict(sub.text)
        rows.append({
            "model": name,
            "challenge_accuracy": accuracy_score(sub.label, pred),
            "challenge_macro_f1": f1_score(sub.label, pred, average="macro", zero_division=0),
        })
    return pd.DataFrame(rows), len(sub)


def exp2_ablation(chal):
    hybrid = HybridIssueClassifier()
    full = RobustIssueClassifier()

    def ml_only(text):
        proba = hybrid.model.predict_proba([text])[0]
        i = int(proba.argmax())
        return hybrid.model.classes_[i] if proba[i] >= hybrid.low_confidence_threshold else "unknown_government_issue"

    systems = {
        "ML model only": ml_only,
        "Keyword rules + ML": lambda t: hybrid.predict(t)["label"],
        "Full HariMaga system": lambda t: full.predict(t)["label"],
    }
    labels = sorted(chal.label.unique())
    rows, preds = [], {}
    for name, fn in systems.items():
        pred = [fn(t) for t in chal.text]
        preds[name] = pred
        row = {
            "system": name,
            "accuracy": accuracy_score(chal.label, pred),
            "macro_f1": f1_score(chal.label, pred, labels=labels, average="macro", zero_division=0),
        }
        for lang in ["en", "si", "singlish", "ta"]:
            m = chal.language == lang
            row[f"acc_{lang}"] = accuracy_score(chal.label[m], np.array(pred)[m.values])
        # Safety recall: of real safety cases, how many were caught?
        _, rec, _, _ = precision_recall_fscore_support(
            chal.label, pred, labels=["women_child_safety"], zero_division=0
        )
        row["safety_recall"] = rec[0]
        rows.append(row)
    return pd.DataFrame(rows), preds, labels


def exp3_learning_curve(train):
    """Macro-F1 (5-fold CV) when using 20%..100% of the training data."""
    rng = np.random.default_rng(SEED)
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=SEED)
    sizes, scores = [], []
    for frac in [0.2, 0.4, 0.6, 0.8, 1.0]:
        # keep classes balanced when sub-sampling
        part = pd.concat(
            g.sample(frac=frac, random_state=int(rng.integers(1_000_000)))
            for _, g in train.groupby("label")
        )
        model = models()["Char TF-IDF + LogReg (C=30, deployed)"]
        s = cross_validate(model, part.text, part.label, cv=cv, scoring="f1_macro")
        sizes.append(len(part))
        scores.append((s["test_score"].mean(), s["test_score"].std()))
    return sizes, scores


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def fig_cv(cv_df):
    df = cv_df.sort_values("macro_f1_mean")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(df.model, df.macro_f1_mean, xerr=df.macro_f1_std, color="#11523F", ecolor="#5b6b64", capsize=3)
    ax.set_xlabel("Macro-F1 (repeated 5-fold CV, mean ± std)")
    ax.set_xlim(0, 1)
    ax.set_title("Model comparison on the training set")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "cv_model_comparison.png", dpi=160)
    plt.close(fig)


def fig_ablation(ab_df):
    cols = ["acc_en", "acc_si", "acc_singlish", "acc_ta"]
    names = ["English", "Sinhala", "Singlish", "Tamil"]
    x = np.arange(len(cols))
    w = 0.26
    colors = ["#9fb8ad", "#3f8f74", "#11523F"]
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, (_, row) in enumerate(ab_df.iterrows()):
        ax.bar(x + (i - 1) * w, [row[c] for c in cols], w, label=row.system, color=colors[i])
    ax.set_xticks(x, names)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Accuracy on challenge set")
    ax.set_title("Accuracy by language: what each layer adds")
    ax.legend(frameon=False, fontsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "ablation_by_language.png", dpi=160)
    plt.close(fig)


def fig_confusion(chal, pred, labels):
    cm = confusion_matrix(chal.label, pred, labels=labels)
    fig, ax = plt.subplots(figsize=(8, 7))
    ConfusionMatrixDisplay(cm, display_labels=[SHORT[l] for l in labels]).plot(
        ax=ax, cmap="Greens", colorbar=False, xticks_rotation=45
    )
    ax.set_title("Full HariMaga system: confusion matrix (challenge set)")
    fig.tight_layout()
    fig.savefig(FIG / "confusion_matrix_full_system.png", dpi=160)
    plt.close(fig)


def fig_learning_curve(sizes, scores):
    m = np.array([s[0] for s in scores])
    sd = np.array([s[1] for s in scores])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(sizes, m, marker="o", color="#11523F")
    ax.fill_between(sizes, m - sd, m + sd, color="#11523F", alpha=0.15)
    ax.set_xlabel("Training examples")
    ax.set_ylabel("Macro-F1 (5-fold CV)")
    ax.set_ylim(0, 1)
    ax.set_title("Learning curve: char TF-IDF + LogReg (C=30)")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "learning_curve.png", dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def pct(x):
    return f"{100 * x:.1f}%"


def write_report(train, chal, cv_df, gen_df, n_gen, ab_df, preds, labels, sizes, scores):
    full_pred = np.array(preds["Full HariMaga system"])
    errors = chal[full_pred != chal.label.values].assign(predicted=full_pred[full_pred != chal.label.values])

    p, r, f, s = precision_recall_fscore_support(chal.label, full_pred, labels=labels, zero_division=0)
    per_class = pd.DataFrame({"category": labels, "precision": p, "recall": r, "f1": f, "n": s})

    best = cv_df.sort_values("macro_f1_mean", ascending=False).iloc[0]
    lines = [
        "# HariMaga AI: Model Evaluation Report",
        "",
        "_Generated by `scripts/evaluate_models.py`. Re-run it after changing the data or models._",
        "",
        "## Data",
        "",
        f"- **Training set:** {len(train)} examples, {train.label.nunique()} categories "
        f"({', '.join(f'{k}: {v}' for k, v in train.language_hint.value_counts().items())}).",
        f"- **Challenge set:** {len(chal)} held-out examples, {chal.label.nunique()} categories × 10, "
        f"({', '.join(f'{k}: {v}' for k, v in chal.language.value_counts().items())}).",
        "  None of them is a near-duplicate of a training example (checked with a 0.8 similarity cut-off).",
        "- **Limitation:** both sets were written by the developers (the challenge set was drafted with an AI "
        "assistant), not collected from real users. The numbers below show how the system behaves on "
        "realistic phrasing, not how it performs in production. Replacing the challenge set with real, "
        "anonymised user queries is the most important next step.",
        "",
        "## 1. Model comparison (repeated stratified 5-fold cross-validation, 5×3 = 15 runs)",
        "",
        "| Model | Accuracy | Macro-F1 |",
        "|---|---|---|",
    ]
    for _, row in cv_df.sort_values("macro_f1_mean", ascending=False).iterrows():
        lines.append(f"| {row.model} | {pct(row.accuracy_mean)} ± {pct(row.accuracy_std)} | "
                     f"{row.macro_f1_mean:.3f} ± {row.macro_f1_std:.3f} |")
    lines += [
        "",
        f"Best in cross-validation: **{best.model}** (macro-F1 {best.macro_f1_mean:.3f}). "
        "The deployed model is **Char TF-IDF + LogReg (C=30)**: the difference to the best model is within one "
        "standard deviation, and HariMaga needs class *probabilities* (confidence threshold and safety bias), "
        "which a linear SVM does not provide.",
        "",
        "![CV comparison](figures/cv_model_comparison.png)",
        "",
        f"### Same models on unseen challenge sentences ({n_gen} examples)",
        "",
        "| Model | Accuracy | Macro-F1 |",
        "|---|---|---|",
    ]
    for _, row in gen_df.sort_values("challenge_macro_f1", ascending=False).iterrows():
        lines.append(f"| {row.model} | {pct(row.challenge_accuracy)} | {row.challenge_macro_f1:.3f} |")
    lines += [
        "",
        "The gap between cross-validation and challenge-set scores shows how much the models rely on "
        "phrasing that is similar to the training examples.",
        "",
        "## 2. Ablation: what each layer of the system contributes (challenge set, all 12 categories)",
        "",
        "| System | Accuracy | Macro-F1 | English | Sinhala | Singlish | Tamil | Safety recall |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, row in ab_df.iterrows():
        lines.append(
            f"| {row.system} | {pct(row.accuracy)} | {row.macro_f1:.3f} | {pct(row.acc_en)} | {pct(row.acc_si)} | "
            f"{pct(row.acc_singlish)} | {pct(row.acc_ta)} | {pct(row.safety_recall)} |"
        )
    lines += [
        "",
        "_Safety recall_ = share of real women/child-safety cases that the system routed to the safety flow. "
        "For this category a miss is far more costly than a false alarm.",
        "",
        "![Ablation by language](figures/ablation_by_language.png)",
        "",
        "### Full system: per-category results",
        "",
        "| Category | Precision | Recall | F1 |",
        "|---|---|---|---|",
    ]
    for _, row in per_class.iterrows():
        lines.append(f"| {row.category} | {row.precision:.2f} | {row.recall:.2f} | {row.f1:.2f} |")
    lines += [
        "",
        "![Confusion matrix](figures/confusion_matrix_full_system.png)",
        "",
        f"### Full system: all {len(errors)} errors",
        "",
        "| Text | Language | Expected | Predicted |",
        "|---|---|---|---|",
    ]
    for _, row in errors.iterrows():
        lines.append(f"| {row.text} | {row.language} | {row.label} | {row.predicted} |")
    lines += [
        "",
        "## 3. Learning curve",
        "",
        "| Training examples | Macro-F1 |",
        "|---|---|",
    ]
    for n, (m, sd) in zip(sizes, scores):
        lines.append(f"| {n} | {m:.3f} ± {sd:.3f} |")
    lines += [
        "",
        "![Learning curve](figures/learning_curve.png)",
        "",
        "If the curve is still rising at 100%, more training data is likely to help.",
        "",
    ]
    (OUT / "model_evaluation.md").write_text("\n".join(lines), encoding="utf-8")


def append_before_after(test_df, dev_df):
    """Compare with the archived v9.3 baseline (reports/baseline_v9_3)."""
    base_file = OUT / "baseline_v9_3" / "results_baseline_v9_3.json"
    if not base_file.exists():
        return
    base = json.loads(base_file.read_text(encoding="utf-8"))
    b_test = {r["system"]: r for r in base["ablation_test_v2"]}["Full HariMaga system"]
    b_dev = {r["system"]: r for r in base["ablation_dev_v1"]}["Full HariMaga system"]
    n_test = test_df.set_index("system").loc["Full HariMaga system"]
    n_dev = dev_df.set_index("system").loc["Full HariMaga system"]
    rows = [("Accuracy", "accuracy"), ("Macro-F1", "macro_f1"), ("English", "acc_en"), ("Sinhala", "acc_si"),
            ("Singlish", "acc_singlish"), ("Tamil", "acc_ta"), ("Safety recall", "safety_recall")]
    lines = [
        "",
        "## 4. Before vs after (full system)",
        "",
        "The **sealed test set** (`data/eval/harimaga_test_v2_sealed.csv`) was written and committed to git "
        "*before* any error analysis, and was only used to produce these final numbers. The dev set was used "
        "to find errors, so its \"after\" numbers are optimistic.",
        "",
        "| Metric | Dev v1: v9.3 | Dev v1: v10 | **Test v2: v9.3** | **Test v2: v10** |",
        "|---|---|---|---|---|",
    ]
    for name, key in rows:
        fmt = (lambda x: f"{x:.3f}") if key == "macro_f1" else pct
        lines.append(f"| {name} | {fmt(b_dev[key])} | {fmt(n_dev[key])} | {fmt(b_test[key])} | **{fmt(n_test[key])}** |")
    lines += [
        "",
        "### What changed in v10",
        "",
        "1. **Model regularisation:** C=1 → C=30. With C=1 the median top probability was 0.17, so the 0.30 "
        "confidence threshold sent 92% of ML predictions to \"unknown\" (CV macro-F1 0.215 with the threshold "
        "vs 0.811 without). Threshold lowered to 0.25. Both chosen by cross-validation on training data only.",
        "2. **Train on all data:** v1 kept 25% of rows out of the saved model.",
        "3. **Training data v2:** 115 AI-drafted examples (marked `origin` in the CSV) for the three categories "
        "the model had never seen (safety, disaster, lost documents), Tamil and English for every category, "
        "and contrast examples (e.g. \"threatening to cut trees\" = environment).",
        "4. **Safety bias:** if the ML probability of safety is ≥ 0.30 the request goes to the safety flow, "
        "because a missed safety case costs far more than a false alarm.",
        "5. **Rule fixes:** bare `ජල` no longer matches `අපජලය` (wastewater); one keyword can no longer "
        "overrule a confident (≥ 0.5) ML prediction; new safety, flood, landslide and lost-document "
        "patterns in English, Singlish, Sinhala and Tamil.",
        "",
        "### Honest limitations",
        "",
        "- All evaluation sentences were written by the developers / an AI assistant, who also wrote the rules. "
        "Even with a sealed test set this can flatter the results. **Real, anonymised user queries are needed "
        "for a trustworthy estimate** (the in-app 👍/👎 feedback shows which categories to collect first).",
        "- Tamil training and test sentences should be reviewed by a native speaker.",
        "- The safety bias produces some false alarms (e.g. Singlish sentences with \"nithara\"). "
        "This is a deliberate trade-off.",
        "",
    ]
    with open(OUT / "model_evaluation.md", "a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="", help="suffix for output files, e.g. _baseline_v9_3")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    train, chal = load()

    print("1/3 cross-validation…")
    cv_df = exp1_cross_validation(train)
    gen_df, n_gen = exp1_generalisation(train, chal)
    print("2/3 ablation…")
    ab_df, preds, labels = exp2_ablation(chal)
    print("3/3 learning curve…")
    sizes, scores = exp3_learning_curve(train)

    fig_cv(cv_df)
    fig_ablation(ab_df)
    fig_confusion(chal, preds["Full HariMaga system"], labels)
    fig_learning_curve(sizes, scores)
    write_report(train, chal, cv_df, gen_df, n_gen, ab_df, preds, labels, sizes, scores)

    # Sealed test set: same ablation, numbers only (no error listing, so it is not used for tuning)
    test = pd.read_csv(TEST, encoding="utf-8")
    test_df, _, _ = exp2_ablation(test)
    print("\nSEALED TEST SET v2:\n", test_df.round(3).to_string(index=False))
    append_before_after(test_df, ab_df)

    results = {
        "cross_validation": cv_df.to_dict("records"),
        "challenge_generalisation": gen_df.to_dict("records"),
        "ablation_dev_v1": ab_df.to_dict("records"),
        "ablation_test_v2": test_df.to_dict("records"),
        "learning_curve": [{"n": n, "macro_f1": m, "std": s} for n, (m, s) in zip(sizes, scores)],
    }
    (OUT / f"results{args.tag}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    pd.set_option("display.width", 160)
    print("\nCross-validation:\n", cv_df.round(3).to_string(index=False))
    print("\nChallenge set, ML models only:\n", gen_df.round(3).to_string(index=False))
    print("\nAblation:\n", ab_df.round(3).to_string(index=False))
    print("\nReport: reports/model_evaluation.md")


if __name__ == "__main__":
    main()
