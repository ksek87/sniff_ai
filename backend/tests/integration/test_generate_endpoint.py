"""
Integration tests for the /api/v1/generate endpoint.
Claude API and ChromaDB are mocked so tests run without external services.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


_MOCK_COMPOSITION = {
    "name": "Autumn Pine Accord",
    "scent_family": "Woody",
    "top_notes": [{"note": "Petitgrain", "percentage": 15}, {"note": "Bergamot", "percentage": 10}],
    "middle_notes": [{"note": "Pine Needle", "percentage": 30}, {"note": "Clary Sage", "percentage": 15}],
    "base_notes": [{"note": "Cedarwood", "percentage": 20}, {"note": "Vetiver", "percentage": 10}],
    "poetic_description": "An autumn walk through a pine forest after rain.",
    "similar_fragrances": [{"brand": "Test Brand", "name": "Forest Walk", "similarity_score": 0.88}],
    "confidence_score": 0.92,
}


@pytest.fixture()
def client():
    with patch("services.agents.orchestrator.anthropic"), \
         patch("services.agents.composer.anthropic"), \
         patch("services.tools.search_tool._get_collection") as mock_coll, \
         patch("services.nlp.scent_classifier.ScentClassifier._load_or_train"), \
         patch("services.nlp.note_extractor.NoteExtractor._load_notes"), \
         patch("services.nlp.note_extractor.NoteExtractor._build_ruler"):

        mock_coll.return_value.count.return_value = 0
        mock_coll.return_value.query.return_value = {"metadatas": [[]], "distances": [[]]}

        with patch("services.generate_fragrance.orchestrator.run") as mock_orch, \
             patch("services.generate_fragrance.composer.run") as mock_comp:
            mock_orch.return_value = {"reference_fragrances": [], "recommended_notes": {}, "reasoning": "test"}
            mock_comp.return_value = _MOCK_COMPOSITION

            from app import app
            app.config["TESTING"] = True
            yield app.test_client()


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
    # Required keys
    for key in ("name", "scent_family", "top_notes", "middle_notes", "base_notes",
                "poetic_description", "similar_fragrances", "confidence_score"):
        assert key in data, f"Missing key: {key}"

    # Percentages sum to 100
    all_notes = data["top_notes"] + data["middle_notes"] + data["base_notes"]
    total = sum(n["percentage"] for n in all_notes)
    assert abs(total - 100) <= 1, f"Percentages sum to {total}"


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
