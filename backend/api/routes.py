import logging
import re
from flask import Blueprint, request, jsonify
from services.generate_fragrance import generate_fragrance_from_description
from services.feedback import save_feedback, get_metrics
from services.shares import save_share, get_share
from services.nlp import get_all_notes
from limiter import limiter

logger = logging.getLogger(__name__)

try:
    from langfuse.decorators import langfuse_context
    _LANGFUSE = True
except ImportError:
    _LANGFUSE = False

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

    if _LANGFUSE:
        langfuse_context.update_current_trace(
            user_id=data.get("session_id"),
            input=description,
            tags=["generate"],
        )

    try:
        result = generate_fragrance_from_description(description, pinned_notes)
    except Exception:
        logger.exception("Generation failed for description=%r", description)
        return jsonify({"error": "Generation failed. Please try again."}), 500
    return jsonify(result)


@api_blueprint.route("/feedback", methods=["POST"])
@limiter.limit("20 per hour")
def feedback():
    data = request.get_json(silent=True) or {}
    required = ("session_id", "input_description", "composition", "rating")
    if not all(k in data for k in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400
    rating = data["rating"]
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "rating must be an integer between 1 and 5"}), 400

    try:
        save_feedback(
            session_id=data["session_id"],
            input_description=data["input_description"],
            composition=data["composition"],
            rating=rating,
            comment=data.get("comment", ""),
        )
    except Exception:
        logger.exception("Feedback save failed for session=%r", data.get("session_id"))
        return jsonify({"error": "Failed to save feedback. Please try again."}), 500
    return jsonify({"status": "ok"}), 201


@api_blueprint.route("/notes", methods=["GET"])
def notes():
    return jsonify(get_all_notes())


@api_blueprint.route("/metrics", methods=["GET"])
@limiter.limit("60 per minute")
def metrics():
    return jsonify(get_metrics())


@api_blueprint.route("/share", methods=["POST"])
@limiter.limit("10 per hour")
def create_share():
    data = request.get_json(silent=True) or {}
    description = _sanitize(str(data.get("input_description", "")))
    if not description:
        return jsonify({"error": "input_description is required"}), 400
    composition = data.get("composition")
    if not isinstance(composition, dict):
        return jsonify({"error": "composition is required"}), 400
    try:
        token = save_share(description, composition)
    except Exception:
        logger.exception("Share save failed")
        return jsonify({"error": "Failed to create share link. Please try again."}), 500
    return jsonify({"token": token}), 201


@api_blueprint.route("/share/<token>", methods=["GET"])
@limiter.limit("120 per hour")
def fetch_share(token: str):
    if not token.isalnum() or len(token) != 32:
        return jsonify({"error": "Invalid share token"}), 400
    try:
        result = get_share(token)
    except Exception:
        logger.exception("Share lookup failed for token=%r", token)
        return jsonify({"error": "Failed to retrieve shared fragrance."}), 500
    if result is None:
        return jsonify({"error": "Share not found"}), 404
    return jsonify(result)
