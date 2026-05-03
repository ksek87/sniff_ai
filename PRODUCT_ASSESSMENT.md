# Sniff AI — Product Assessment

## What It Is

Sniff AI translates poetic text descriptions ("autumn forest after rain") into professional fragrance compositions with named top/middle/base notes, percentages, a custom name, and real-world reference fragrances. Output is a structured digital formula, not a product recommendation.

---

## Market Position

**The gap is real.** No consumer-accessible tool currently converts natural language into a structured fragrance formula.

| | Pro tools (Givaudan Carto, Symrise Philyra) | Recommendation apps (Scentbird, Jo Malone AI) | Sniff AI |
|---|---|---|---|
| Poetic text input | No | Partially (maps to catalog) | **Yes** |
| Outputs a novel composition | Yes — B2B only, closed | No | **Yes** |
| Consumer/indie accessible | No | Yes | **Yes** |
| No physical fulfillment required | — | Yes | **Yes** |

The closest competitor — **Osmo "Generation"** ($60M+ raised, Google Ventures) — requires physical bottles and targets brands only. **ScentGenie** maps text to existing products. Sniff AI is positioned in genuinely unclaimed territory: digital-native, composition-first, accessible to individuals.

**Market context:** $59B global fragrance market (2025), growing at 5.5% CAGR. Personalized perfume sub-market projected at $1.5B by 2028. AI fragrance startups raised $130M+.

---

## Target Users (Prioritized)

1. **Indie/hobbyist perfumers** — Fragrantica has 15M monthly users; Basenotes is vocal; no tools help translate creative briefs into starting formulas. Highest engagement potential.
2. **Fragrance enthusiasts / gifters** — Want imagination-to-scent; emotional resonance drives purchase intent. Largest audience.
3. **Small fragrance brands / indie founders** — Need composition briefs for contract manufacturers; can't afford Givaudan/Symrise contracts. High willingness to pay.
4. **Creative professionals** — Writers, brand strategists, event designers commissioning atmospheric scents. Niche but premium.

---

## Current Product State

### What Works End-to-End
- NLP preprocessing: spaCy EntityRuler note extraction + sklearn scent family classifier + sentence-transformers embeddings (~50ms)
- Dual-agent Claude pipeline: Orchestrator (tool-use loop, ChromaDB retrieval) → Composer (structured JSON output)
- Full backend API: 7 endpoints, rate-limited, tested (95 tests)
- React frontend: description input → fragrance card with notes pyramid, reference fragrances, confidence score
- Single-container Docker deployment targeting Hugging Face Spaces

### What's Built but Not Exposed in UI
| Feature | Backend | Frontend |
|---|---|---|
| Pinned notes (hard note constraints) | ✅ | ❌ NoteSelector not built |
| Feedback (star rating + comment) | ✅ | ❌ FeedbackWidget not built |
| Fragrance search | ✅ | ❌ SearchPanel not built |
| Metrics dashboard | ✅ | ❌ MetricsDashboard not built |

### Data Gaps
- **ChromaDB not seeded** — `ingest_dataset.py` exists but hasn't run in production; search returns empty until ingestion completes (~8 min first boot on HF Spaces)
- **note_profiles.json absent** — generated at runtime from dataset.csv if missing
- **No live deployment** — HF Space not yet created; GitHub Pages frontend calls localhost

---

## Roadmap Assessment

**v1 (shipped):** Core generation pipeline, full API, basic UI, Docker deployment ready.
**v2 (next):** NoteSelector + FeedbackWidget — unlocks personalization and the feedback loop.
**v3 (later):** SearchPanel + MetricsDashboard — discovery and analytics.

**v2 is the critical unlock.** The feedback loop (ratings → classifier retraining) is the mechanism that improves output quality over time. Without `FeedbackWidget`, there's no data collection and no improvement cycle. `NoteSelector` is the key personalization differentiator that justifies returning use.

---

## Strategic Priorities

### Immediate (before promotion)
1. **Deploy to HF Spaces** — create the Space, add `ANTHROPIC_API_KEY` secret, point `BACKEND_URL` GitHub secret at it, re-run the frontend GitHub Pages deploy
2. **Seed ChromaDB** — run ingestion once; without it, similar fragrances are empty and output quality degrades significantly

### Short-term (v2)
3. **Build FeedbackWidget** — star rating + comment, POST to `/api/v1/feedback`; starts the improvement flywheel
4. **Build NoteSelector** — multi-select note chips from `/api/v1/notes`; this is the feature that distinguishes sniff AI from a demo

### Medium-term
5. **Prompt caching** — both Claude agents re-send the full system prompt on every request; adding `cache_control` cuts API costs ~90% on cache hits
6. **Rate limit storage** — current Flask-Limiter uses in-memory storage; won't work across multiple gunicorn workers. Add Redis or use a single-worker config on HF Spaces.

---

## Key Differentiators to Emphasize

- **"A composition, not a recommendation"** — most competitors surface existing products; sniff AI creates a new formula
- **Language as interface** — no quiz, no sliders; poetic feeling is the UX primitive
- **Indie perfumer enablement** — the B2B giants serve only large brands; this community is vocal, underserved, and actively seeking tools
- **Grounded in 13,644 real fragrances** — output is anchored in real-world references, not hallucinated chemistry
