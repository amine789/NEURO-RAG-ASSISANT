"""Unit tests for specs/api/spec.md: FastAPI's test client and a pipeline of fakes; no Qdrant, no Claude."""
import logging

import pytest
from fastapi.testclient import TestClient

from neuro_rag.api.app import create_app
from neuro_rag.generation.generate import GenerationError
from neuro_rag.retrieval.retrieve import RetrievalError
from pipeline_fakes import ANSWER, PMC1_URL, FakeGenerator, FakeRetriever, RecordingTracer, fake_pipeline

QUESTION = {"question": "What do place cells do?"}


def client_for(pipeline=None):
    return TestClient(create_app(pipeline or fake_pipeline(), RecordingTracer()))


# Answers

def test_AP1_question_gets_answer_sources_and_trace_id():
    with client_for() as client:
        r = client.post("/ask", json=QUESTION)

    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == ANSWER
    assert body["sources"] == [{"n": 1, "pmcid": "PMC1", "title": "Place cells paper",
                                "citation": "Author et al. 2020", "page": 3, "url": PMC1_URL}]
    assert body["trace_id"]


def test_AP2_uncovered_question_is_an_answer():
    pipeline = fake_pipeline(generator=FakeGenerator(text="The provided papers don't cover this."))
    with client_for(pipeline) as client:
        r = client.post("/ask", json={"question": "How do I fix a flat tyre?"})

    assert r.status_code == 200
    assert r.json()["answer"] == "The provided papers don't cover this."
    assert r.json()["sources"] == []


# Bad input

def test_AP3_empty_question_is_rejected():
    retriever = FakeRetriever()
    with client_for(fake_pipeline(retriever)) as client:
        responses = [client.post("/ask", json=body) for body in ({"question": ""}, {"question": "   "}, {})]

    for r in responses:
        assert r.status_code == 422
        assert "missing" in r.json()["detail"] or "empty" in r.json()["detail"]
    assert retriever.calls == 0


def test_AP4_question_over_1000_characters_is_rejected():
    retriever = FakeRetriever()
    with client_for(fake_pipeline(retriever)) as client:
        too_long = client.post("/ask", json={"question": "a" * 1001})
        assert retriever.calls == 0
        at_limit = client.post("/ask", json={"question": "a" * 1000})

    assert too_long.status_code == 422
    assert "1,000" in too_long.json()["detail"]
    assert at_limit.status_code == 200


# Failures

def test_AP5_qdrant_down_gives_503():
    pipeline = fake_pipeline(FakeRetriever(error=RetrievalError("Qdrant is unreachable")))
    with client_for(pipeline) as client:
        r = client.post("/ask", json=QUESTION)

    assert r.status_code == 503
    assert r.json()["detail"] == "The paper index is unavailable. Please try again shortly."
    assert r.json()["trace_id"]
    assert "Traceback" not in r.text and "localhost" not in r.text and "6333" not in r.text


def test_AP6_claude_unavailable_gives_503():
    pipeline = fake_pipeline(generator=FakeGenerator(error=GenerationError("Claude is unavailable")))
    with client_for(pipeline) as client:
        r = client.post("/ask", json=QUESTION)

    assert r.status_code == 503
    assert r.json()["detail"] == "The answer service is unavailable. Please try again shortly."
    assert r.json()["trace_id"]


def test_AP7_unexpected_error_gives_500_and_reveals_nothing(caplog):
    pipeline = fake_pipeline(generator=FakeGenerator(error=KeyError("payload")))
    with caplog.at_level(logging.ERROR), client_for(pipeline) as client:
        r = client.post("/ask", json=QUESTION)

    assert r.status_code == 500
    assert r.json()["detail"] == "Something went wrong."
    trace_id = r.json()["trace_id"]
    assert trace_id
    assert "KeyError" not in r.text and "payload" not in r.text
    logged = [rec for rec in caplog.records if trace_id in rec.getMessage()]
    assert logged and "KeyError" in caplog.text  # the full error is in the log, under the same trace ID


# Service

def test_AP9_health_ok():
    with client_for() as client:
        r = client.get("/health")

    assert r.status_code == 200
    assert r.json() == {"status": "ok", "index": "hippocampus-v1"}


def test_AP9_health_unavailable():
    pipeline = fake_pipeline(FakeRetriever(index=RetrievalError("Qdrant is unreachable")),
                             FakeGenerator(error=AssertionError("health must not call Claude")))
    with client_for(pipeline) as client:
        r = client.get("/health")

    assert r.status_code == 503
    assert r.json() == {"status": "unavailable"}
