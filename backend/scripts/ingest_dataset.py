"""
One-time ingestion script: loads dataset.csv into ChromaDB.
Run from the backend/ directory:
    python scripts/ingest_dataset.py
"""
import ast
import json
import os
import sys

import pandas as pd
import chromadb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.nlp.embedder import Embedder

_DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "../../data_collection/dataset.csv"
)
_CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "../data/note_profiles.json")
_COLLECTION_NAME = "fragrances"
_BATCH_SIZE = 256


def _safe_parse(val) -> list:
    if not isinstance(val, str):
        return []
    try:
        result = ast.literal_eval(val)
        return result if isinstance(result, list) else []
    except Exception:
        return []


def _build_doc(row) -> str:
    parts = [str(row.get("Description", "")).strip()]
    notes = _safe_parse(row.get("Notes", "[]"))
    concepts = _safe_parse(row.get("Concepts", "[]"))
    if notes:
        parts.append("Notes: " + ", ".join(str(n) for n in notes))
    if concepts:
        parts.append("Concepts: " + ", ".join(str(c) for c in concepts))
    return " ".join(parts)


def ingest():
    print(f"Loading dataset from {_DATASET_PATH}")
    df = pd.read_csv(_DATASET_PATH)
    print(f"  {len(df)} rows loaded")

    df = df.dropna(subset=["Description"])
    df["Description"] = df["Description"].astype(str)

    embedder = Embedder()
    client = chromadb.PersistentClient(path=_CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    docs = [_build_doc(row) for _, row in df.iterrows()]
    ids = [str(i) for i in range(len(df))]
    metadatas = []
    for _, row in df.iterrows():
        notes = _safe_parse(row.get("Notes", "[]"))
        concepts = _safe_parse(row.get("Concepts", "[]"))
        metadatas.append(
            {
                "brand": str(row.get("Brand", "")),
                "name": str(row.get("Name", "")),
                "description": str(row.get("Description", ""))[:500],
                "notes_list": json.dumps(notes),
                "concepts_list": json.dumps(concepts),
            }
        )

    print(f"Encoding {len(docs)} documents in batches of {_BATCH_SIZE}…")
    embeddings = embedder.encode_batch(docs, batch_size=_BATCH_SIZE)

    print("Storing in ChromaDB…")
    for start in range(0, len(docs), _BATCH_SIZE):
        end = start + _BATCH_SIZE
        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings[start:end].tolist(),
            documents=docs[start:end],
            metadatas=metadatas[start:end],
        )
    print(f"  Stored {collection.count()} documents in {_CHROMA_DIR}")

    _generate_note_profiles(df)


def _generate_note_profiles(df: pd.DataFrame):
    from collections import defaultdict, Counter

    note_cooccurrence: dict[str, Counter] = defaultdict(Counter)
    note_family_map: dict[str, Counter] = defaultdict(Counter)

    for _, row in df.iterrows():
        notes = _safe_parse(row.get("Notes", "[]"))
        concepts = _safe_parse(row.get("Concepts", "[]"))
        for note in notes:
            for other in notes:
                if other != note:
                    note_cooccurrence[note][other] += 1
            for concept in concepts:
                note_family_map[note][concept] += 1

    # Rough volatility heuristic from known top/middle/base note names
    _TOP_HINTS = {"Bergamot", "Lemon", "Orange", "Grapefruit", "Petitgrain", "Lime",
                  "Mandarin", "Neroli", "Aldehydes", "Green", "Pink Pepper"}
    _BASE_HINTS = {"Musk", "Amber", "Sandalwood", "Cedarwood", "Vanilla", "Oakmoss",
                   "Benzoin", "Labdanum", "Oud", "Vetiver", "Patchouli", "Civet",
                   "Tonka Bean", "Castoreum"}

    profiles: dict[str, dict] = {}
    for note in note_cooccurrence:
        if note in _TOP_HINTS:
            volatility = "top"
        elif note in _BASE_HINTS:
            volatility = "base"
        else:
            volatility = "middle"

        family = note_family_map[note].most_common(1)[0][0] if note_family_map[note] else "unknown"
        pairs = [n for n, _ in note_cooccurrence[note].most_common(5)]

        profiles[note] = {
            "volatility": volatility,
            "family": family,
            "pairs_well_with": pairs,
        }

    os.makedirs(os.path.dirname(_PROFILES_PATH), exist_ok=True)
    with open(_PROFILES_PATH, "w") as f:
        json.dump(profiles, f, indent=2)
    print(f"  Note profiles written to {_PROFILES_PATH} ({len(profiles)} notes)")


if __name__ == "__main__":
    ingest()
