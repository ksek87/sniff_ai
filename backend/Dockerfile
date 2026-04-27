FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Dataset lands at /data_collection/dataset.csv — matches the relative path
# computed by ingest_dataset.py (scripts/../../data_collection/dataset.csv)
COPY data_collection/dataset.csv /data_collection/dataset.csv

RUN chmod +x start.sh

EXPOSE 7860

CMD ["./start.sh"]
