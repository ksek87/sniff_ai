#!/bin/bash
set -e

CHROMA_DIR="${CHROMA_PERSIST_DIR:-/data/chroma_db}"

if [ ! -d "$CHROMA_DIR" ] || [ -z "$(ls -A "$CHROMA_DIR" 2>/dev/null)" ]; then
    echo "ChromaDB not found at $CHROMA_DIR — running ingestion (first-start, ~8 min)…"
    python scripts/ingest_dataset.py
    echo "Ingestion complete."
fi

exec gunicorn -w 2 -b "0.0.0.0:${PORT:-7860}" \
    --timeout 120 \
    --access-logfile - \
    app:app
