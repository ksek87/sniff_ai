# Sniff AI

**[Try it live →](https://ksek87.github.io/sniff_ai/)**

*From memory to molecule.* Sniff AI translates poetic, descriptive language into professional fragrance compositions — a notes pyramid (top / heart / base with percentages), a custom name, and real-world reference matches.

> *"A thunderstorm over a pine forest at dusk"* → **Twilight Pine Accord** — Woody Aromatic · Bergamot + Petitgrain · Pine Needle + Clary Sage · Cedarwood + Musk

---

## Architecture

```
POST /generate
        │
        ├─① NLP Preprocessing ──────────────────── run in parallel ──┐
        │    spaCy EntityRuler  → detected notes                      │
        │    TF-IDF + LogReg    → scent family + confidence           │
        │                                                             │
        └─② Vector Search ──────────────────────────────────────────┘
             all-MiniLM-L6-v2 → ChromaDB (13,644 records, cosine HNSW)
        │
        ▼
③ Orchestrator Agent  (Claude claude-sonnet-4-6, tool-use)
   ┌─ Round 1: get_note_profile(all_candidates)
   │           ↳ volatility · family · pairings · shared_pairings
   │           [parallel if multiple tool calls in same round]
   └─ Round 2: end_turn → recommended_notes JSON
        │
        ▼
④ Composer Agent  (Claude claude-sonnet-4-6, single call)
   trimmed orchestrator context → FragranceComposition JSON
        │
        ▼
   React 18 / TypeScript FragranceCard
```

Two LLM calls per generation (orchestrator + composer). NLP and vector search run concurrently before either LLM call. Multiple tool calls within the same orchestrator round are dispatched in parallel via `ThreadPoolExecutor`.

---

## Agentic Design

### Why two agents?

The pipeline splits into two deliberately separate concerns:

**Orchestrator** — a *grounding* agent. It has no idea what the final formula looks like. Its only job is to retrieve relevant fragrance knowledge and recommend which notes belong in each tier. It uses tools backed by real data so Claude can't hallucinate notes.

**Composer** — a *formulation* agent. It receives the orchestrator's trimmed output (recommended notes + 3 reference fragrances + short reasoning) and produces the final structured JSON: name, percentages, poetic description, confidence score. It never touches the database directly.

This separation keeps each prompt small, focused, and independently improvable.

### Orchestrator tools

| Tool | Purpose | Design note |
|---|---|---|
| `search_fragrance_db` | Semantic search over 13,644 records (optional family filter) | Only called if pre-loaded references are insufficient |
| `get_note_profile` | Volatility, family, pairings for a list of notes in one call | Returns `shared_pairings` (intersection of all notes' pairing sets) when ≥2 notes requested — eliminates a separate round-trip |

`validate_composition` and `get_note_pairings` were deliberately removed from the orchestrator:
- `validate_composition` belongs to the composer step. Giving it to the orchestrator caused Claude to waste a round building a draft formula purely to validate it.
- `get_note_pairings` is now merged into `get_note_profile` via `shared_pairings`, collapsing the typical 3-round flow to 2.

### Token optimisation

Three cache breakpoints per request (Anthropic prompt caching, 90% discount on hits):

```
[system prompt]       ← cache breakpoint 1  (cross-request)
[tools block]         ← cache breakpoint 2  (cross-request, within TTL)
[user message]        ← cache breakpoint 3  (within-request: rounds 2+ pay only for new content)
[accumulated rounds]  ← billed at full price (grows ~300 tokens per round)
```

Additional compression:
- `initial_hits` formatted as compact text (3 references, ~80 tokens) instead of `json.dumps(indent=2)` (~350 tokens)
- Tool results stripped of non-essential fields before appending to conversation history
- Composer receives a trimmed orchestrator result (`{notes, refs, reasoning}`) rather than the full response
- `max_tokens` right-sized: orchestrator 1024, composer 1500

Net result: **~65–70% fewer billed input tokens** vs. the naive implementation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Anthropic Claude claude-sonnet-4-6 |
| Vector store | ChromaDB (embedded, cosine HNSW) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| NER | spaCy `EntityRuler` — rule-based, no training data needed |
| Scent classifier | scikit-learn TF-IDF + Logistic Regression (trained on dataset) |
| Backend | Python 3.11 · Flask · gunicorn (4 workers) |
| Frontend | React 18 · TypeScript 5 |
| Deployment | Single Docker container — Flask serves both API and React build |

---

## Data & Knowledge

**Dataset** — `data_collection/dataset.csv`: 13,644 fragrance records (Brand, Name, Description, Notes, Concepts).

**Note profiles** — `backend/data/note_profiles.json`: 174 hand-crafted notes from perfumery literature (Arctander, IFRA, accord theory), augmented with ~1,000 additional notes mined from the dataset via co-occurrence analysis. Each entry: `{volatility, family, descriptors, pairs_well_with}`.

The ingestion script (`backend/scripts/ingest_dataset.py`) runs once at first boot (~8 min):
1. Encodes all 13,644 records with `all-MiniLM-L6-v2` → ChromaDB
2. Merges the hand-crafted corpus with dataset-derived pairings

---

## Performance

Cold-start latency was the main production reliability issue ("first request always slow"). Three root causes, all fixed:

| Problem | Fix |
|---|---|
| ChromaDB HNSWLIB index loads on first query (10–30 s) | `gunicorn post_worker_init` calls `search_fragrance_db("warmup")` after each worker forks |
| spaCy + sklearn models load on first request | `post_worker_init` also calls `preprocess("warmup")` — all models lazy-init thread-safely, then pre-loaded |
| New Anthropic TCP/TLS connection per request | Singleton client reused across requests |

NLP singletons (`NoteExtractor`, `ScentClassifier`, `Embedder`) use double-checked locking so they're created exactly once per worker under concurrent load.

---

## API

All endpoints under `/api/v1/`.

| Method | Path | Rate limit | Purpose |
|---|---|---|---|
| POST | `/generate` | 5 / hour | Generate fragrance from description + optional pinned notes |
| POST | `/feedback` | 20 / hour | Submit 1–5 star rating with optional comment |
| GET | `/notes` | — | All available fragrance note names |
| GET | `/metrics` | 60 / min | Aggregated feedback statistics |
| POST | `/share` | 10 / hour | Save a composition and get a shareable token |
| GET | `/share/<token>` | 120 / hour | Retrieve a shared composition |
| GET | `/health` | — | Liveness check |

### Generation request / response

```jsonc
// POST /api/v1/generate
{ "description": "autumn rain on pine needles", "pinned_notes": ["Oud"] }

// 200 OK
{
  "name": "Twilight Pine Accord",
  "scent_family": "Woody",
  "top_notes":    [{ "note": "Bergamot",    "percentage": 15 }],
  "middle_notes": [{ "note": "Pine Needle", "percentage": 30 }],
  "base_notes":   [{ "note": "Oud",         "percentage": 30 },
                   { "note": "Cedarwood",   "percentage": 25 }],
  "poetic_description": "...",
  "similar_fragrances": [{ "brand": "Jo Malone", "name": "Wood Sage & Sea Salt", "similarity_score": 0.87 }],
  "confidence_score": 0.91
}
```

---

## Local Development

**Prerequisites:** Python 3.11+, Node 18+, `ANTHROPIC_API_KEY`

```bash
# Backend
cd backend
pip install -r requirements.txt
python scripts/ingest_dataset.py   # one-time, ~8 min
ANTHROPIC_API_KEY=sk-ant-... python app.py
# → http://localhost:5000

# Frontend (separate terminal)
cd frontend
npm ci --legacy-peer-deps
REACT_APP_API_URL=http://localhost:5000 npm start
# → http://localhost:3000
```

**Docker Compose (recommended)**

```bash
cp .env.example .env   # add ANTHROPIC_API_KEY
docker compose up --build
```

---

## Deployment (Hugging Face Spaces)

```bash
docker build -f backend/Dockerfile -t sniff-ai .
```

1. Create a Hugging Face Space (Docker SDK)
2. Secrets: `ANTHROPIC_API_KEY`, `CORS_ORIGINS=https://ksek87.github.io`, `CHROMA_PERSIST_DIR=/data/chroma_db`
3. Push `ghcr.io/ksek87/sniff_ai/backend:latest` (built by `docker.yml` on every push to `main`)
4. First boot auto-ingests ChromaDB (~8 min), then serves on port 7860

Frontend deploys to GitHub Pages via `pages.yml`.

---

## Testing

```bash
# Backend — all external calls mocked, no API key needed
python -m pytest backend/tests/ -q

# Frontend type check
cd frontend && npx tsc --noEmit
```
