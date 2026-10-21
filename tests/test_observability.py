"""Unit tests for specs/observability/spec.md: the API with a recording tracer and a pipeline of fakes."""
import logging
import re

from fastapi.testclient import TestClient

from neuro_rag.api.app import create_app
from neuro_rag.generation.generate import GenerationError
from neuro_rag.retrieval.retrieve import RetrievalError
from pipeline_fakes import ANSWER, PLACE_CELLS, FakeGenerator, FakeRetriever, RecordingTracer, fake_pipeline

QUESTION = {"question": "What do place cells do?"}


def ask(pipeline=None, tracer=None, body=QUESTION):
    tracer = tracer or RecordingTracer()
    with TestClient(create_app(pipeline or fake_pipeline(), tracer)) as client:
        return client.post("/ask", json=body), tracer


def test_OB1_one_trace_with_three_steps_in_order():
    r, tracer = ask()

    assert len(tracer.traces) == 1
    trace = tracer.traces[0]
    assert trace["name"] == "ask"
    assert trace["input"] == "What do place cells do?"
    assert trace["output"] == {"answer": ANSWER, "pmcids": ["PMC1"], "path": "papers"}
    assert [s["name"] for s in trace["steps"]] == ["retrieve", "rerank", "generate"]
    for step in trace["steps"]:
        assert step["start"] <= step["end"]
    assert r.json()["trace_id"] == trace["id"]


def test_OB2_retrieve_and_rerank_show_chosen_chunks():
    _, tracer = ask()
    retrieve, rerank, generate = tracer.traces[0]["steps"]

    assert len(retrieve["output"]) == 20  # every fused chunk
    assert len(rerank["output"]) == 5  # the chunks kept
    for listed in retrieve["output"] + rerank["output"]:
        assert set(listed) == {"chunk_id", "pmcid", "page", "score"}  # no texts here
    assert rerank["output"][0]["score"] == 20.0  # the fake reranker's score, not the fused one
    assert PLACE_CELLS in generate["input"]["documents"]  # texts appear once, in "generate"


def test_OB3_generate_records_model_tokens_and_cost():
    _, tracer = ask()
    generate = tracer.traces[0]["steps"][2]

    assert generate["kind"] == "generation"
    assert generate["model"] == "claude-haiku-5-5"
    assert generate["input"]["documents"] == [PLACE_CELLS] * 5
    assert generate["output"] == ANSWER
    assert generate["usage"] == {"input": 3000, "output": 400}
    assert abs(generate["cost"] - 0.0005) < 1e-12  # 3,000 x $0.10/1M + 400 x $0.50/1M


def test_OB4_failed_request_is_traced_with_its_error():
    pipeline = fake_pipeline(FakeRetriever(error=RetrievalError("Qdrant is unreachable")))
    r, tracer = ask(pipeline)

    assert r.status_code == 503
    assert len(tracer.traces) == 1
    trace = tracer.traces[0]
    assert [s["name"] for s in trace["steps"]] == ["retrieve"]
    assert "Qdrant is unreachable" in trace["steps"][0]["error"]
    assert r.json()["trace_id"] == trace["id"]


def test_OB6_no_keys_means_tracing_off(monkeypatch, caplog):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    with caplog.at_level(logging.INFO), TestClient(create_app(fake_pipeline())) as client:
        first = client.post("/ask", json=QUESTION)
        second = client.post("/ask", json=QUESTION)

    for r in (first, second):
        assert r.status_code == 200
        assert re.fullmatch(r"[0-9a-f]{32}", r.json()["trace_id"])  # generated locally
    assert caplog.text.count("tracing is off") == 1  # said once, at startup


def test_OB7_no_api_key_in_traces(monkeypatch):
    secrets = {"ANTHROPIC_API_KEY": "sk-ant-test-123", "LANGFUSE_SECRET_KEY": "sk-lf-test-456",
               "QDRANT_API_KEY": "qd-test-789"}
    for name, value in secrets.items():
        monkeypatch.setenv(name, value)
    tracer = RecordingTracer()

    ask(tracer=tracer)
    # an error message that carries a key, as a client library's error might
    leaky = GenerationError("Claude is unavailable: request with x-api-key sk-ant-test-123 failed")
    ask(fake_pipeline(generator=FakeGenerator(error=leaky)), tracer)

    assert len(tracer.traces) == 2
    recorded = repr(tracer.traces)
    for value in secrets.values():
        assert value not in recorded
    assert "[redacted]" in recorded  # the message was kept, the key removed
