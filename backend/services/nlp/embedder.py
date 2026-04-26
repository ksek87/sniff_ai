from __future__ import annotations
from sentence_transformers import SentenceTransformer
import numpy as np

_MODEL_NAME = "all-MiniLM-L6-v2"


class Embedder:
    _instance: "Embedder | None" = None

    def __new__(cls):
        # Singleton so the model is only loaded once at startup
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = SentenceTransformer(_MODEL_NAME)
        return cls._instance

    def encode(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def encode_batch(self, texts: list[str], batch_size: int = 256) -> np.ndarray:
        return self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
