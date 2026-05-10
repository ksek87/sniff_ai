import logging
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import NotFound
from api.routes import api_blueprint
from limiter import limiter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

app = Flask(__name__)

_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
CORS(app, origins=[o.strip() for o in _origins])

limiter.init_app(app)
app.register_blueprint(api_blueprint, url_prefix="/api/v1")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


_FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "frontend/build")
_HAS_FRONTEND = os.path.isdir(_FRONTEND_BUILD)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if not _HAS_FRONTEND:
        return jsonify({"error": "frontend build not found"}), 404
    try:
        return send_from_directory(_FRONTEND_BUILD, path or "index.html")
    except NotFound:
        return send_from_directory(_FRONTEND_BUILD, "index.html")


# Warm up ChromaDB at worker startup so the first real request doesn't pay
# the 10–30 s HNSWLIB index-load cost. In tests, _get_collection is mocked
# so this is a no-op.
try:
    from services.tools.search_tool import _get_collection as _warmup_chroma
    _warmup_chroma()
except Exception:
    pass


if __name__ == "__main__":
    # Dev-only path — production uses gunicorn via start.sh.
    # Bind to loopback only; never expose the dev server to all interfaces.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)))
