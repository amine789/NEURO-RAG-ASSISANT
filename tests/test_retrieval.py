"""Unit tests for specs/retrieval/spec.md: no Qdrant, no models. Named after the criteria."""
import numpy as np
import pytest
from qdrant_client.http.exceptions import ResponseHandlingException

import neuro_rag.encoders as encoders_module
import neuro_rag.retrieval.rerank as rerank_module
from neuro_rag.encoders import Encoders
from neuro_rag.retrieval.rerank import Reranker
from neuro_rag.retrieval.retrieve import RetrievalError, Retriever


class FakeQdrant:
    """Records every call; returns `points` (none by default), or raises `error` if set."""

    def __init__(self, error=None, points=()):
        self.calls = []
        self.error = error
        self.points = list(points)

    def query_points(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return type("Response", (), {"points": self.points[:kwargs["limit"]]})()


def fake_point(name, score):
    payload = {"chunk_id": name, "text": name, "pmcid": "PMC1", "title": "Title", "citation": "Citation",
               "license": "CC BY", "page": 1}
    return type("Point", (), {"payload": payload, "score": score})()


class FakeReranker:
    """Scores c20 highest, then c19, down to c1; records what it was given."""

    def __init__(self):
        self.calls = []

    def score(self, question, texts):
        self.calls.append((question, texts))
        return [float(t[1:]) for t in texts]


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


def test_RT14_reranker_scores_decide_the_order(counting_models):
    qdrant = FakeQdrant(points=[fake_point(f"c{i}", 1 / i) for i in range(1, 21)])  # c1 first by fusion
    reranker = FakeReranker()
    retriever = Retriever(qdrant, Encoders(), reranker=reranker)

    results = retriever.retrieve("where are place cells?", k=5)

    assert qdrant.calls[-1]["limit"] == 20
    assert reranker.calls == [("where are place cells?", [f"c{i}" for i in range(1, 21)])]
    assert [r.chunk_id for r in results] == ["c20", "c19", "c18", "c17", "c16"]
    assert [r.score for r in results] == [20.0, 19.0, 18.0, 17.0, 16.0]


class CountingCrossEncoder:
    loads = 0

    def __init__(self, model_name):
        CountingCrossEncoder.loads += 1

    def rerank(self, query, documents):
        return [0.0 for _ in documents]


def test_RT16_reranker_loads_once(counting_models, monkeypatch):
    CountingCrossEncoder.loads = 0
    monkeypatch.setattr(rerank_module, "TextCrossEncoder", CountingCrossEncoder)
    qdrant = FakeQdrant(points=[fake_point(f"c{i}", 1 / i) for i in range(1, 21)])
    retriever = Retriever(qdrant, Encoders(), reranker=Reranker())

    retriever.retrieve("where are place cells?")
    retriever.retrieve("what do grid cells do?")

    assert CountingCrossEncoder.loads == 1
