"""
conftest.py — session-level stubs and shared fixtures.

sentence_transformers is stubbed in sys.modules at the very top so the
Embedder singleton never tries to download or load model weights.

The `from app import app` call is inside the client fixture (not at module
level) because app.py pulls in Flask and several service modules. Unit tests
that don't use the client fixture shouldn't pay that import cost or fail due
to missing production dependencies (Flask, chromadb, etc.).
"""
import sys

import numpy as np
from unittest.mock import MagicMock

# ── Stub sentence_transformers before any app code can import it ──────────
_st_model = MagicMock()
_st_model.encode.return_value = np.zeros(384, dtype=np.float32)
_st_module = MagicMock()
_st_module.SentenceTransformer.return_value = _st_model
sys.modules.setdefault("sentence_transformers", _st_module)
# ─────────────────────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch


MOCK_COMPOSITION = {
    "name": "Autumn Pine Accord",
    "scent_family": "Woody",
    "top_notes": [
        {"note": "Petitgrain", "percentage": 15},
        {"note": "Bergamot", "percentage": 10},
    ],
    "middle_notes": [
        {"note": "Pine Needle", "percentage": 30},
        {"note": "Clary Sage", "percentage": 15},
    ],
    "base_notes": [
        {"note": "Cedarwood", "percentage": 20},
        {"note": "Vetiver", "percentage": 10},
    ],
    "poetic_description": "An autumn walk through a pine forest after rain.",
    "similar_fragrances": [
        {"brand": "Test Brand", "name": "Forest Walk", "similarity_score": 0.88}
    ],
    "confidence_score": 0.92,
}


@pytest.fixture()
def client():
    """
    Flask test client with every external dependency mocked:
    - Claude API (anthropic)          – no outbound calls
    - ChromaDB (_get_collection)      – returns deterministic fixture data
    - NLP model loaders               – no filesystem / download
    - Feedback store (save/metrics)   – in-memory, no SQLite writes
    Rate limiting is disabled so tests don't interfere with each other.
    """
    with (
        patch("services.nlp.note_extractor.NoteExtractor._load_notes"),
        patch("services.nlp.note_extractor.NoteExtractor._build_ruler"),
        patch("services.nlp.scent_classifier.ScentClassifier._load_or_train"),
        patch("services.agents._client.anthropic"),
        patch("services.tools.search_tool._get_collection") as mock_coll,
        patch("services.generate_fragrance.orchestrator.run") as mock_orch,
        patch("services.generate_fragrance.composer.run") as mock_comp,
        patch("services.feedback.save_feedback"),
        patch("services.feedback.get_metrics") as mock_metrics,
        patch("services.shares.save_share", return_value="a" * 32),
        patch("services.shares.get_share") as mock_get_share,
    ):
        mock_coll.return_value.count.return_value = 100
        mock_coll.return_value.query.return_value = {
            "metadatas": [[
                {
                    "brand": "TestBrand", "name": "TestFrag",
                    "description": "a test fragrance", "notes_list": "[]",
                    "concepts_list": "[]",
                }
            ]],
            "distances": [[0.15]],
        }
        mock_orch.return_value = {
            "reference_fragrances": [],
            "recommended_notes": {},
            "reasoning": "test",
        }
        mock_comp.return_value = MOCK_COMPOSITION
        mock_get_share.return_value = {
            "input_description": "autumn forest after rain",
            "composition": MOCK_COMPOSITION,
        }
        mock_metrics.return_value = {
            "total_feedback": 5,
            "average_rating": 4.2,
            "rating_distribution": {"1": 0, "2": 0, "3": 1, "4": 2, "5": 2},
        }

        # Reset NLP singletons so each fixture gets a fresh lazy instance
        # created while the patches on _load_notes / _load_or_train are active.
        import services.nlp as _nlp
        _nlp._note_extractor = None
        _nlp._classifier = None

        from app import app as flask_app
        from limiter import limiter as _limiter

        flask_app.config["TESTING"] = True
        _limiter.enabled = False
        with flask_app.test_client() as c:
            yield c
        _limiter.enabled = True
