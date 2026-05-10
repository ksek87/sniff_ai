# Sniff AI

**[Try it live →](https://ksek87.github.io/sniff_ai/)**

---

## The idea

Fragrance is one of the most emotionally vivid senses, but describing a scent you want is almost impossible without a perfumer's vocabulary. People reach for metaphors — *"a walk through a pine forest after rain"*, *"warm, like old books and amber"*, *"the sea at five in the morning"* — but those descriptions live in a completely different language from the ingredient lists, volatility classes, and accord structures that actually make a perfume.

Sniff AI bridges that gap. You describe a feeling or a memory in plain language. It produces a professional fragrance composition — a notes pyramid with percentages, a name, a poetic description written back in your register, and real-world references from a database of 13,644 fragrances. No perfumery knowledge required.

> *"A thunderstorm over a pine forest at dusk"* → **Twilight Pine Accord** — Woody Aromatic · Bergamot + Petitgrain · Pine Needle + Clary Sage · Cedarwood + Musk

The core problem is translation: from subjective, sensory language to structured, technical knowledge. That's what makes it an interesting AI engineering problem — it's not enough to ask an LLM to "make a perfume". The model needs to be grounded in real fragrance data, guided by domain signals (what scent family does this description suggest? which notes did the user explicitly name?), and constrained by perfumery rules (volatility balance, note compatibility, percentages summing to 100). Getting that right without hallucinated notes or unconstrained output is the design challenge the architecture is built around.

→ **[Full architecture and engineering decisions](ARCHITECTURE.md)**

---

## Features

- **Natural language input** — describe a mood, memory, or scene
- **Notes pyramid** — top / heart / base breakdown with percentages summing to 100%
- **Pinned notes** — constrain the composition to specific ingredients
- **Reference fragrances** — real-world matches from 13,644 records
- **Share** — save any composition to a permanent link
- **Feedback** — 1–5 star rating with optional comment

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Anthropic Claude claude-sonnet-4-6 |
| Vector store | ChromaDB (cosine HNSW) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| NER | spaCy `EntityRuler` |
| Scent classifier | scikit-learn TF-IDF + Logistic Regression |
| Backend | Python 3.11 · Flask · gunicorn |
| Frontend | React 18 · TypeScript 5 |
| Deployment | Docker · Hugging Face Spaces + GitHub Pages |

---

## API

All endpoints under `/api/v1/`.

| Method | Path | Rate limit | Purpose |
|---|---|---|---|
| POST | `/generate` | 5 / hour | Generate fragrance from description + optional pinned notes |
| POST | `/feedback` | 20 / hour | Submit star rating |
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

# Frontend (separate terminal)
cd frontend
npm ci --legacy-peer-deps
REACT_APP_API_URL=http://localhost:5000 npm start
```

**Docker Compose (recommended)**

```bash
cp .env.example .env   # add ANTHROPIC_API_KEY
docker compose up --build
```

---

## Testing

```bash
# Backend — all external calls mocked, no API key needed
python -m pytest backend/tests/ -q

# Frontend type check
cd frontend && npx tsc --noEmit
```

---

## Deployment

Backend runs on Hugging Face Spaces (Docker, port 7860). Frontend on GitHub Pages. Both deploy automatically on push to `main` via GitHub Actions. See [ARCHITECTURE.md](ARCHITECTURE.md) for deployment details.
