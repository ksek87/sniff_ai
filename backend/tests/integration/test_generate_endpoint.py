"""
Integration tests for the /api/v1/generate endpoint.
Claude API and ChromaDB are mocked by the shared `client` fixture in conftest.py.
"""
import json
import pytest


def test_generate_returns_200(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "autumn forest after rain"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Autumn Pine Accord"


def test_generate_missing_description_returns_400(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_generate_schema_compliance(client):
    resp = client.post(
        "/api/v1/generate",
        data=json.dumps({"description": "fresh citrus morning"}),
        content_type="application/json",
    )
    data = resp.get_json()
    for key in ("name", "scent_family", "top_notes", "middle_notes", "base_notes",
                "poetic_description", "similar_fragrances", "confidence_score"):
        assert key in data, f"Missing key: {key}"

    all_notes = data["top_notes"] + data["middle_notes"] + data["base_notes"]
    total = sum(n["percentage"] for n in all_notes)
    assert abs(total - 100) <= 1, f"Percentages sum to {total}"


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
