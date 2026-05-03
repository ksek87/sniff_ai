import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from api.routes import api_blueprint
from limiter import limiter

load_dotenv()

app = Flask(__name__)

_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
CORS(app, origins=[o.strip() for o in _origins])

limiter.init_app(app)
app.register_blueprint(api_blueprint, url_prefix="/api/v1")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


_FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "frontend/build")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if not os.path.isdir(_FRONTEND_BUILD):
        return jsonify({"error": "frontend build not found"}), 404
    # send_from_directory uses werkzeug safe_join, which blocks path traversal
    # and raises NotFound for missing files — no manual os.path.join needed.
    from werkzeug.exceptions import NotFound
    try:
        return send_from_directory(_FRONTEND_BUILD, path or "index.html")
    except NotFound:
        return send_from_directory(_FRONTEND_BUILD, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
