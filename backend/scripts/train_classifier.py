"""
Offline training pipeline for ScentClassifier — SetFit edition.

Requires: pip install setfit
Run from the backend/ directory on a machine with a GPU:
    python scripts/train_classifier.py

Labelling strategy (applied in order, first match wins):
  1. Concept tags  — Concepts column contains known family keywords
  2. Notes voting  — majority family across notes found in note_profiles.json

The fine-tuned SetFit model is saved to services/nlp/scent_classifier_model/.
Push it to HF Hub and set SCENT_CLASSIFIER_MODEL env-var in the Docker image,
or commit the directory directly if storage is acceptable.
"""
from __future__ import annotations
import ast
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "../../data_collection/dataset.csv"
)
_PROFILES_PATH = os.path.join(
    os.path.dirname(__file__), "../data/note_profiles.json"
)
_MODEL_OUT = os.path.join(
    os.path.dirname(__file__), "../services/nlp/scent_classifier_model"
)

# Base model — paraphrase-mpnet-base-v2 (768-dim) gives better semantic
# understanding than all-MiniLM-L6-v2 (384-dim) for classification tasks.
# Swap for a larger model (e.g. all-mpnet-base-v2) if GPU memory allows.
_BASE_MODEL = "sentence-transformers/paraphrase-mpnet-base-v2"

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
        lookup.setdefault(note.split("(")[0].strip().lower(), fam)
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
    return max(votes, key=votes.get) if votes else None


def main() -> None:
    # ── Load and label dataset ────────────────────────────────────────────
    print(f"Loading dataset: {_DATASET_PATH}")
    df = pd.read_csv(_DATASET_PATH).dropna(subset=["Description"])

    note_lookup = _build_note_lookup()
    df["family"] = df["Concepts"].apply(_concepts_to_family)
    df["source"] = "concept"

    needs_label = df["family"].isna()
    df.loc[needs_label, "family"] = df.loc[needs_label, "Notes"].apply(
        lambda r: _notes_to_family(r, note_lookup)
    )
    df.loc[needs_label & df["family"].notna(), "source"] = "notes"

    concept_n = (df["source"] == "concept").sum()
    note_n    = (df["source"] == "notes").sum()
    missing_n = df["family"].isna().sum()
    df = df.dropna(subset=["family"])

    print(f"\nLabelling sources:")
    print(f"  Concept tags : {concept_n:,}")
    print(f"  Notes voting : {note_n:,}")
    print(f"  Unlabelled   : {missing_n:,}  (dropped)")
    print(f"  Total        : {len(df):,}")
    print(f"\nClass distribution:")
    print(df["family"].value_counts().to_string())

    # ── Train/test split on concept-labelled rows (clean ground truth) ───
    concept_df = df[df["source"] == "concept"].reset_index(drop=True)
    train_c, test_c = train_test_split(
        concept_df, test_size=0.2, random_state=42, stratify=concept_df["family"]
    )

    # All labelled rows for training; concept rows get higher weight
    train_all = df.copy()
    sample_weights = np.where(train_all["source"] == "concept", 1.0, 0.5)

    print(f"\nTrain (all sources): {len(train_all):,}  |  Test (concept only): {len(test_c):,}")

    # ── SetFit training ───────────────────────────────────────────────────
    try:
        from setfit import SetFitModel, Trainer, TrainingArguments
        from datasets import Dataset
    except ImportError:
        print("\nERROR: setfit not installed. Run: pip install setfit datasets")
        sys.exit(1)

    print(f"\nLoading base model: {_BASE_MODEL}")
    model = SetFitModel.from_pretrained(
        _BASE_MODEL,
        labels=sorted(df["family"].unique().tolist()),
    )

    train_dataset = Dataset.from_dict({
        "text":  train_all["Description"].astype(str).tolist(),
        "label": train_all["family"].tolist(),
    })
    test_dataset = Dataset.from_dict({
        "text":  test_c["Description"].astype(str).tolist(),
        "label": test_c["family"].tolist(),
    })

    args = TrainingArguments(
        output_dir="setfit_output",
        num_epochs=3,              # contrastive fine-tuning epochs
        batch_size=32,
        num_iterations=20,         # pairs per class per epoch
        evaluation_strategy="epoch",
        save_strategy="no",
        load_best_model_at_end=False,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        metric="f1",
        metric_kwargs={"average": "macro"},
    )

    print("\nFine-tuning…")
    trainer.train()

    # ── Evaluate ──────────────────────────────────────────────────────────
    y_pred = model.predict(test_c["Description"].astype(str).tolist())
    y_true = test_c["family"].tolist()

    print(f"\n── SetFit ({_BASE_MODEL}) — concept-labelled hold-out ──────────────")
    print(classification_report(y_true, y_pred, zero_division=0))

    labels = sorted(set(y_true))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print("── Confusion matrix (rows=true, cols=predicted) ─────────────────")
    col_w = max(len(l) for l in labels) + 2
    print("".ljust(col_w) + "".join(l.ljust(col_w) for l in labels))
    for label, row in zip(labels, cm):
        print(label.ljust(col_w) + "".join(str(v).ljust(col_w) for v in row))

    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    print(f"\nMacro-F1: {macro_f1:.3f}")

    # ── Save ──────────────────────────────────────────────────────────────
    os.makedirs(_MODEL_OUT, exist_ok=True)
    model.save_pretrained(_MODEL_OUT)
    print(f"\nSaved model to: {_MODEL_OUT}")
    print("Push to HF Hub with: model.push_to_hub('ksek87/sniff-ai-scent-classifier')")
    print("Then set SCENT_CLASSIFIER_MODEL=ksek87/sniff-ai-scent-classifier in Docker.")


if __name__ == "__main__":
    main()
