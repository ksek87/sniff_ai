"""
Unit tests for services/nlp/embedder.py — singleton pattern and encoding.
sentence_transformers is stubbed in sys.modules by conftest.py before any import.
"""
import numpy as np
import pytest


def test_embedder_singleton():
    """Two Embedder() calls return the same instance."""
    from services.nlp.embedder import Embedder
    e1 = Embedder()
    e2 = Embedder()
    assert e1 is e2


def test_encode_returns_list_of_floats():
    """encode() returns a plain Python list (JSON-serialisable)."""
    from services.nlp.embedder import Embedder
    result = Embedder().encode("autumn pine forest")
    assert isinstance(result, list)


def test_encode_length_matches_model_output():
    """encode() vector length matches the stub model's output (384 zeros)."""
    from services.nlp.embedder import Embedder
    result = Embedder().encode("test text")
    assert len(result) == 384


def test_encode_batch_returns_ndarray():
    """encode_batch() returns a numpy array (used by ingest_dataset.py)."""
    from services.nlp.embedder import Embedder
    result = Embedder().encode_batch(["rose", "oud", "cedar"])
    assert isinstance(result, np.ndarray)


def test_encode_called_with_normalize_embeddings():
    """encode() passes normalize_embeddings=True to the underlying model."""
    from services.nlp.embedder import Embedder
    e = Embedder()
    e._model.encode.reset_mock()
    e.encode("bergamot")
    e._model.encode.assert_called_once()
    _, kwargs = e._model.encode.call_args
    assert kwargs.get("normalize_embeddings") is True
