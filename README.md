# Sniff AI — AI Fragrance Composer

**Generate professional perfume compositions from natural language descriptions.**

[![Live Demo](https://img.shields.io/badge/Try%20it%20live-→-brightgreen?style=for-the-badge)](https://ksek87.github.io/sniff_ai/)
[![Backend](https://img.shields.io/badge/Backend-Hugging%20Face%20Spaces-yellow?style=for-the-badge)](https://huggingface.co/spaces/ksek87/sniff_ai)
[![Frontend](https://img.shields.io/badge/Frontend-GitHub%20Pages-blue?style=for-the-badge)](https://ksek87.github.io/sniff_ai/)

---

Sniff AI translates the way people *actually* talk about scent — moods, memories, metaphors — into structured, perfumer-grade fragrance compositions. Describe a feeling in plain language; get back a full notes pyramid, a name, a poetic description, and real-world fragrance references.

> *"A thunderstorm over a pine forest at dusk"* → **Twilight Pine Accord** — Woody Aromatic · Bergamot + Petitgrain · Pine Needle + Clary Sage · Cedarwood + Musk

The hard problem is **translation**: subjective sensory language → structured technical knowledge. The architecture grounds the model in a database of 13,644 real fragrances, uses domain signals (scent family classification, named ingredient recognition) to guide generation, and enforces perfumery constraints (volatility balance, percentages summing to 100). The result is compositions that feel intentional rather than hallucinated.

→ **[Full architecture and engineering decisions](ARCHITECTURE.md)**

---

## Features

| Feature | Description |
|---|---|
| Natural language input | Describe a mood, memory, or scene — no perfumery vocabulary needed |
| Notes pyramid | Top / heart / base breakdown with percentages summing to 100% |
| Pinned notes | Lock specific ingredients into the composition |
| Reference fragrances | Real-world matches from 13,644 indexed records |
| Shareable compositions | Save any result to a permanent link |
| Feedback | 1–5 star rating with optional comment |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Anthropic Claude API |
| Vector store | ChromaDB (cosine HNSW) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| NER | spaCy `EntityRuler` |
| Scent classifier | scikit-learn TF-IDF + Logistic Regression |
| Backend | Python 3.11 · Flask · gunicorn |
| Frontend | React 18 · TypeScript 5 |
| Deployment | Docker · Hugging Face Spaces + GitHub Pages |

---

## API Reference

Base path: `/api/v1/`

| Method | Path | Rate limit | Purpose |
|---|---|---|---|
| `POST` | `/generate` | 5 / hour | Generate fragrance from description + optional pinned notes |
| `POST` | `/feedback` | 20 / hour | Submit star rating |
| `GET` | `/notes` | — | All available fragrance note names |
| `GET` | `/metrics` | 60 / min | Aggregated feedback statistics |
| `POST` | `/share` | 10 / hour | Save a composition, get a shareable token |
| `GET` | `/share/<token>` | 120 / hour | Retrieve a shared composition |
| `GET` | `/health` | — | Liveness check |

**Example — generate a fragrance:**

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

**Option 1 — Docker Compose (recommended)**

```bash
cp .env.example .env   # add ANTHROPIC_API_KEY
docker compose up --build
```

**Option 2 — Manual**

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

Backend deploys to **Hugging Face Spaces** (Docker, port 7860); frontend to **GitHub Pages**. Both deploy automatically on push to `main` via GitHub Actions.

The HF Space must have `CORS_ORIGINS=https://ksek87.github.io` set, and GitHub Pages source must be configured to **GitHub Actions** (not "Deploy from branch").

See [ARCHITECTURE.md](ARCHITECTURE.md) for full deployment details.
