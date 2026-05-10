from __future__ import annotations
import ast
import hashlib
import logging
import os
import pickle

import numpy as np
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

# Committed alongside this module; baked into Docker at build time.
# Retrain with: python backend/scripts/train_classifier.py, then commit the pkl.
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "scent_classifier.pkl")
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
_DEFAULT_FAMILY = "Woody"


def _concepts_to_family(concepts_raw: str) -> str | None:
    try:
        concepts = ast.literal_eval(concepts_raw)
    except (ValueError, SyntaxError):
        return None
    for concept in concepts:
        if concept in _CONCEPT_MAP:
            return _CONCEPT_MAP[concept]
    return None


def _file_sha256(path: str) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


class ScentClassifier:
    def __init__(self):
        self._pipeline: Pipeline | None = None
        self._load_or_train()

    def _load_or_train(self):
        if not os.path.exists(_MODEL_PATH):
            logger.warning(
                "scent_classifier.pkl not found at %s — using default family. "
                "Run backend/scripts/train_classifier.py and commit the pkl.",
                _MODEL_PATH,
            )
            return

        if os.path.exists(_HASH_PATH):
            with open(_HASH_PATH) as f:
                expected = f.read().strip()
            actual = _file_sha256(_MODEL_PATH)
            if actual != expected:
                logger.error(
                    "scent_classifier.pkl SHA-256 mismatch (expected %s…, got %s…) "
                    "— refusing to load. Retrain and commit a fresh pkl.",
                    expected[:16], actual[:16],
                )
                return

        with open(_MODEL_PATH, "rb") as f:
            self._pipeline = pickle.load(f)
        logger.info("Loaded scent_classifier.pkl from %s", _MODEL_PATH)

    def predict(self, text: str) -> tuple[str, float]:
        if self._pipeline is None:
            return _DEFAULT_FAMILY, 0.0
        proba = self._pipeline.predict_proba([text])[0]
        idx = int(np.argmax(proba))
        family = self._pipeline.classes_[idx]
        return family, float(proba[idx])
