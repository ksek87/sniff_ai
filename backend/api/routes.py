from flask import Blueprint, request, jsonify
from services.generate_fragrance import generate_fragrance_from_description
from services.feedback import save_feedback, get_metrics
from services.tools.search_tool import search_fragrance_db
from services.nlp import get_all_notes, get_all_families

api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400

    pinned_notes = data.get("pinned_notes", [])
    result = generate_fragrance_from_description(description, pinned_notes)
    return jsonify(result)


@api_blueprint.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    required = ("session_id", "input_description", "composition", "rating")
    if not all(k in data for k in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400
    rating = data["rating"]
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "rating must be an integer between 1 and 5"}), 400

    save_feedback(
        session_id=data["session_id"],
        input_description=data["input_description"],
        composition=data["composition"],
        rating=rating,
        comment=data.get("comment", ""),
    )
    return jsonify({"status": "ok"}), 201


@api_blueprint.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    family = request.args.get("family")
    if not query:
        return jsonify({"error": "q parameter is required"}), 400
    results = search_fragrance_db(query, scent_family=family, top_k=10)
    return jsonify(results)


@api_blueprint.route("/notes", methods=["GET"])
def notes():
    return jsonify(get_all_notes())


@api_blueprint.route("/families", methods=["GET"])
def families():
    return jsonify(get_all_families())


@api_blueprint.route("/metrics", methods=["GET"])
def metrics():
    return jsonify(get_metrics())
