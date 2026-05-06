# Sniff AI

Sniff AI translates poetic, descriptive language into professional fragrance compositions — complete with a notes pyramid (top / middle / base with percentages), a custom name, and real-world reference fragrances.

> *"A thunderstorm over a pine forest at dusk"* → **Twilight Pine Accord** — Woody Aromatic, top: Bergamot + Petitgrain, heart: Pine Needle + Clary Sage, base: Cedarwood + Musk

---

## Features

- **Natural language input** — describe a mood, memory, or scene; receive a structured formula
- **Notes pyramid** — top / heart / base breakdown with percentages summing to 100%
- **Pinned notes** — constrain the composition to specific ingredients you want included
- **Reference fragrances** — 3 real-world matches from a database of 13,644 records
- **Semantic search** — explore the fragrance database by description, mood, or ingredient
- **Feedback** — 1–5 star rating with optional comment; feeds a continuous improvement loop
- **Metrics** — community rating distribution

---

## How It Works

```
User description
  → NLP preprocessing   (spaCy note detection · sklearn scent-family classifier · ~50ms)
  → ChromaDB search     (sentence-transformers all-MiniLM-L6-v2 · 13,644 records)
  → Orchestrator Agent  (Claude claude-sonnet-4-6 · tool-use loop · up to 5 rounds)
  → Composition Agent   (Claude claude-sonnet-4-6 · structured JSON output)
  → Fragrance Card      (React 18 · TypeScript 5)
```

Two Claude API calls per generation. The NLP layer runs on CPU, no GPU required.
Both agents use **prompt caching** — system prompts are cached ephemerally, reducing API costs ~90% on repeat calls.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Anthropic Claude claude-sonnet-4-6 |
| Vector search | ChromaDB (embedded, cosine HNSW) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384-dim) |
| NER | spaCy `EntityRuler` (rule-based, zero training) |
| Scent classifier | scikit-learn TF-IDF + Logistic Regression |
| Backend | Python 3.11 · Flask · gunicorn |
| Frontend | React 18 · TypeScript 5 · Axios |
| Deployment | Single Docker container — Flask serves both API and React build |

---

## API

All endpoints are under `/api/v1/`.

| Method | Path | Rate limit | Purpose |
|---|---|---|---|
| POST | `/generate` | 5 / hour | Generate fragrance from description + optional pinned notes |
| POST | `/feedback` | 20 / hour | Submit 1–5 star rating with optional comment |
| GET | `/search` | 30 / hour | Semantic search over fragrance database |
| GET | `/notes` | — | All available fragrance note names |
| GET | `/families` | — | 9 canonical scent families |
| GET | `/metrics` | 60 / min | Aggregated feedback statistics |
| GET | `/health` | — | Liveness check |

### Generation request / response

```jsonc
// POST /api/v1/generate
{ "description": "autumn rain on pine needles", "pinned_notes": ["Oud"] }

// Response
{
  "name": "Twilight Pine Accord",
  "scent_family": "Woody",
  "top_notes":    [{ "note": "Bergamot",    "percentage": 15 }],
  "middle_notes": [{ "note": "Pine Needle", "percentage": 30 }],
  "base_notes":   [{ "note": "Oud",         "percentage": 30 }, { "note": "Cedarwood", "percentage": 25 }],
  "poetic_description": "…",
  "similar_fragrances": [{ "brand": "Jo Malone", "name": "Wood Sage & Sea Salt", "similarity_score": 0.87 }],
  "confidence_score": 0.91
}
```

---

## Local Development

### Prerequisites

- Python 3.11+, Node 18+
- `ANTHROPIC_API_KEY` — get one at [console.anthropic.com](https://console.anthropic.com)

### Backend

```bash
cd backend
pip install -r requirements.txt

# One-time: ingest 13,644 records into ChromaDB and generate note_profiles.json (~8 min)
python scripts/ingest_dataset.py

ANTHROPIC_API_KEY=sk-ant-... python app.py
# → http://localhost:5000
```

### Frontend (dev server)

```bash
cd frontend
npm ci --legacy-peer-deps
REACT_APP_API_URL=http://localhost:5000 npm start
# → http://localhost:3000
```

### Docker Compose (recommended)

```bash
cp .env.example .env          # fill in ANTHROPIC_API_KEY
docker compose up --build
# Backend: localhost:5000 (auto-ingests ChromaDB on first start)
```

---

## Deployment (Hugging Face Spaces)

The single Docker image serves both the Flask API and the compiled React app.

```bash
# Build image from repo root (multi-stage: Node 18 → Python 3.11)
docker build -f backend/Dockerfile -t sniff-ai .
```

1. Create a [Hugging Face Space](https://huggingface.co/spaces) (Docker SDK, public)
2. Add secrets: `ANTHROPIC_API_KEY`, `CHROMA_PERSIST_DIR=/data/chroma_db`
3. Push `ghcr.io/ksek87/sniff_ai/backend:latest` (built by `docker.yml` on every push to `main`)
4. Point the Space at that image — first boot auto-ingests ChromaDB (~8 min), then serves on port 7860

---

## Testing

```bash
# Backend — 95 tests, no API key required (all external calls mocked)
python -m pytest backend/tests/ -q

# Frontend type check
cd frontend && npx tsc --noEmit
```

---

## Data

`data_collection/dataset.csv` — 13,644 fragrance records (Brand, Name, Description, Notes, Concepts).

`backend/scripts/ingest_dataset.py` (one-time):
- Encodes all records with `all-MiniLM-L6-v2` into ChromaDB
- Generates `backend/data/note_profiles.json` (volatility class + co-occurrence pairs for 1,000+ notes)

---

## Project Status

- [x] Data collection — 13,644 fragrance records
- [x] Agentic pipeline — Claude API · ChromaDB · NLP layer
- [x] Core UI — Fragrance Card · Notes Pyramid
- [x] Personalization — pinned notes (NoteSelector)
- [x] Feedback — star rating + comment (FeedbackWidget)
- [x] Search — semantic fragrance database search (SearchPanel)
- [x] Metrics — rating distribution dashboard (MetricsDashboard)
- [x] Deployment — single-container Docker · Hugging Face Spaces
- [ ] Feedback loop — re-weight scent classifier on accumulated ratings
