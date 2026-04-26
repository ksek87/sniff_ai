import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from api.routes import api_blueprint

load_dotenv()

app = Flask(__name__)

_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://ksek87.github.io",
).split(",")
CORS(app, origins=[o.strip() for o in _origins])

app.register_blueprint(api_blueprint, url_prefix="/api/v1")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
