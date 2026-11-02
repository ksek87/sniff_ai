# Sniff AI — Product Assessment

*Last updated: November 2026*

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

### Shipped
- **Generation pipeline** — NLP preprocessing (spaCy note extraction, scent family classifier, sentence-transformer embeddings) → Claude orchestrator with ChromaDB retrieval → Claude composer producing structured JSON. Prompt caching on both agents.
- **Pinned notes** — `NoteSelector` lets users lock up to 10 notes into the composition.
- **Feedback** — `FeedbackWidget` (1–5 stars + comment) persisted to SQLite.
- **Metrics** — `MetricsDashboard` shows rating count, average, and distribution.
- **Sharing** — permanent share links, native share sheet via the Web Share API on mobile.
- **Observability** — Langfuse traces for every generation (tool calls, tokens, cost, latency).
- **Deployment** — backend on Hugging Face Spaces (Docker), frontend on GitHub Pages, CI restarts the Space on image push. ~136 backend tests.

### Deliberately removed
- **Public fragrance database search** (`SearchPanel`, `/search`, `/families`) — removed to avoid IP concerns over exposing the scraped dataset. ChromaDB is still used internally by the orchestrator for grounding.

---

## Backlog

### Fixes
1. **Rate limiting is ineffective** — Flask-Limiter uses `memory://` storage while gunicorn runs 4 workers, so each worker counts separately (~4× the intended limit). There is also no `ProxyFix`, so behind the HF proxy all users may share one rate-limit bucket. Fix: single worker + threads with `ProxyFix`, or Redis-backed storage.
2. **Default model is outdated** — `_client.py` defaults to `claude-sonnet-4-6`; move to a current model.

### Features
3. **Additional input customization** — let users choose intensity, season, or occasion alongside the description. Fits naturally beside pinned notes. *(Carried over from the original README's Future Enhancements.)*
4. **Close the feedback loop** — ratings are stored and displayed but never used. Options: retrain the scent classifier on highly-rated outputs, or feed top-rated compositions back to the composer as few-shot examples.
5. **Improved fragrance matching** — refine similarity scoring for the reference fragrances shown with each composition. *(Carried over.)*
6. **User accounts and saved fragrances** — let users keep a library of compositions; today the only persistence is anonymous share links. Largest item — requires auth and per-user storage. *(Carried over.)*
7. **Automated data scraping for new releases** (issue #22) — on hold; conflicts with the same IP concerns that led to removing public search. Needs a decision on data sourcing before any work.

---

## Key Differentiators to Emphasize

- **"A composition, not a recommendation"** — most competitors surface existing products; Sniff AI creates a new formula
- **Language as interface** — no quiz, no sliders; poetic feeling is the UX primitive
- **Indie perfumer enablement** — the B2B giants serve only large brands; this community is vocal, underserved, and actively seeking tools
- **Grounded in 13,644 real fragrances** — output is anchored in real-world references, not hallucinated chemistry
