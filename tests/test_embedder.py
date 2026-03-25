import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from claw.rag.embedder import Embedder, EMBEDDING_DIM, MODEL_NAME


class TestEmbedder:
    def test_dimension(self):
        embedder = Embedder()
        assert embedder.dimension == EMBEDDING_DIM

    def test_embed_returns_correct_shape(self):
        embedder = Embedder()

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.randn(3, EMBEDDING_DIM).astype(np.float32)
        embedder._model = mock_model

        result = embedder.embed(["a", "b", "c"])
        assert result.shape == (3, EMBEDDING_DIM)
        assert result.dtype == np.float32

    def test_embed_empty(self):
        embedder = Embedder()
        result = embedder.embed([])
        assert result.shape == (0, EMBEDDING_DIM)

    def test_embed_single(self):
        embedder = Embedder()
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.randn(1, EMBEDDING_DIM).astype(np.float32)
        embedder._model = mock_model

        result = embedder.embed_single("test")
        assert result.shape == (EMBEDDING_DIM,)

    def test_lazy_loading(self):
        embedder = Embedder()
        assert embedder._model is None

    def test_model_name(self):
        assert MODEL_NAME == "all-MiniLM-L6-v2"
