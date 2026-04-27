from __future__ import annotations
import ast
import json
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../data/scent_classifier.pkl")
_DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "../../../data_collection/dataset.csv"
)

# Mapping from raw Concepts tags → canonical family
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
_DEFAULT_FAMILY = "Woody"
CANONICAL_FAMILIES = sorted(set(_CONCEPT_MAP.values()))


def _concepts_to_family(concepts_raw: str) -> str | None:
    try:
        concepts = ast.literal_eval(concepts_raw)
    except (ValueError, SyntaxError):
        return None
    for concept in concepts:
        if concept in _CONCEPT_MAP:
            return _CONCEPT_MAP[concept]
    return None


class ScentClassifier:
    def __init__(self):
        self._pipeline: Pipeline | None = None
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(_MODEL_PATH):
            with open(_MODEL_PATH, "rb") as f:
                self._pipeline = pickle.load(f)
            return
        self._train()

    def _train(self):
        if not os.path.exists(_DATASET_PATH):
            # No dataset available — classifier disabled, returns default
            return

        df = pd.read_csv(_DATASET_PATH)
        df["family"] = df["Concepts"].apply(_concepts_to_family)
        df = df.dropna(subset=["Description", "family"])

        X = df["Description"].astype(str).tolist()
        y = df["family"].tolist()

        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=500, C=1.0)),
        ])
        self._pipeline.fit(X, y)

        os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
        with open(_MODEL_PATH, "wb") as f:
            pickle.dump(self._pipeline, f)

    def predict(self, text: str) -> tuple[str, float]:
        if self._pipeline is None:
            return _DEFAULT_FAMILY, 0.0
        proba = self._pipeline.predict_proba([text])[0]
        idx = int(np.argmax(proba))
        family = self._pipeline.classes_[idx]
        return family, float(proba[idx])
