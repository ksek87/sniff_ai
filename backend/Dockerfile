# Stage 1: Build React ─────────────────────────────────────────────────────
FROM node:18-slim AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + React static files ──────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install build deps, compile native extensions (chromadb/hnswlib), then
# strip the compiler toolchain from the final layer to reduce attack surface.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn \
    && apt-get purge -y --auto-remove build-essential cmake \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

COPY backend/ ./

# Dataset lands at /data_collection/dataset.csv — matches the relative path
# computed by ingest_dataset.py (scripts/../../data_collection/dataset.csv)
COPY data_collection/dataset.csv /data_collection/dataset.csv

# React build from Stage 1 — Flask serves these as static files
COPY --from=frontend /frontend/build ./frontend/build

RUN chmod +x start.sh

# Run as non-root user — reduces blast radius if the app is compromised
RUN groupadd -r sniffai && useradd -r -g sniffai -d /app -s /sbin/nologin sniffai \
    && chown -R sniffai:sniffai /app /data_collection \
    && mkdir -p /data && chown sniffai:sniffai /data

USER sniffai

EXPOSE 7860

CMD ["./start.sh"]
