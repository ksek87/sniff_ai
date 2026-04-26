# Sniff AI

Sniff AI translates poetic, descriptive language ("a thunderstorm over a pine forest at dusk") into professional fragrance compositions — complete with a structured notes pyramid (top / middle / base), percentage breakdowns, a custom name, and real-world reference fragrances.

Live frontend: **[ksek87.github.io/sniff_ai](https://ksek87.github.io/sniff_ai/)**

---

## How It Works

```
User description
  → NLP preprocessing (spaCy note detection, sklearn scent-family classifier)
  → ChromaDB semantic search (sentence-transformers all-MiniLM-L6-v2)
  → Orchestrator Agent (Claude claude-sonnet-4-6, tool use)
  → Composition Agent (Claude claude-sonnet-4-6, structured JSON output)
  → Fragrance Card (React frontend)
```

The system uses **two Claude API calls** per generation. No local LLM is run. The NLP layer (spaCy + sklearn + sentence-transformers) runs entirely on CPU and adds ~50ms.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM reasoning | Anthropic Claude claude-sonnet-4-6 (API) |
| Vector search | ChromaDB (embedded, cosine similarity) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| NER | spaCy `EntityRuler` (rule-based, no training) |
| Scent classifier | scikit-learn TF-IDF + Logistic Regression |
| Backend | Python 3.11, Flask, gunicorn |
| Frontend | React 18, TypeScript 5, Axios |
| Frontend hosting | GitHub Pages |
| Backend hosting | Hugging Face Spaces (Docker, free tier) |

---

## Architecture

### Backend API (`/api/v1/`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/generate` | POST | Generate fragrance from description |
| `/feedback` | POST | Submit 1–5 star rating |
| `/search` | GET | Semantic search over fragrance database |
| `/notes` | GET | List all available fragrance notes |
| `/families` | GET | List scent families |
| `/metrics` | GET | Aggregated feedback metrics |
| `/health` | GET | Health check |

### Output Schema

```json
{
  "name": "Twilight Pine Accord",
  "scent_family": "Woody Aromatic",
  "top_notes":    [{"note": "Bergamot",    "percentage": 15}],
  "middle_notes": [{"note": "Pine Needle", "percentage": 25}],
  "base_notes":   [{"note": "Cedarwood",   "percentage": 35}],
  "poetic_description": "…",
  "similar_fragrances": [{"brand": "Jo Malone", "name": "Wood Sage & Sea Salt", "similarity_score": 0.87}],
  "confidence_score": 0.91
}
```

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node 18+
- An `ANTHROPIC_API_KEY` (get one at [console.anthropic.com](https://console.anthropic.com))

### Backend

```bash
cd backend
pip install -r requirements.txt

# One-time: populate ChromaDB and generate note_profiles.json (~8 min)
python scripts/ingest_dataset.py

# Start the API server
ANTHROPIC_API_KEY=sk-ant-... python app.py
# → http://localhost:7860
```

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
REACT_APP_API_URL=http://localhost:7860 npm start
# → http://localhost:3000
```

### Docker Compose (recommended for local dev)

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY
docker compose up --build
```

Backend at `localhost:5000`, frontend at `localhost:3000`.  
The backend runs `start.sh` which auto-populates ChromaDB on first start (~8 min), then starts gunicorn.

---

## Deployment

### Backend — Hugging Face Spaces

1. Create a new Space (Docker SDK, public) at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Set Space secrets: `ANTHROPIC_API_KEY`, `CHROMA_PERSIST_DIR=/data/chroma_db`
3. Deploy the GHCR image: `ghcr.io/ksek87/sniff_ai/backend:latest`
4. First startup ingests the dataset (~8 min); ChromaDB persists at `/data/chroma_db`

### Frontend — GitHub Pages

The `deploy.yml` workflow builds and deploys automatically on every push to `main`.

Set the GitHub Actions secret `BACKEND_URL` to your HF Space URL (e.g. `https://ksek87-sniff-ai.hf.space`) so the frontend build wires up the correct API endpoint.

```
Repo Settings → Secrets and variables → Actions → New repository secret
Name: BACKEND_URL
Value: https://your-space-name.hf.space
```

---

## Data

The fragrance database (`data_collection/dataset.csv`) contains **13,644 records** scraped from public fragrance catalogues, with fields: Brand, Name, Description, Notes (list), Concepts (list).

One-time ingestion via `scripts/ingest_dataset.py`:
- Encodes all records with `all-MiniLM-L6-v2` (384-dim vectors)
- Stores in ChromaDB with cosine HNSW index
- Generates `backend/data/note_profiles.json` (volatility + co-occurrence pairs for 1,000+ notes)

---

## Project Phases

- [x] **Phase 1** — Data collection & curation (13,644 fragrance records)
- [x] **Phase 2** — Agentic pipeline (Claude API + ChromaDB + NLP layer)
- [x] **Phase 3** — React frontend (Fragrance Card, Notes Pyramid, feedback)
- [ ] **Phase 4** — Personalization (pinned notes, scent family filter)
- [ ] **Phase 5** — Search panel + metrics dashboard
- [ ] **Phase 6** — Feedback loop (re-weight classifier on ratings)

---

## Contributing

PRs welcome. For larger changes, open an issue first to discuss the approach.

Product management documentation (roadmaps, feature specs): [`/product-management`](product-management/)
