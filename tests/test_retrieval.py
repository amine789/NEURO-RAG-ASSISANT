"""Unit tests for specs/retrieval/spec.md: no Qdrant, no models. Named after the criteria."""
import numpy as np
import pytest
from qdrant_client.http.exceptions import ResponseHandlingException

import neuro_rag.encoders as encoders_module
from neuro_rag.encoders import Encoders
from neuro_rag.retrieval.retrieve import RetrievalError, Retriever


class FakeQdrant:
    """Records every call; returns no points, or raises `error` if set."""

    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def query_points(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return type("Response", (), {"points": []})()


class CountingDenseModel:
    loads = 0

    def __init__(self, name):
        CountingDenseModel.loads += 1

    def encode(self, texts, **kwargs):
        return np.zeros((len(texts), 384))


class CountingSparseModel:
    loads = 0

    def __init__(self, model_name):
        CountingSparseModel.loads += 1

    def embed(self, texts):
        for _ in texts:
            yield type("Sparse", (), {"indices": np.array([1, 2]), "values": np.array([1.0, 1.0])})()


@pytest.fixture
def counting_models(monkeypatch):
    CountingDenseModel.loads = CountingSparseModel.loads = 0
    monkeypatch.setattr(encoders_module, "SentenceTransformer", CountingDenseModel)
    monkeypatch.setattr(encoders_module, "SparseTextEmbedding", CountingSparseModel)


def test_RT10_encoders_load_once(counting_models):
    retriever = Retriever(FakeQdrant(), Encoders())

    retriever.retrieve("where are place cells?")
    retriever.retrieve("what do grid cells do?")

    assert CountingDenseModel.loads == 1
    assert CountingSparseModel.loads == 1


def test_RT11_empty_question_is_rejected_before_qdrant(counting_models):
    qdrant = FakeQdrant()
    retriever = Retriever(qdrant, Encoders())

    for question in ["", "   "]:
        with pytest.raises(ValueError):
            retriever.retrieve(question)

    assert qdrant.calls == []


def test_RT12_qdrant_unreachable_gives_clear_error(counting_models):
    down = FakeQdrant(error=ResponseHandlingException(ConnectionError("connection refused")))
    retriever = Retriever(down, Encoders())

    with pytest.raises(RetrievalError, match="Qdrant is unreachable"):
        retriever.retrieve("where are place cells?")
