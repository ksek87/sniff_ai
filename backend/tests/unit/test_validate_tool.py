import pytest
from services.tools.validate_tool import validate_composition


def _make_composition(**overrides):
    base = {
        "name": "Test Accord",
        "scent_family": "Woody",
        "top_notes": [{"note": "Bergamot", "percentage": 20}],
        "middle_notes": [{"note": "Rose", "percentage": 50}],
        "base_notes": [{"note": "Cedarwood", "percentage": 30}],
        "similar_fragrances": [],
    }
    base.update(overrides)
    return base


def test_valid_composition():
    result = validate_composition(_make_composition())
    assert result["valid"] is True
    assert result["errors"] == []


def test_percentages_not_summing_to_100():
    comp = _make_composition(
        top_notes=[{"note": "Bergamot", "percentage": 10}],
        middle_notes=[{"note": "Rose", "percentage": 40}],
        base_notes=[{"note": "Cedarwood", "percentage": 20}],
    )
    result = validate_composition(comp)
    assert result["valid"] is False
    assert any("70%" in e for e in result["errors"])


def test_unknown_scent_family():
    comp = _make_composition(scent_family="Imaginary")
    result = validate_composition(comp)
    assert result["valid"] is False
    assert any("Imaginary" in e for e in result["errors"])


def test_too_many_similar_fragrances():
    comp = _make_composition(
        similar_fragrances=[{"brand": "X", "name": str(i), "similarity_score": 0.9} for i in range(6)]
    )
    result = validate_composition(comp)
    assert result["valid"] is False


def test_empty_composition():
    result = validate_composition({})
    assert result["valid"] is False
