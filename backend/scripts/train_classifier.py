"""
Offline training pipeline for ScentClassifier.

Run from the backend/ directory:
    python scripts/train_classifier.py

Outputs a classification report and confusion matrix, then writes the trained
model to services/nlp/scent_classifier.pkl alongside a SHA-256 sidecar.
Commit both files so Docker bakes the model in and production never retrains.
"""
from __future__ import annotations
import ast
import hashlib
import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "../../data_collection/dataset.csv"
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
        concepts = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return None
    for c in concepts:
        if c in _CONCEPT_MAP:
            return _CONCEPT_MAP[c]
    return None


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    print(f"Loading dataset: {_DATASET_PATH}")
    df = pd.read_csv(_DATASET_PATH)
    df["family"] = df["Concepts"].apply(_concepts_to_family)
    df = df.dropna(subset=["Description", "family"])

    X = df["Description"].astype(str).tolist()
    y = df["family"].tolist()

    counts = pd.Series(y).value_counts()
    print(f"\nLabelled samples: {len(y):,}")
    print(counts.to_string())

    # ── Hold-out evaluation ────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=500, C=1.0, class_weight="balanced")),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print("\n── Hold-out classification report (20 % test split) ──────────────")
    print(classification_report(y_test, y_pred, zero_division=0))

    # ── Stratified 5-fold cross-validation ────────────────────────────────
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    # Refit on full data for CV to get stable estimates
    full_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=500, C=1.0, class_weight="balanced")),
    ])
    scores = cross_val_score(full_pipeline, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    macro_scores = cross_val_score(full_pipeline, X, y, cv=cv, scoring="f1_macro", n_jobs=-1)
    print(f"── 5-fold CV accuracy: {scores.mean():.3f} ± {scores.std():.3f}  |  macro-F1: {macro_scores.mean():.3f} ± {macro_scores.std():.3f} ──")

    # ── Confusion matrix (text) ────────────────────────────────────────────
    labels = sorted(set(y))
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    print("\n── Confusion matrix (rows=true, cols=predicted) ─────────────────")
    col_w = max(len(l) for l in labels) + 2
    header = "".ljust(col_w) + "".join(l.ljust(col_w) for l in labels)
    print(header)
    for label, row in zip(labels, cm):
        print(label.ljust(col_w) + "".join(str(v).ljust(col_w) for v in row))

    # ── Retrain on full dataset and save ──────────────────────────────────
    print("\nRetraining on full dataset…")
    full_pipeline.fit(X, y)

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
