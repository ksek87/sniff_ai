import pytest
from services.tools.validate_tool import validate_composition, _VALID_FAMILIES


def _comp(**overrides):
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


# ── Valid cases ───────────────────────────────────────────────────────────

def test_valid_composition():
    result = validate_composition(_comp())
    assert result["valid"] is True
    assert result["errors"] == []


@pytest.mark.parametrize("family", sorted(_VALID_FAMILIES))
def test_all_canonical_families_are_valid(family):
    result = validate_composition(_comp(scent_family=family))
    assert result["valid"] is True


def test_percentages_within_tolerance_99():
    comp = _comp(
        top_notes=[{"note": "Bergamot", "percentage": 20}],
        middle_notes=[{"note": "Rose", "percentage": 50}],
        base_notes=[{"note": "Cedarwood", "percentage": 29}],  # sums to 99
    )
    result = validate_composition(comp)
    assert result["valid"] is True


def test_percentages_within_tolerance_101():
    comp = _comp(
        top_notes=[{"note": "Bergamot", "percentage": 20}],
        middle_notes=[{"note": "Rose", "percentage": 51}],
        base_notes=[{"note": "Cedarwood", "percentage": 30}],  # sums to 101
    )
    result = validate_composition(comp)
    assert result["valid"] is True


def test_max_similar_fragrances_exactly_five():
    comp = _comp(
        similar_fragrances=[{"brand": "X", "name": str(i), "similarity_score": 0.9} for i in range(5)]
    )
    assert validate_composition(comp)["valid"] is True


def test_tier_with_max_six_notes():
    notes = [{"note": f"Note{i}", "percentage": 10} for i in range(6)]
    comp = _comp(
        top_notes=notes,
        middle_notes=[{"note": "Rose", "percentage": 25}],
        base_notes=[{"note": "Musk", "percentage": 15}],
    )
    # 60+25+15 = 100
    assert validate_composition(comp)["valid"] is True


# ── Invalid cases ─────────────────────────────────────────────────────────

def test_percentages_not_summing_to_100():
    comp = _comp(
        top_notes=[{"note": "Bergamot", "percentage": 10}],
        middle_notes=[{"note": "Rose", "percentage": 40}],
        base_notes=[{"note": "Cedarwood", "percentage": 20}],
    )
    result = validate_composition(comp)
    assert result["valid"] is False
    assert any("70%" in e["message"] for e in result["errors"])


def test_unknown_scent_family():
    result = validate_composition(_comp(scent_family="Imaginary"))
    assert result["valid"] is False
    assert any("Imaginary" in e["message"] for e in result["errors"])


def test_empty_scent_family_is_valid():
    # Empty string bypasses the family check (the field is optional)
    result = validate_composition(_comp(scent_family=""))
    assert result["valid"] is True


def test_too_many_similar_fragrances():
    comp = _comp(
        similar_fragrances=[{"brand": "X", "name": str(i), "similarity_score": 0.9} for i in range(6)]
    )
    result = validate_composition(comp)
    assert result["valid"] is False


def test_empty_composition():
    result = validate_composition({})
    assert result["valid"] is False


def test_tier_with_zero_notes_top():
    comp = _comp(top_notes=[])
    result = validate_composition(comp)
    assert result["valid"] is False
    assert any("top" in e["message"] for e in result["errors"])


def test_tier_with_zero_notes_middle():
    comp = _comp(middle_notes=[])
    result = validate_composition(comp)
    assert result["valid"] is False
    assert any("middle" in e["message"] for e in result["errors"])


def test_tier_with_zero_notes_base():
    comp = _comp(base_notes=[])
    result = validate_composition(comp)
    assert result["valid"] is False
    assert any("base" in e["message"] for e in result["errors"])


def test_tier_with_seven_notes():
    seven_notes = [{"note": f"Note{i}", "percentage": 10} for i in range(7)]
    comp = _comp(top_notes=seven_notes, middle_notes=[], base_notes=[])
    result = validate_composition(comp)
    assert result["valid"] is False
    assert any("7 notes" in e["message"] for e in result["errors"])


def test_multiple_errors_reported():
    # Both bad family AND bad percentages
    comp = _comp(
        scent_family="Imaginary",
        top_notes=[{"note": "X", "percentage": 10}],
        middle_notes=[],
        base_notes=[],
    )
    result = validate_composition(comp)
    assert result["valid"] is False
    assert len(result["errors"]) >= 2


# ── Error shape ───────────────────────────────────────────────────────────────

def test_error_has_message_and_severity_fields():
    result = validate_composition(_comp(scent_family="Imaginary"))
    for err in result["errors"]:
        assert "message" in err
        assert "severity" in err
        assert err["severity"] in ("critical", "warning")


def test_percentage_error_is_critical():
    comp = _comp(
        top_notes=[{"note": "Bergamot", "percentage": 10}],
        middle_notes=[{"note": "Rose", "percentage": 40}],
        base_notes=[{"note": "Cedarwood", "percentage": 20}],
    )
    result = validate_composition(comp)
    pct_errors = [e for e in result["errors"] if "70%" in e["message"]]
    assert pct_errors and pct_errors[0]["severity"] == "critical"


def test_too_many_notes_tier_is_warning():
    seven_notes = [{"note": f"Note{i}", "percentage": 10} for i in range(7)]
    comp = _comp(top_notes=seven_notes, middle_notes=[{"note": "Rose", "percentage": 15}], base_notes=[{"note": "Musk", "percentage": 15}])
    result = validate_composition(comp)
    tier_errors = [e for e in result["errors"] if "7 notes" in e["message"]]
    assert tier_errors and tier_errors[0]["severity"] == "warning"
