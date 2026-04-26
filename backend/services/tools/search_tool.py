from __future__ import annotations
import os

import chromadb
from chromadb.config import Settings

from services.nlp.embedder import Embedder

_CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
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


def search_fragrance_db(
    query: str,
    scent_family: str | None = None,
    top_k: int = 10,
) -> list[dict]:
    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_vector = _embedder.encode(query)

    where: dict | None = None
    if scent_family:
        where = {"scent_family": {"$eq": scent_family}}

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        where=where,
        include=["metadatas", "distances"],
    )

    output: list[dict] = []
    for meta, dist in zip(
        results["metadatas"][0], results["distances"][0]
    ):
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
    return output
