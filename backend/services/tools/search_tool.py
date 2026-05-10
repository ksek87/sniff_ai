from __future__ import annotations
import os

import chromadb
from services.nlp.embedder import Embedder

_CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", "/data/chroma_db")
_COLLECTION_NAME = "fragrances"

_client: chromadb.PersistentClient | None = None
_collection = None
_embedder = Embedder()


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=_CHROMA_DIR)
        _collection = _client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def search_fragrance_db(query: str, top_k: int = 10, family: str | None = None) -> list[dict]:
    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_vector = _embedder.encode(query)

    # Fetch extra results when filtering so we still return up to top_k after the filter
    fetch_k = min(top_k * 3 if family else top_k, collection.count())

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=fetch_k,
        include=["metadatas", "distances"],
    )

    output: list[dict] = []
    for meta, dist in zip(
        results["metadatas"][0], results["distances"][0]
    ):
        if family and family.lower() not in (meta.get("concepts_list", "") or "").lower():
            continue
        output.append(
            {
                "brand": meta.get("brand", ""),
                "name": meta.get("name", ""),
                "notes": meta.get("notes_list", ""),
                "concepts": meta.get("concepts_list", ""),
                "description": meta.get("description", ""),
                "similarity_score": round(1 - dist, 4),
            }
        )
        if len(output) >= top_k:
            break
    return output
