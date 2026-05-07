"""
Unit tests for services/tools/search_tool.py.
ChromaDB is fully mocked — no filesystem access.
"""
from unittest.mock import MagicMock, patch

import pytest


def _make_collection(count: int, metadatas=None, distances=None):
    coll = MagicMock()
    coll.count.return_value = count
    if count > 0:
        coll.query.return_value = {
            "metadatas": [metadatas or []],
            "distances": [distances or []],
        }
    return coll


# ── Empty collection ────────────────────────────────────────────────────────

def test_empty_collection_returns_empty_list():
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(0)
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("rose")
    assert result == []


# ── Similarity score ────────────────────────────────────────────────────────

def test_similarity_score_is_one_minus_distance():
    meta = {"brand": "TestBrand", "name": "TestFrag", "description": "desc",
            "notes_list": "Rose", "concepts_list": "Floral"}
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(1, [meta], [0.20])
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("rose")
    assert len(result) == 1
    assert result[0]["similarity_score"] == round(1 - 0.20, 4)


def test_similarity_score_rounds_to_4_decimal_places():
    meta = {"brand": "B", "name": "N", "description": "", "notes_list": "", "concepts_list": ""}
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(1, [meta], [0.123456789])
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("query")
    score = result[0]["similarity_score"]
    assert score == round(1 - 0.123456789, 4)


# ── Result shape ────────────────────────────────────────────────────────────

def test_result_contains_required_fields():
    meta = {"brand": "Jo Malone", "name": "Wood Sage", "description": "fresh",
            "notes_list": "Cedar, Sage", "concepts_list": "Fresh"}
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(1, [meta], [0.10])
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("woody")
    record = result[0]
    for field in ("brand", "name", "notes", "concepts", "description", "similarity_score"):
        assert field in record, f"Missing field: {field}"


def test_result_maps_metadata_keys():
    """notes_list and concepts_list in metadata map to notes and concepts in output."""
    meta = {"brand": "B", "name": "N", "description": "d",
            "notes_list": "Rose, Cedar", "concepts_list": "Floral"}
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(1, [meta], [0.0])
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("floral")
    assert result[0]["notes"] == "Rose, Cedar"
    assert result[0]["concepts"] == "Floral"


def test_top_k_limits_results():
    """n_results passed to ChromaDB is min(top_k, collection.count())."""
    metas = [{"brand": f"B{i}", "name": f"N{i}", "description": "",
              "notes_list": "", "concepts_list": ""} for i in range(5)]
    dists = [0.1 * i for i in range(5)]
    coll = _make_collection(100, metas, dists)
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = coll
        from services.tools.search_tool import search_fragrance_db
        search_fragrance_db("query", top_k=5)
    call_kwargs = coll.query.call_args.kwargs
    assert call_kwargs["n_results"] == 5


# ── family filter ───────────────────────────────────────────────────────────

def test_family_filter_excludes_non_matching():
    """Results whose concepts_list does not contain the family are excluded."""
    metas = [
        {"brand": "A", "name": "Floral Frag", "description": "", "notes_list": "", "concepts_list": "Floral, Fresh"},
        {"brand": "B", "name": "Woody Frag", "description": "", "notes_list": "", "concepts_list": "Woody"},
    ]
    dists = [0.1, 0.2]
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(2, metas, dists)
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("rose", family="Floral")
    assert len(result) == 1
    assert result[0]["name"] == "Floral Frag"


def test_family_filter_is_case_insensitive():
    """Family filter matches regardless of case."""
    meta = {"brand": "A", "name": "N", "description": "", "notes_list": "", "concepts_list": "Woody, Fresh"}
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(1, [meta], [0.1])
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("cedar", family="woody")
    assert len(result) == 1


def test_no_family_filter_returns_all():
    """Without family filter, all results are returned."""
    metas = [{"brand": f"B{i}", "name": f"N{i}", "description": "", "notes_list": "", "concepts_list": f"Family{i}"}
             for i in range(3)]
    dists = [0.1 * i for i in range(3)]
    with patch("services.tools.search_tool._get_collection") as mock_gc:
        mock_gc.return_value = _make_collection(3, metas, dists)
        from services.tools.search_tool import search_fragrance_db
        result = search_fragrance_db("query")
    assert len(result) == 3
