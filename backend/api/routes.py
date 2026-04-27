import re
from flask import Blueprint, request, jsonify
from services.generate_fragrance import generate_fragrance_from_description
from services.feedback import save_feedback, get_metrics
from services.tools.search_tool import search_fragrance_db
from services.nlp import get_all_notes, get_all_families
from limiter import limiter

api_blueprint = Blueprint("api", __name__)

_MAX_DESCRIPTION = 500
_MAX_NOTE_LEN = 100
_MAX_PINNED_NOTES = 10
# Strip ASCII control characters (keep printable + normal whitespace)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _sanitize(text: str) -> str:
    return _CONTROL_RE.sub("", text).strip()


@api_blueprint.route("/generate", methods=["POST"])
@limiter.limit("5 per hour")
def generate():
    data = request.get_json(silent=True) or {}

    description = _sanitize(str(data.get("description", "")))
    if not description:
        return jsonify({"error": "description is required"}), 400
    if len(description) > _MAX_DESCRIPTION:
        return jsonify({"error": f"description must be {_MAX_DESCRIPTION} characters or fewer"}), 400

    raw_notes = data.get("pinned_notes", [])
    if not isinstance(raw_notes, list):
        return jsonify({"error": "pinned_notes must be an array"}), 400
    if len(raw_notes) > _MAX_PINNED_NOTES:
        return jsonify({"error": f"pinned_notes may contain at most {_MAX_PINNED_NOTES} items"}), 400
    pinned_notes = [_sanitize(str(n))[:_MAX_NOTE_LEN] for n in raw_notes if str(n).strip()]

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
@limiter.limit("30 per hour")
def search():
    query = _sanitize(request.args.get("q", ""))
    if not query:
        return jsonify({"error": "q parameter is required"}), 400
    if len(query) > _MAX_DESCRIPTION:
        return jsonify({"error": f"q must be {_MAX_DESCRIPTION} characters or fewer"}), 400
    results = search_fragrance_db(query, top_k=10)
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
