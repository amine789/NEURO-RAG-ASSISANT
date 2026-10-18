"""Cross-encoder reranker: scores each (question, chunk) pair together.

Runs on ONNX through FastEmbed, the library that already runs the BM25 encoder;
the same model on PyTorch was too slow on CPU (RT-17).

Spec: docs/specs/retrieval/spec.md, Reranking (RT-14 to RT-17).
"""
from functools import cached_property

from fastembed.rerank.cross_encoder import TextCrossEncoder

from neuro_rag.config import RERANK_MODEL


class Reranker:
    """Loads its model on first use, once per process (RT-16)."""

    def __init__(self, model_name: str = RERANK_MODEL):
        self.model_name = model_name

    @cached_property
    def model(self) -> TextCrossEncoder:
        return TextCrossEncoder(model_name=self.model_name)

    def score(self, question: str, texts: list[str]) -> list[float]:
        """One relevance score per text, higher is better; same order as `texts`."""
        return [float(s) for s in self.model.rerank(question, texts)]
