"""
One-time ingestion script: loads dataset.csv into ChromaDB.
Run from the backend/ directory:
    python scripts/ingest_dataset.py
"""
import ast
import json
import os
import re
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
_BATCH_SIZE = int(os.environ.get("INGEST_BATCH_SIZE", 512))


_SCRAPER_ARTIFACT = re.compile(r"\.?\s*Discover more details!", re.IGNORECASE)


def _safe_parse(val) -> list:
    if not isinstance(val, str):
        return []
    try:
        result = ast.literal_eval(val)
        if not isinstance(result, list):
            return []
        return [_SCRAPER_ARTIFACT.sub("", str(item)).strip() for item in result]
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
    """
    Merge hand-crafted note_profiles.json with dataset-derived co-occurrence data.

    Hand-crafted entries are authoritative: their volatility, family, and
    descriptors are preserved unchanged.  The dataset contributes two things:
      1. Additional notes not in the hand-crafted corpus (long-tail coverage).
      2. Extended pairing suggestions for all notes, appended after the
         hand-crafted pairs so curated choices rank first.
    """
    from collections import defaultdict, Counter

    # Load the hand-crafted base corpus if it exists.
    base: dict[str, dict] = {}
    if os.path.exists(_PROFILES_PATH):
        with open(_PROFILES_PATH) as f:
            base = json.load(f)
        print(f"  Loaded {len(base)} hand-crafted note profiles as base")

    # Build co-occurrence and concept maps from the dataset.
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

    # Volatility heuristic for dataset-only notes (hand-crafted entries override).
    _TOP_HINTS = {
        "Bergamot", "Lemon", "Orange", "Grapefruit", "Petitgrain", "Lime",
        "Mandarin", "Neroli", "Aldehydes", "Pink Pepper", "Yuzu", "Blood Orange",
        "Tangerine", "Ginger", "Cardamom", "Coriander", "Black Pepper", "Basil",
        "Mint", "Peppermint", "Spearmint", "Rosemary", "Eucalyptus", "Juniper Berry",
    }
    _BASE_HINTS = {
        "Musk", "Amber", "Sandalwood", "Cedarwood", "Vanilla", "Oakmoss",
        "Benzoin", "Labdanum", "Oud", "Vetiver", "Patchouli", "Civet",
        "Tonka Bean", "Castoreum", "Atlas Cedar", "Ambroxan", "Iso E Super",
        "Frankincense", "Myrrh", "Styrax", "Tobacco", "Leather", "Smoke",
    }

    # Canonical families and aliases found in dataset concept tags.
    _CANONICAL = {
        "Floral", "Oriental", "Woody", "Fresh/Citrus",
        "Fougère", "Chypre", "Gourmand", "Aquatic/Marine", "Earthy/Mossy",
    }
    _CONCEPT_MAP = {
        "Citrus": "Fresh/Citrus", "Fresh": "Fresh/Citrus", "Green": "Fresh/Citrus",
        "Aromatic": "Fougère", "Fern": "Fougère",
        "Amber": "Oriental", "Spicy": "Oriental", "Resinous": "Oriental",
        "Mossy": "Earthy/Mossy", "Earthy": "Earthy/Mossy", "Musky": "Earthy/Mossy",
        "Marine": "Aquatic/Marine", "Aquatic": "Aquatic/Marine", "Ozonic": "Aquatic/Marine",
        "Sweet": "Gourmand", "Powdery": "Floral",
    }

    merged: dict[str, dict] = dict(base)

    for note, cooc in note_cooccurrence.items():
        dataset_pairs = [n for n, _ in cooc.most_common(10)]

        if note in merged:
            # Extend hand-crafted pairs with high-frequency dataset pairs not already listed.
            existing = merged[note]["pairs_well_with"]
            existing_set = set(existing)
            extra = [p for p in dataset_pairs if p not in existing_set][:5]
            merged[note]["pairs_well_with"] = existing + extra
        else:
            # New note from the dataset — derive properties from heuristics.
            if note in _TOP_HINTS:
                volatility = "top"
            elif note in _BASE_HINTS:
                volatility = "base"
            else:
                volatility = "middle"

            # Map the most common dataset concept to a canonical family.
            family = "unknown"
            for candidate, _ in note_family_map[note].most_common():
                if candidate in _CANONICAL:
                    family = candidate
                    break
                if candidate in _CONCEPT_MAP:
                    family = _CONCEPT_MAP[candidate]
                    break

            merged[note] = {
                "volatility": volatility,
                "family": family,
                "pairs_well_with": dataset_pairs[:8],
            }

    os.makedirs(os.path.dirname(_PROFILES_PATH), exist_ok=True)
    with open(_PROFILES_PATH, "w") as f:
        json.dump(merged, f, indent=2, sort_keys=True)
    new_count = len(merged) - len(base)
    print(f"  Note profiles: {len(base)} hand-crafted + {new_count} from dataset = {len(merged)} total")


if __name__ == "__main__":
    ingest()
