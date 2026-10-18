"""The dense and sparse encoders, defined once for ingest and retrieval.

If indexing and querying encoded text differently, search would get worse
without any error (ARCHITECTURE section 2), so both import from here.
"""
from functools import cached_property
from importlib.metadata import version

from fastembed import SparseTextEmbedding
from qdrant_client.models import SparseVector
from sentence_transformers import SentenceTransformer

from neuro_rag.config import DENSE_MODEL, SPARSE_MODEL


class Encoders:
    """Loads both models on first use, so importing this module stays cheap."""

    @cached_property
    def dense_model(self) -> SentenceTransformer:
        return SentenceTransformer(DENSE_MODEL)

    @cached_property
    def sparse_model(self) -> SparseTextEmbedding:
        return SparseTextEmbedding(model_name=SPARSE_MODEL)

    @property
    def max_tokens(self) -> int:
        """Longest input the dense model reads; anything longer is cut off silently."""
        return self.dense_model.max_seq_length

    def count_tokens(self, text: str) -> int:
        """Tokens the dense model sees, including its two special tokens ([CLS], [SEP])."""
        return len(self.dense_model.tokenizer(text)["input_ids"])

    def dense(self, texts: list[str]) -> list[list[float]]:
        vectors = self.dense_model.encode(texts, normalize_embeddings=True, batch_size=64)
        return vectors.tolist()

    def sparse(self, texts: list[str]) -> list[SparseVector]:
        """BM25 term-frequency weights only; Qdrant adds IDF at search time (decision 002)."""
        return [
            SparseVector(indices=e.indices.tolist(), values=e.values.tolist())
            for e in self.sparse_model.embed(texts)
        ]

    def describe(self) -> dict:
        """Names and library versions, recorded with each index (IN-12)."""
        return {
            "dense_model": DENSE_MODEL,
            "dense_library": f"sentence-transformers {version('sentence-transformers')}",
            "sparse_model": SPARSE_MODEL,
            "sparse_library": f"fastembed {version('fastembed')}",
        }
