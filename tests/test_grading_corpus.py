"""Corpus tests for specs/grading/spec.md: the real index, reranker and grader (GR-10, GR-11). About $0.01.

Follows "The GR-10 agreement run" in the spec, step by step. Run with -s to see every question:

    pytest tests/test_grading_corpus.py -m llm -v -s
"""
import json
import os
import time
from collections import defaultdict

import pytest
from qdrant_client import QdrantClient

from neuro_rag import config
from neuro_rag.encoders import Encoders
from neuro_rag.eval.run import load_questions
from neuro_rag.grading.grade import Grader
from neuro_rag.retrieval.rerank import Reranker
from neuro_rag.retrieval.retrieve import RetrievalError, Retriever

pytestmark = [pytest.mark.llm,
              pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY")]

RERANK_RUN = config.PROJECT_ROOT / "eval" / "results" / "2026-10-18_2224_rerank" / "runs.jsonl"
FOUND_PASS = 0.9
OTHERS_FAIL = 0.6
MAX_P95_S = 2.0


@pytest.fixture(scope="module")
def retriever():
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    r = Retriever(client, Encoders(), reranker=Reranker())
    try:
        r.index_name()
    except RetrievalError as e:
        pytest.skip(f"no index to test: {e}")  # step 6: skipped, not failed
    yield r
    client.close()


def labels(questions) -> dict[str, str]:
    """Step 2: off-topic, missed, found, or left out (borderline)."""
    hits = defaultdict(list)
    with open(RERANK_RUN, encoding="utf-8") as f:
        for run in map(json.loads, f):
            hits[run["id"]].append(bool(run.get("retrieval_hit")))
    out = {}
    for q in questions:
        if q.type.startswith("off_domain"):
            out[q.id] = "off-topic"
        elif q.type.startswith("out_of_corpus"):
            out[q.id] = "missed"
        elif q.type == "borderline":
            continue
        else:
            assert q.expected_pmcids, f"{q.id} has no expected paper"
            out[q.id] = "found" if sum(hits[q.id]) > len(hits[q.id]) / 2 else "missed"
    return out


@pytest.fixture(scope="module")
def agreement_run(retriever):
    questions = load_questions()  # step 1
    text = {q.id: q.question for q in questions}
    grader = Grader()
    rows = []
    for qid, label in labels(questions).items():
        chunks = retriever.retrieve(text[qid], k=5)  # step 3
        start = time.perf_counter()
        result = grader.grade(text[qid], chunks)
        rows.append((qid, label, result, time.perf_counter() - start, text[qid]))
    return rows


def p95(values):
    return sorted(values)[max(0, round(0.95 * len(values)) - 1)]


def test_GR10_grader_agrees_with_eval_labels(agreement_run):
    print("\nGR-10 grade per question:")  # step 5
    for qid, label, result, seconds, question in agreement_run:
        agrees = result.passed == (label == "found")  # step 4
        print(f"  {'passed' if result.passed else 'failed':6}  {label:9}  {'agrees' if agrees else 'DISAGREES':9}  "
              f"relevant {result.relevant}  {seconds:.2f} s  {qid}  {question}")
    found = [r for _, label, r, *_ in agreement_run if label == "found"]
    others = [r for _, label, r, *_ in agreement_run if label != "found"]
    found_pass = sum(r.passed for r in found) / len(found)
    others_fail = sum(not r.passed for r in others) / len(others)
    times = [seconds for *_, seconds, _ in agreement_run]
    print(f"GR-10: found passing {found_pass:.0%} ({len(found)}), missed and off-topic failing {others_fail:.0%} "
          f"({len(others)}); grading p50 {sorted(times)[len(times) // 2]:.2f} s, p95 {p95(times):.2f} s")

    assert found_pass >= FOUND_PASS
    assert others_fail >= OTHERS_FAIL


def test_GR11_grading_takes_at_most_2s(agreement_run):
    assert p95([seconds for *_, seconds, _ in agreement_run]) <= MAX_P95_S
