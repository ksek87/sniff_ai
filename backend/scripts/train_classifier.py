"""
Offline training pipeline for ScentClassifier.

Run from the backend/ directory:
    python scripts/train_classifier.py

Labelling strategy (applied in order, first match wins):
  1. Concept tags  — Concepts column contains known family keywords
  2. Notes voting  — majority family across notes found in note_profiles.json

Outputs a classification report and confusion matrix, then writes the trained
model to services/nlp/scent_classifier.pkl alongside a SHA-256 sidecar.
Commit both files so Docker bakes the model in and production never retrains.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "../../data_collection/dataset.csv"
)
_PROFILES_PATH = os.path.join(
    os.path.dirname(__file__), "../data/note_profiles.json"
)
_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "../services/nlp/scent_classifier.pkl"
)
_HASH_PATH = _MODEL_PATH + ".sha256"

_CONCEPT_MAP: dict[str, str] = {
    "Floral": "Floral", "Rose": "Floral", "Jasmine": "Floral", "Lily": "Floral",
    "Oriental": "Oriental", "Amber": "Oriental", "Spicy": "Oriental", "Vanilla": "Oriental",
    "Woody": "Woody", "Cedar": "Woody", "Sandalwood": "Woody", "Oud": "Woody",
    "Fresh": "Fresh/Citrus", "Citrus": "Fresh/Citrus", "Green": "Fresh/Citrus",
    "Aromatic": "Fougère", "Fougère": "Fougère", "Herbal": "Fougère",
    "Chypre": "Chypre", "Mossy": "Earthy/Mossy", "Earthy": "Earthy/Mossy",
    "Gourmand": "Gourmand", "Sweet": "Gourmand", "Fruity": "Gourmand",
    "Aquatic": "Aquatic/Marine", "Marine": "Aquatic/Marine", "Ozonic": "Aquatic/Marine",
}


def _concepts_to_family(raw: str) -> str | None:
    try:
        concepts = ast.literal_eval(str(raw))
    except (ValueError, SyntaxError):
        return None
    for c in concepts:
        if c in _CONCEPT_MAP:
            return _CONCEPT_MAP[c]
    return None


def _build_note_lookup() -> dict[str, str]:
    """Lowercase + base-name (strip parenthetical variant) → family."""
    if not os.path.exists(_PROFILES_PATH):
        return {}
    with open(_PROFILES_PATH) as f:
        profiles = json.load(f)
    lookup: dict[str, str] = {}
    for note, data in profiles.items():
        fam = data.get("family", "unknown")
        if fam == "unknown":
            continue
        lookup[note.lower()] = fam
        base = note.split("(")[0].strip().lower()
        lookup.setdefault(base, fam)
    return lookup


def _notes_to_family(raw: str, lookup: dict[str, str]) -> str | None:
    try:
        notes = ast.literal_eval(str(raw))
    except (ValueError, SyntaxError):
        return None
    votes: dict[str, int] = {}
    for note in notes:
        fam = lookup.get(note.lower()) or lookup.get(note.split("(")[0].strip().lower())
        if fam:
            votes[fam] = votes.get(fam, 0) + 1
    if not votes:
        return None
    return max(votes, key=votes.get)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    print(f"Loading dataset: {_DATASET_PATH}")
    df = pd.read_csv(_DATASET_PATH)
    df = df.dropna(subset=["Description"])

    # ── Label: concept tags first, note voting as fallback ────────────────
    note_lookup = _build_note_lookup()
    df["family"] = df["Concepts"].apply(_concepts_to_family)
    df["source"] = "concept"

    needs_label = df["family"].isna()
    df.loc[needs_label, "family"] = df.loc[needs_label, "Notes"].apply(
        lambda raw: _notes_to_family(raw, note_lookup)
    )
    df.loc[needs_label & df["family"].notna(), "source"] = "notes"

    concept_n = (df["source"] == "concept").sum()
    note_n    = (df["source"] == "notes").sum()
    missing_n = df["family"].isna().sum()

    df = df.dropna(subset=["family"])
    X = df["Description"].astype(str).tolist()
    y = df["family"].tolist()
    # Concept-tag labels are cleaner; note-voted labels get half weight
    sample_weight = (df["source"] == "concept").map({True: 1.0, False: 0.5}).tolist()

    print(f"\nLabelling sources:")
    print(f"  Concept tags : {concept_n:,}")
    print(f"  Notes voting : {note_n:,}")
    print(f"  Unlabelled   : {missing_n:,}  (dropped)")
    print(f"  Total        : {len(y):,}")

    counts = pd.Series(y).value_counts()
    print(f"\nClass distribution:")
    print(counts.to_string())

    # ── Evaluate on concept-labelled rows only (clean ground truth) ──────
    concept_mask = np.array(df["source"].tolist()) == "concept"
    X_clean = [X[i] for i in np.where(concept_mask)[0]]
    y_clean = [y[i] for i in np.where(concept_mask)[0]]

    idx_clean = np.arange(len(X_clean))
    idx_train_c, idx_test_c = train_test_split(
        idx_clean, test_size=0.2, random_state=42, stratify=y_clean
    )
    X_train_c = [X_clean[i] for i in idx_train_c]
    y_train_c = [y_clean[i] for i in idx_train_c]
    X_test_c  = [X_clean[i] for i in idx_test_c]
    y_test_c  = [y_clean[i] for i in idx_test_c]

    tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=500, C=1.0, class_weight="balanced"),
        "LinearSVC":          CalibratedClassifierCV(LinearSVC(max_iter=2000, C=1.0, class_weight="balanced")),
        "RandomForest":       RandomForestClassifier(n_estimators=200, class_weight="balanced", n_jobs=-1, random_state=42),
    }

    print(f"\n── Model comparison — concept-labelled hold-out (n_test={len(X_test_c):,}) ──")
    print(f"{'Model':<22} {'Accuracy':>9} {'Macro-F1':>10}")
    print("-" * 44)

    best_name, best_f1, best_clf = "", 0.0, None
    for name, clf in candidates.items():
        pipe = Pipeline([("tfidf", tfidf), ("clf", clf)])
        pipe.fit(X_train_c, y_train_c)
        y_pred_c = pipe.predict(X_test_c)
        acc_c = np.mean(np.array(y_pred_c) == np.array(y_test_c))
        f1_c  = f1_score(y_test_c, y_pred_c, average="macro", zero_division=0)
        print(f"{name:<22} {acc_c:>9.3f} {f1_c:>10.3f}")
        if f1_c > best_f1:
            best_f1, best_name, best_clf = f1_c, name, clf

    print(f"\nBest: {best_name}  (macro-F1 {best_f1:.3f})")

    # Full report + confusion matrix for the winner
    best_pipe = Pipeline([("tfidf", tfidf), ("clf", best_clf)])
    best_pipe.fit(X_train_c, y_train_c)
    y_pred_best = best_pipe.predict(X_test_c)
    print(f"\n── {best_name} — full classification report ──────────────────────────")
    print(classification_report(y_test_c, y_pred_best, zero_division=0))

    labels = sorted(set(y_clean))
    cm = confusion_matrix(y_test_c, y_pred_best, labels=labels)
    print("── Confusion matrix (rows=true, cols=predicted) ─────────────────")
    col_w = max(len(l) for l in labels) + 2
    print("".ljust(col_w) + "".join(l.ljust(col_w) for l in labels))
    for label, row in zip(labels, cm):
        print(label.ljust(col_w) + "".join(str(v).ljust(col_w) for v in row))

    # ── Retrain winner on full dataset (concept + note-labelled) and save ──
    print(f"\nRetraining {best_name} on full dataset ({len(X):,} samples)…")
    full_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
        ("clf", best_clf),
    ])
    full_pipeline.fit(X, y, clf__sample_weight=sample_weight)

    os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
    with open(_MODEL_PATH, "wb") as f:
        pickle.dump(full_pipeline, f)

    digest = _sha256(_MODEL_PATH)
    with open(_HASH_PATH, "w") as f:
        f.write(digest)

    size_kb = os.path.getsize(_MODEL_PATH) / 1024
    print(f"\nSaved: {_MODEL_PATH}  ({size_kb:.0f} KB)")
    print(f"SHA-256: {digest}")
    print("\nCommit both scent_classifier.pkl and scent_classifier.pkl.sha256.")


if __name__ == "__main__":
    main()
