# Sniff AI

**[Try it live →](https://ksek87.github.io/sniff_ai/)**

---

## The idea

Fragrance is one of the most emotionally vivid senses, but describing a scent you want is almost impossible without a perfumer's vocabulary. People reach for metaphors — *"a walk through a pine forest after rain"*, *"warm, like old books and amber"*, *"the sea at five in the morning"* — but those descriptions live in a completely different language from the ingredient lists, volatility classes, and accord structures that actually make a perfume.

Sniff AI bridges that gap. You describe a feeling or a memory in plain language. It produces a professional fragrance composition — a notes pyramid with percentages, a name, a poetic description written back in your register, and real-world references from a database of 13,644 fragrances. No perfumery knowledge required.

> *"A thunderstorm over a pine forest at dusk"* → **Twilight Pine Accord** — Woody Aromatic · Bergamot + Petitgrain · Pine Needle + Clary Sage · Cedarwood + Musk

The core problem is translation: from subjective, sensory language to structured, technical knowledge. That's what makes it an interesting AI engineering problem — it's not enough to ask an LLM to "make a perfume". The model needs to be grounded in real fragrance data, guided by domain signals (what scent family does this description suggest? which notes did the user explicitly name?), and constrained by perfumery rules (volatility balance, note compatibility, percentages that sum to 100). Getting that right without hallucinated notes or unconstrained LLM output is the design challenge the architecture is built around.

---

## Full Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA PIPELINE  (one-time, ~8 min)                              │
│                                                                 │
│  dataset.csv (13,644 records)                                   │
│    │                                                            │
│    ├─ all-MiniLM-L6-v2 → encode descriptions                   │
│    │    └─ ChromaDB (cosine HNSW, 13,644 vectors)               │
│    │                                                            │
│    ├─ TF-IDF + LogReg ← train on descriptions + family labels   │
│    │    └─ scent_classifier.pkl                                 │
│    │                                                            │
│    └─ co-occurrence mining ← merge with hand-crafted corpus     │
│         └─ note_profiles.json (174 curated + ~1k dataset notes) │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  INFERENCE PIPELINE  (per request)                              │
│                                                                 │
│  User description                                               │
│    │                                                            │
│    ├─① spaCy EntityRuler ────────────── run in parallel ───┐   │
│    │    1,000+ note patterns from note_profiles.json         │   │
│    │    → detected_notes: ["Cedar", "Oud"]                  │   │
│    │                                                         │   │
│    ├─② sklearn TF-IDF + LogReg ──────────────────────────┐  │   │
│    │    trained on 13,644 fragrance descriptions          │  │   │
│    │    → predicted_family: "Woody"  confidence: 0.84    │  │   │
│    │                                                      │  │   │
│    └─③ all-MiniLM-L6-v2 → ChromaDB ────────────────────┘  │   │
│         cosine HNSW retrieval, top-5 similar fragrances    ┘   │
│    │                                                            │
│    ▼  context = {description, detected_notes,                  │
│                  predicted_family, family_confidence,          │
│                  initial_hits, pinned_notes}                   │
│    │                                                            │
│    ├─④ Orchestrator Agent  (Claude claude-sonnet-4-6)          │
│    │    Tools:                                                  │
│    │      get_note_profile(notes)                              │
│    │        → volatility · family · pairs · shared_pairings    │
│    │      search_fragrance_db(query, family?)                  │
│    │        → semantic search (only if initial_hits lack scope)│
│    │    Typical flow: 2 rounds                                 │
│    │      Round 1: profile all candidate notes in one call     │
│    │      Round 2: end_turn → recommended_notes JSON           │
│    │    Parallel: multiple tool calls in one round run         │
│    │              concurrently via ThreadPoolExecutor          │
│    │                                                            │
│    └─⑤ Composer Agent  (Claude claude-sonnet-4-6)              │
│         Single call: description + trimmed orchestrator output  │
│         → FragranceComposition JSON                            │
│              name · scent_family · top/middle/base notes       │
│              percentages · poetic_description · similar_refs   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why the NLP layer exists

The NLP layer runs on CPU before either LLM call. It converts the free-text description into structured signals that go directly into the orchestrator's context, reducing the amount of reasoning Claude needs to do — and therefore the number of tool rounds needed.

| Component | Model | Output | How it's used |
|---|---|---|---|
| **Note extractor** | spaCy `EntityRuler` | `detected_notes: ["Cedar", "Oud"]` | Tells the orchestrator which notes the user explicitly named — these are treated as high-priority candidates and passed alongside pinned notes |
| **Scent classifier** | sklearn TF-IDF + Logistic Regression | `predicted_family: "Woody"`, `confidence: 0.84` | Gives the orchestrator a prior on the scent family before it searches, reducing the chance of semantically drifted results |
| **Embedder** | `all-MiniLM-L6-v2` (384-dim) | Dense vector | Used both at ingest time (encode the database) and at query time (encode the description for ChromaDB retrieval) |

The classifier is trained once during ingestion on the 13,644 fragrance descriptions with concept tags as labels. It lives in `scent_classifier.pkl` and is loaded lazily per gunicorn worker.

---

## Knowledge base: `note_profiles.json`

174 notes hand-crafted from perfumery literature (Arctander, IFRA standards, accord theory), augmented with ~1,000 additional notes mined from the dataset via co-occurrence analysis. Each entry:

```jsonc
"Bergamot": {
  "volatility": "top",          // top / middle / base
  "family": "Fresh/Citrus",
  "descriptors": ["citrus", "green", "floral"],
  "pairs_well_with": ["Neroli", "Lavender", "Cedar", ...]
}
```

The `get_note_profile` tool serves this data to the orchestrator at runtime. When ≥2 notes are requested it also returns `shared_pairings` — the intersection of all their pairing sets — in the same call, removing the need for a separate round-trip that was previously a distinct `get_note_pairings` tool.

---

## Agentic design decisions

**Two agents, not one.** The pipeline splits into grounding (orchestrator) and formulation (composer). The orchestrator has no idea what a percentage is; the composer never touches the database. Each agent's prompt is small, focused, and independently improvable.

**Tools removed from the orchestrator:**
- `validate_composition` — the orchestrator recommends notes, it doesn't build a formula. Giving it a validation tool caused Claude to waste a round drafting a composition just to check it, before the composer rebuilt it from scratch anyway.
- `get_note_pairings` — merged into `get_note_profile` via `shared_pairings`. What was a 3-round flow (profile → pair → end_turn) is now typically 2 rounds.

**Three-layer prompt caching** (Anthropic prompt cache, 90% discount on hits):

```
[system prompt]    ← cached cross-request (same text every call)
[tools block]      ← cached cross-request (same schema every call)
[user message]     ← cached within-request (identical across all rounds
                      of the same orchestrator loop; rounds 2+ pay only
                      for the new accumulated tool results)
```

**Parallel execution at two levels:**
1. NLP preprocessing and ChromaDB search run concurrently before the first LLM call
2. Multiple tool calls returned in a single orchestrator round are dispatched concurrently via `ThreadPoolExecutor`

Result: ~65–70% fewer billed input tokens vs. the naive implementation; typical request completes in 2 orchestrator rounds instead of 3–5.

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Anthropic Claude claude-sonnet-4-6 |
| Vector store | ChromaDB (embedded, cosine HNSW) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| NER | spaCy `EntityRuler` — rule-based, zero training data |
| Scent classifier | scikit-learn TF-IDF + Logistic Regression |
| Backend | Python 3.11 · Flask · gunicorn (4 workers) |
| Frontend | React 18 · TypeScript 5 |
| Deployment | Single Docker container — Flask serves both API and React build |

---

## API

All endpoints under `/api/v1/`.

| Method | Path | Rate limit | Purpose |
|---|---|---|---|
| POST | `/generate` | 5 / hour | Generate fragrance from description + optional pinned notes |
| POST | `/feedback` | 20 / hour | Submit 1–5 star rating with optional comment |
| GET | `/notes` | — | All available fragrance note names |
| GET | `/metrics` | 60 / min | Aggregated feedback statistics |
| POST | `/share` | 10 / hour | Save a composition, get a shareable token |
| GET | `/share/<token>` | 120 / hour | Retrieve a shared composition |
| GET | `/health` | — | Liveness check |

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

## Local development

**Prerequisites:** Python 3.11+, Node 18+, `ANTHROPIC_API_KEY`

```bash
# Backend
cd backend
pip install -r requirements.txt
python scripts/ingest_dataset.py   # one-time: builds ChromaDB + trains classifier (~8 min)
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

## Deployment (Hugging Face Spaces + GitHub Pages)

```bash
docker build -f backend/Dockerfile -t sniff-ai .
```

1. Create a Hugging Face Space (Docker SDK)
2. Secrets: `ANTHROPIC_API_KEY`, `CORS_ORIGINS=https://ksek87.github.io`, `CHROMA_PERSIST_DIR=/data/chroma_db`
3. `docker.yml` builds and pushes `ghcr.io/ksek87/sniff_ai/backend:latest` on every push to `main`
4. First boot auto-ingests ChromaDB and trains the classifier (~8 min), then serves on port 7860

Frontend deploys to GitHub Pages via `pages.yml`.

---

## Testing

```bash
# Backend — all external calls mocked, no API key needed
python -m pytest backend/tests/ -q

# Frontend type check
cd frontend && npx tsc --noEmit
```
