# HariMaga: Data Collection Plan

The learning curve in `reports/model_evaluation.md` is still rising at ~330
examples, and every evaluation sentence so far was written by the developers or
an AI assistant. Real user language is the biggest missing piece.

## Goal

| | Now | Target |
|---|---|---|
| Training examples | ~330 (216 developer + ~115 AI-drafted) | 1,200+ (100 per category) |
| Real user examples | 0 | at least 50% of the training set |
| Sealed test set | 60 AI-drafted | 300 real, anonymised, never used for training |
| Tamil | ~2 per category, AI-drafted | 25+ per category, written or checked by native speakers |

## Where the data comes from

1. **Friends, family, classmates (fastest).** A short Google Form: "Describe a
   problem you had with a road, water, electricity, bus, shop… in your own
   words, the way you would type it on your phone." No names, no phone
   numbers. Ask for Sinhala, Singlish, Tamil and English separately.
2. **In-app feedback.** The 👍/👎 counts (`/api/feedback/summary`) show which
   categories fail most. Collect more examples for those first.
3. **Opt-in example sharing (future).** A clearly worded checkbox: "Share this
   sentence (without any personal details) to help improve HariMaga."
   Off by default. Never store sentences from the safety category.

## Rules for every example

- Remove names, phone numbers, NIC numbers, addresses and vehicle numbers.
- Label with one of the 12 category keys; when unsure, two people label it
  and disagreements are discussed.
- Record `language_hint` (si / ta / en / singlish / mixed) and `origin`
  (developer / ai_drafted / user_form / user_optin).
- Check for near-duplicates against the test set before adding to training
  (see the `difflib` check in the git history of `data/eval`).
- Freeze a new sealed test set **before** looking at any model errors on it.

## After collecting

```bash
python scripts/train_issue_classifier.py
python scripts/evaluate_models.py
python scripts/evaluate_transformer.py      # optional, on a computer with ~3 GB free
pytest
```
