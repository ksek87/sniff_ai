"""
Unit tests for the Composition Agent's pure-Python helpers.
Claude API calls are not exercised here.
"""
import pytest
from services.agents.composer import _normalise_percentages, _fallback_composition


# ── _normalise_percentages ────────────────────────────────────────────────

def _make_comp(top, mid, base):
    return {
        "top_notes": [{"note": "A", "percentage": top}],
        "middle_notes": [{"note": "B", "percentage": mid}],
        "base_notes": [{"note": "C", "percentage": base}],
    }


def test_normalise_exact_100_unchanged():
    comp = _make_comp(20, 50, 30)
    _normalise_percentages(comp)
    total = sum(n["percentage"] for n in
                comp["top_notes"] + comp["middle_notes"] + comp["base_notes"])
    assert abs(total - 100) <= 0.1


def test_normalise_scales_up_from_50():
    comp = _make_comp(10, 25, 15)  # sums to 50
    _normalise_percentages(comp)
    total = sum(n["percentage"] for n in
                comp["top_notes"] + comp["middle_notes"] + comp["base_notes"])
    assert abs(total - 100) <= 0.1


def test_normalise_scales_down_from_200():
    comp = _make_comp(40, 100, 60)  # sums to 200
    _normalise_percentages(comp)
    total = sum(n["percentage"] for n in
                comp["top_notes"] + comp["middle_notes"] + comp["base_notes"])
    assert abs(total - 100) <= 0.1


def test_normalise_skips_when_within_tolerance():
    comp = _make_comp(20, 50, 30)  # exact 100 — no scaling needed
    original_top = comp["top_notes"][0]["percentage"]
    _normalise_percentages(comp)
    assert comp["top_notes"][0]["percentage"] == original_top


def test_normalise_zero_total_no_crash():
    comp = _make_comp(0, 0, 0)
    _normalise_percentages(comp)  # should not raise


def test_normalise_empty_composition():
    comp = {"top_notes": [], "middle_notes": [], "base_notes": []}
    _normalise_percentages(comp)  # should not raise


# ── _fallback_composition ─────────────────────────────────────────────────

def test_fallback_has_required_keys():
    result = _fallback_composition("pine forest", {})
    for key in ("name", "scent_family", "top_notes", "middle_notes",
                "base_notes", "poetic_description", "similar_fragrances", "confidence_score"):
        assert key in result


def test_fallback_percentages_sum_to_100():
    result = _fallback_composition("desc", {})
    total = sum(n["percentage"] for n in
                result["top_notes"] + result["middle_notes"] + result["base_notes"])
    assert abs(total - 100) <= 1


def test_fallback_includes_reference_fragrances():
    orch = {
        "reference_fragrances": [
            {"brand": "Jo Malone", "name": "Wood Sage", "similarity_score": 0.9},
            {"brand": "Chanel", "name": "No.5", "similarity_score": 0.8},
        ]
    }
    result = _fallback_composition("desc", orch)
    assert len(result["similar_fragrances"]) == 2
    assert result["similar_fragrances"][0]["brand"] == "Jo Malone"


def test_fallback_description_in_poetic_text():
    result = _fallback_composition("autumn leaves", {})
    assert "autumn leaves" in result["poetic_description"]
