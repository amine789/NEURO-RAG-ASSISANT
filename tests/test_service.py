"""Service tests for specs/api/spec.md and specs/observability/spec.md: the real service, in process.

    pytest tests/test_service.py -v -s           # AP-8, AP-9, OB-5: free; needs Qdrant
    pytest tests/test_service.py -m llm -v -s    # AP-10: real Claude, about $0.03
"""
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

from neuro_rag import config
from neuro_rag.api.app import build_pipeline, create_app
from neuro_rag.encoders import Encoders
from neuro_rag.observability.tracing import LangfuseTracer, Tracer
from neuro_rag.orchestration.pipeline import Pipeline
from neuro_rag.retrieval.retrieve import Retriever
from pipeline_fakes import FakeGenerator, fake_pipeline

KNOWN_PAPERS = Path(__file__).parent / "data" / "known_papers.jsonl"
QUESTION = {"question": "What do place cells do?"}
CLOSED_PORT = "http://localhost:9"  # nothing listens here


def p95(times):
    return sorted(times)[int(0.95 * len(times)) - 1]


@pytest.fixture(scope="module")
def service():
    """The real pipeline and tracer, exactly as uvicorn starts them."""
    with TestClient(create_app()) as client:
        if client.get("/health").status_code != 200:
            pytest.skip("Qdrant or the hippocampus index isn't available")
        yield client


@pytest.mark.integration
def test_AP9_health_with_real_qdrant_up_and_down():
    never_called = FakeGenerator(error=AssertionError("health must not call Claude"))
    up = Pipeline(Retriever(QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY), Encoders()),
                  never_called)
    down = Pipeline(Retriever(QdrantClient(url=CLOSED_PORT), Encoders()), never_called)

    with TestClient(create_app(up, Tracer())) as client:
        ok = client.get("/health")
    with TestClient(create_app(down, Tracer())) as client:
        unavailable = client.get("/health")

    assert ok.status_code == 200
    assert ok.json()["status"] == "ok" and ok.json()["index"].startswith("hippocampus-v")
    assert unavailable.status_code == 503
    assert unavailable.json() == {"status": "unavailable"}


def timed_asks(client, n=5) -> float:
    """Median seconds per request over n requests."""
    times = []
    for _ in range(n):
        start = time.perf_counter()
        assert client.post("/ask", json=QUESTION).status_code == 200
        times.append(time.perf_counter() - start)
    return sorted(times)[n // 2]


@pytest.mark.integration
def test_OB5_langfuse_unreachable_does_not_break_answers(caplog):
    from langfuse import Langfuse

    unreachable = LangfuseTracer(Langfuse(public_key="pk-lf-test", secret_key="sk-lf-test", base_url=CLOSED_PORT))
    with TestClient(create_app(fake_pipeline(), Tracer())) as client:
        without = timed_asks(client)
    with caplog.at_level(logging.WARNING), TestClient(create_app(fake_pipeline(), unreachable)) as client:
        with_tracing = timed_asks(client)
    # the app flushes when it stops; that is when the failed export is logged

    print(f"\nOB-5: median {without * 1000:.0f} ms without tracing, {with_tracing * 1000:.0f} ms with Langfuse unreachable")
    assert with_tracing - without <= 0.5
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING
                and r.name.startswith(("langfuse", "opentelemetry"))]
    assert warnings, "expected a warning that traces couldn't be sent"


@pytest.mark.integration
def test_AP8_models_load_at_startup():
    # The service's own startup, with a fake in place of Claude: Claude's time varies by a second or
    # two between calls and has nothing to do with loading models, so it would hide what is measured.
    with TestClient(create_app(build_pipeline(generator=FakeGenerator()), Tracer())) as client:
        if client.get("/health").status_code != 200:
            pytest.skip("Qdrant or the hippocampus index isn't available")
        start = time.perf_counter()
        first = client.post("/ask", json=QUESTION)
        first_s = time.perf_counter() - start
        start = time.perf_counter()
        second = client.post("/ask", json={"question": "What do grid cells do?"})
        second_s = time.perf_counter() - start

    print(f"\nAP-8: first {first_s:.2f} s, second {second_s:.2f} s")
    assert first.status_code == second.status_code == 200
    assert first_s - second_s <= 1.0


@pytest.mark.llm
def test_AP10_answer_takes_at_most_6s(service):
    with open(KNOWN_PAPERS, encoding="utf-8") as f:
        questions = [json.loads(line)["question"] for line in f if line.strip()]

    def timed(question):
        start = time.perf_counter()
        r = service.post("/ask", json={"question": question})
        assert r.status_code == 200, r.text
        return time.perf_counter() - start

    one_at_a_time = [timed(q) for q in questions]
    with ThreadPoolExecutor(max_workers=4) as pool:
        four_at_a_time = list(pool.map(timed, questions))

    print(f"\nAP-10: one at a time p50 {sorted(one_at_a_time)[10]:.1f} s, p95 {p95(one_at_a_time):.1f} s; "
          f"4 at a time p50 {sorted(four_at_a_time)[10]:.1f} s, p95 {p95(four_at_a_time):.1f} s")
    assert p95(one_at_a_time) <= 6.0
