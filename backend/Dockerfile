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

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ ./

# Dataset lands at /data_collection/dataset.csv — matches the relative path
# computed by ingest_dataset.py (scripts/../../data_collection/dataset.csv)
COPY data_collection/dataset.csv /data_collection/dataset.csv

# React build from Stage 1 — Flask serves these as static files
COPY --from=frontend /frontend/build ./frontend/build

RUN chmod +x start.sh

EXPOSE 7860

CMD ["./start.sh"]
