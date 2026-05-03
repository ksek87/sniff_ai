"""
Integration tests covering all /api/v1/* endpoints and input validation.
All external dependencies (Claude API, ChromaDB, NLP models, SQLite) are
mocked by the shared `client` fixture from conftest.py.
"""
import json
import pytest


# ── /health ───────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


# ── /api/v1/generate ─────────────────────────────────────────────────────

def test_generate_returns_200_with_valid_input(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "autumn forest after rain"}),
        content_type="application/json",
    )
    assert resp.status_code == 200


def test_generate_returns_composition_keys(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "warm spicy amber"}),
        content_type="application/json",
    )
    data = resp.get_json()
    for key in ("name", "scent_family", "top_notes", "middle_notes", "base_notes",
                "poetic_description", "similar_fragrances", "confidence_score"):
        assert key in data, f"Missing key: {key}"


def test_generate_percentages_sum_to_100(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "fresh citrus morning"}),
        content_type="application/json",
    )
    data = resp.get_json()
    all_notes = data["top_notes"] + data["middle_notes"] + data["base_notes"]
    total = sum(n["percentage"] for n in all_notes)
    assert abs(total - 100) <= 1


def test_generate_missing_description_returns_400(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "description" in resp.get_json()["error"]


def test_generate_empty_description_returns_400(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "   "}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_generate_description_too_long_returns_400(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "x" * 501}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "500" in resp.get_json()["error"]


def test_generate_strips_control_characters(client):
    """Control chars in description should be stripped, not rejected."""
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "autumn\x00forest\x1bafter rain"}),
        content_type="application/json",
    )
    assert resp.status_code == 200


def test_generate_pinned_notes_not_a_list_returns_400(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "forest", "pinned_notes": "Rose"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "array" in resp.get_json()["error"]


def test_generate_too_many_pinned_notes_returns_400(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "forest", "pinned_notes": ["Note"] * 11}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "10" in resp.get_json()["error"]


def test_generate_accepts_valid_pinned_notes(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "forest", "pinned_notes": ["Rose", "Oud"]}),
        content_type="application/json",
    )
    assert resp.status_code == 200


def test_generate_no_json_body_returns_400(client):
    resp = client.post("/api/v1/generate", data="not json", content_type="text/plain")
    assert resp.status_code == 400


# ── /api/v1/feedback ─────────────────────────────────────────────────────

def _feedback_payload(**overrides):
    base = {
        "session_id": "test-session",
        "input_description": "forest rain",
        "composition": {"name": "Test"},
        "rating": 4,
    }
    base.update(overrides)
    return base


def test_feedback_returns_201(client):
    resp = client.post(
        "/api/v1/feedback",
        data=json.dumps(_feedback_payload()),
        content_type="application/json",
    )
    assert resp.status_code == 201
    assert resp.get_json()["status"] == "ok"


def test_feedback_missing_field_returns_400(client):
    payload = _feedback_payload()
    del payload["rating"]
    resp = client.post(
        "/api/v1/feedback",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_feedback_rating_out_of_range_returns_400(client):
    resp = client.post(
        "/api/v1/feedback",
        data=json.dumps(_feedback_payload(rating=6)),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_feedback_rating_zero_returns_400(client):
    resp = client.post(
        "/api/v1/feedback",
        data=json.dumps(_feedback_payload(rating=0)),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_feedback_non_integer_rating_returns_400(client):
    resp = client.post(
        "/api/v1/feedback",
        data=json.dumps(_feedback_payload(rating=3.5)),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_feedback_with_comment_accepted(client):
    resp = client.post(
        "/api/v1/feedback",
        data=json.dumps(_feedback_payload(comment="Lovely composition")),
        content_type="application/json",
    )
    assert resp.status_code == 201


# ── /api/v1/search ───────────────────────────────────────────────────────

def test_search_returns_200_with_query(client):
    resp = client.get("/api/v1/search?q=pine+forest")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_search_missing_q_returns_400(client):
    resp = client.get("/api/v1/search")
    assert resp.status_code == 400
    assert "q" in resp.get_json()["error"]


def test_search_empty_q_returns_400(client):
    resp = client.get("/api/v1/search?q=")
    assert resp.status_code == 400


def test_search_q_too_long_returns_400(client):
    resp = client.get(f"/api/v1/search?q={'x' * 501}")
    assert resp.status_code == 400


def test_search_accepts_optional_family(client):
    resp = client.get("/api/v1/search?q=rose&family=Floral")
    assert resp.status_code == 200


# ── /api/v1/notes ────────────────────────────────────────────────────────

def test_notes_returns_list(client):
    resp = client.get("/api/v1/notes")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


# ── /api/v1/families ─────────────────────────────────────────────────────

def test_families_returns_list(client):
    resp = client.get("/api/v1/families")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_families_contains_expected_values(client):
    resp = client.get("/api/v1/families")
    families = resp.get_json()
    assert "Floral" in families
    assert "Woody" in families


# ── /api/v1/metrics ──────────────────────────────────────────────────────

def test_metrics_returns_expected_shape(client):
    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_feedback" in data
    assert "average_rating" in data
    assert "rating_distribution" in data


def test_metrics_rating_distribution_has_all_keys(client):
    resp = client.get("/api/v1/metrics")
    dist = resp.get_json()["rating_distribution"]
    for key in ("1", "2", "3", "4", "5"):
        assert key in dist


# ── SPA catch-all ─────────────────────────────────────────────────────────

def test_root_returns_404_when_no_frontend_build(client):
    """Without a bundled React build, the catch-all returns 404."""
    resp = client.get("/")
    assert resp.status_code == 404

def test_unknown_path_returns_404_when_no_frontend_build(client):
    resp = client.get("/some/deep/route")
    assert resp.status_code == 404
