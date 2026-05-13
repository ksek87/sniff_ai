from __future__ import annotations
import ast
import hashlib
import logging
import os
import pickle

import numpy as np

logger = logging.getLogger(__name__)

# SetFit model directory takes priority; falls back to legacy pkl.
# Set SCENT_CLASSIFIER_MODEL env-var to a HF Hub repo ID or local path
# to override the default location.
_SETFIT_DIR = os.getenv(
    "SCENT_CLASSIFIER_MODEL",
    os.path.join(os.path.dirname(__file__), "scent_classifier_model"),
)
_PKL_PATH  = os.path.join(os.path.dirname(__file__), "scent_classifier.pkl")
_HASH_PATH = _PKL_PATH + ".sha256"

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
        self._setfit = None   # SetFitModel, if available
        self._clf    = None   # sklearn classifier (legacy pkl fallback)
        self._load()

    def _load(self):
        # ── Prefer SetFit model ───────────────────────────────────────────
        setfit_config = os.path.join(_SETFIT_DIR, "config_setfit.json")
        if os.path.isfile(setfit_config) or (
            not os.path.isabs(_SETFIT_DIR) is False
            and not _SETFIT_DIR.startswith("/")
        ):
            try:
                from setfit import SetFitModel
                self._setfit = SetFitModel.from_pretrained(_SETFIT_DIR)
                logger.info("Loaded SetFit classifier from %s", _SETFIT_DIR)
                return
            except Exception as e:
                logger.warning("SetFit load failed (%s) — falling back to pkl", e)

        # ── Legacy pkl fallback ───────────────────────────────────────────
        if not os.path.exists(_PKL_PATH):
            logger.warning(
                "No classifier found (checked %s and %s). "
                "Run backend/scripts/train_classifier.py.",
                _SETFIT_DIR, _PKL_PATH,
            )
            return

        if os.path.exists(_HASH_PATH):
            with open(_HASH_PATH) as f:
                expected = f.read().strip()
            actual = _file_sha256(_PKL_PATH)
            if actual != expected:
                logger.error(
                    "scent_classifier.pkl SHA-256 mismatch — refusing to load."
                )
                return

        with open(_PKL_PATH, "rb") as f:
            payload = pickle.load(f)

        if isinstance(payload, dict):
            self._clf = payload["clf"]
            logger.info("Loaded embedding-based classifier (%s) from pkl", payload.get("clf_name"))
        else:
            self._clf = payload
            logger.info("Loaded TF-IDF pipeline classifier from pkl")

    def predict(self, text: str) -> tuple[str, float]:
        # ── SetFit path ───────────────────────────────────────────────────
        if self._setfit is not None:
            proba = self._setfit.predict_proba([text])[0]
            idx = int(np.argmax(proba))
            labels = self._setfit.labels
            return labels[idx], float(proba[idx])

        # ── Legacy pkl path ───────────────────────────────────────────────
        if self._clf is not None:
            from .embedder import Embedder
            vec = np.array(Embedder().encode(text)).reshape(1, -1)
            proba = self._clf.predict_proba(vec)[0]
            idx = int(np.argmax(proba))
            return self._clf.classes_[idx], float(proba[idx])

        return _DEFAULT_FAMILY, 0.0
