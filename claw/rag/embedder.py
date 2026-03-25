from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@dataclass
class Embedder:
    _model: object = field(default=None, repr=False)

    def _load_model(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(MODEL_NAME)
        logger.info("Loaded embedding model: %s", MODEL_NAME)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        self._load_model()
        if not texts:
            return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

        embeddings = self._model.encode(
            list(texts),
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        result = self.embed([text])
        return result[0]

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIM
