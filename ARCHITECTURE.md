# Architecture

A deep dive into how Sniff AI works — useful context for interviews or contributors.

---

## Full pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA PIPELINE  (one-time, ~8 min)                              │
│                                                                 │
│  dataset.csv (13,644 fragrance records)                         │
│    │                                                            │
│    ├─ all-MiniLM-L6-v2 → encode all descriptions               │
│    │    └─ ChromaDB  (cosine HNSW, 13,644 vectors on disk)      │
│    │                                                            │
│    ├─ TF-IDF + LogReg ← train on descriptions × family labels   │
│    │    └─ scent_classifier.pkl                                 │
│    │                                                            │
│    └─ co-occurrence mining ← merge with hand-crafted corpus     │
│         └─ note_profiles.json  (174 curated + ~1k dataset notes)│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  INFERENCE PIPELINE  (per request)                              │
│                                                                 │
│  User description                                               │
│    │                                                            │
│    ├─① spaCy EntityRuler ──────────────── run in parallel ──┐  │
│    │    ~1,000 note patterns from note_profiles.json          │  │
│    │    → detected_notes: ["Cedar", "Oud"]                   │  │
│    │                                                          │  │
│    ├─② sklearn TF-IDF + Logistic Regression ───────────────┐ │  │
│    │    trained on 13,644 fragrance descriptions            │ │  │
│    │    → predicted_family: "Woody"  confidence: 0.84      │ │  │
│    │                                                        │ │  │
│    └─③ all-MiniLM-L6-v2 + ChromaDB (cosine HNSW) ────────┘ ┘  │
│         → initial_hits: top-5 similar fragrances               │
│    │                                                            │
│    ▼  context = { description, detected_notes,                 │
│                   predicted_family, family_confidence,         │
│                   initial_hits, pinned_notes }                 │
│    │                                                            │
│    ├─④ Orchestrator Agent  (Claude claude-sonnet-4-6)          │
│    │    Tools:                                                  │
│    │      get_note_profile(notes)                              │
│    │        → volatility · family · pairs · shared_pairings    │
│    │      search_fragrance_db(query, family?)                  │
│    │        → semantic DB search (only if initial_hits          │
│    │          lack sufficient scope)                           │
│    │    Typical flow: 2 rounds                                 │
│    │      Round 1: profile all candidate notes in one call     │
│    │      Round 2: end_turn → recommended_notes JSON           │
│    │    Multiple tool calls per round: ThreadPoolExecutor      │
│    │                                                            │
│    └─⑤ Composer Agent  (Claude claude-sonnet-4-6)              │
│         Single call, trimmed orchestrator context              │
│         → FragranceComposition JSON                            │
│              name · scent_family · notes + percentages         │
│              poetic_description · similar_fragrances           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why the NLP layer exists

The NLP layer runs entirely on CPU before either LLM call. It converts free-text input into structured signals that go directly into the orchestrator's context — reducing the amount of reasoning Claude needs to do and therefore the number of tool rounds needed.

| Component | Model | Output | How it's used |
|---|---|---|---|
| **Note extractor** | spaCy `EntityRuler` | `detected_notes: ["Cedar", "Oud"]` | Tells the orchestrator which notes the user explicitly named. Treated as high-priority candidates alongside pinned notes. |
| **Scent classifier** | sklearn TF-IDF + Logistic Regression | `predicted_family: "Woody"`, `confidence: 0.84` | Gives the orchestrator a prior on scent family before it searches, reducing semantically drifted results. |
| **Embedder** | `all-MiniLM-L6-v2` (384-dim) | Dense vector | Encodes the database at ingest time and encodes each query at runtime for ChromaDB similarity retrieval. |

Without this layer, Claude would need extra tool-use rounds to derive the same information from scratch — at LLM token rates. The classifier alone saves roughly one orchestrator round per request by pre-answering "what family does this description suggest?".

---

## Knowledge base: `note_profiles.json`

174 notes hand-crafted from perfumery literature (Arctander, IFRA standards, accord theory), augmented with ~1,000 notes mined from the dataset via co-occurrence analysis. Each entry:

```jsonc
"Bergamot": {
  "volatility": "top",
  "family": "Fresh/Citrus",
  "descriptors": ["citrus", "green", "floral", "bright"],
  "pairs_well_with": ["Neroli", "Lavender", "Cedar", "Vetiver", ...]
}
```

The hand-crafted entries are authoritative — their `volatility`, `family`, and `descriptors` are preserved when the dataset augmentation runs. Dataset-mined notes get heuristic volatility and concept-mapped family.

At runtime the `get_note_profile` orchestrator tool serves this data. When ≥2 notes are requested the response also includes `shared_pairings` — the intersection of all their pairing sets — in the same call. This collapsed what was previously a separate `get_note_pairings` tool into a single round-trip.

---

## Agentic design decisions

### Two agents, not one

The pipeline deliberately separates two concerns:

**Orchestrator** — a *grounding* agent. It has no concept of a final formula. Its only job is to retrieve relevant fragrance knowledge and recommend which notes belong in each tier. It works entirely with tools backed by real data, which prevents note hallucination.

**Composer** — a *formulation* agent. It receives the orchestrator's trimmed output (`{recommended_notes, refs, reasoning}`) and produces the final structured JSON: name, percentages, poetic description, confidence score. It never touches the database directly.

Splitting them keeps each prompt small and focused. It also means quality problems are locatable: if the notes are wrong, the issue is in the orchestrator; if the formula is wrong, it's in the composer.

### Tools removed from the orchestrator

`validate_composition` — the orchestrator recommends notes, not formulas. Giving it a validation tool caused Claude to waste a round drafting a composition purely to check it, before the composer rebuilt it from scratch. Server-side normalisation in `_normalise_percentages` handles percentage correction correctly.

`get_note_pairings` — merged into `get_note_profile` via `shared_pairings`. The previous 3-round pattern (profile → pairings → end_turn) is now typically 2 rounds.

`_MAX_TOOL_ROUNDS` reduced from 5 to 3: sufficient headroom for edge cases, prevents runaway loops.

### Token optimisation

Three cache breakpoints per request (Anthropic prompt caching — 90% discount on hits, ~5-min TTL):

```
[system prompt]    ← breakpoint 1: same text every call, cached cross-request
[tools block]      ← breakpoint 2: same schema every call, cached cross-request
[user message]     ← breakpoint 3: within-request — rounds 2+ pay only for
                      the newly accumulated tool results, not the full context re-send
```

Additional compression:
- `initial_hits` formatted as compact text (3 refs, ~80 tokens) vs. `json.dumps(indent=2)` (~350 tokens)
- Tool results stripped of non-essential fields before appending to conversation history
- Composer receives trimmed orchestrator output (~200 tokens vs. ~600 with full fragrance data)
- `max_tokens` right-sized: orchestrator 1024, composer 1500

**Net result: ~65–70% fewer billed input tokens vs. the naive implementation.**

---

## Performance engineering

The production failure mode was "first request always slow or times out; second request works". Three root causes:

| Problem | Root cause | Fix |
|---|---|---|
| First query 10–30 s | ChromaDB HNSWLIB index loads lazily on first `collection.query()` — not on client/collection creation | `gunicorn post_worker_init` calls `search_fragrance_db("warmup")` after each worker forks |
| First NLP inference slow | spaCy, sklearn, and sentence-transformers models load on first use | `post_worker_init` also calls `preprocess("warmup")` — lazy init with double-checked locking ensures each model loads exactly once per worker |
| Connection overhead | New Anthropic TCP/TLS connection per request | Singleton `anthropic.Anthropic` client reused across requests |

NLP singletons (`NoteExtractor`, `ScentClassifier`, `Embedder`) use double-checked locking in `services/nlp/__init__.py` — thread-safe lazy init without a lock on the hot path.

```python
def _get_note_extractor() -> NoteExtractor:
    global _note_extractor
    if _note_extractor is None:          # fast path, no lock
        with _lock:
            if _note_extractor is None:  # re-check under lock
                _note_extractor = NoteExtractor()
    return _note_extractor
```

---

## Deployment

| Component | Platform | Notes |
|---|---|---|
| Backend | Hugging Face Spaces (Docker, port 7860) | `start.sh` auto-ingests ChromaDB on first boot |
| Frontend | GitHub Pages | `REACT_APP_API_URL` points at the HF Space |
| CI | GitHub Actions | `docker.yml` builds + pushes backend image on push to `main`; `pages.yml` builds + deploys frontend |

`CORS_ORIGINS=https://ksek87.github.io` must be set in the HF Space secrets or the browser will block API calls.

gunicorn is configured via `backend/gunicorn_config.py` (4 workers, 300 s timeout, `post_worker_init` warmup).
