"""Corpus tests for specs/correction/spec.md (rewrite): the real index, reranker and rewriter (CR-9, CR-10).

Follows "The CR-9 retrieval run" and "The CR-10 timing run" in the spec. Well under $0.01. Run with -s:

    pytest tests/test_rewrite_corpus.py -m llm -v -s
"""
import json
import os
import time
from collections import defaultdict

import pytest
from qdrant_client import QdrantClient

from neuro_rag import config
from neuro_rag.correction.rewrite import Rewriter
from neuro_rag.encoders import Encoders
from neuro_rag.eval.run import load_questions
from neuro_rag.retrieval.rerank import Reranker
from neuro_rag.retrieval.retrieve import RetrievalError, Retriever

pytestmark = [pytest.mark.llm,
              pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY")]

RERANK_RUN = config.PROJECT_ROOT / "eval" / "results" / "2026-10-18_2224_rerank" / "runs.jsonl"
KNOWN_PAPERS = config.PROJECT_ROOT / "tests" / "data" / "known_papers.jsonl"
MIN_FOUND = 4


@pytest.fixture(scope="module")
def retriever():
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    r = Retriever(client, Encoders(), reranker=Reranker())
    try:
        r.index_name()
    except RetrievalError as e:
        pytest.skip(f"no index to test: {e}")  # step 4: skipped, not failed
    yield r
    client.close()


def missed_questions():
    """Step 1: questions with an expected paper found in at most half of their repeats."""
    hits = defaultdict(list)
    with open(RERANK_RUN, encoding="utf-8") as f:
        for run in map(json.loads, f):
            hits[run["id"]].append(bool(run.get("retrieval_hit")))
    return [q for q in load_questions()
            if q.expected_pmcids and not q.type.startswith(("off_domain", "out_of_corpus"))
            and q.type != "borderline" and sum(hits[q.id]) <= len(hits[q.id]) / 2]


@pytest.fixture(scope="module")
def retrieval_run(retriever):
    rewriter = Rewriter()
    rows = []
    for q in missed_questions():
        start = time.perf_counter()  # step 2
        query = rewriter.rewrite(q.question)
        seconds = time.perf_counter() - start
        found = bool(q.expected_pmcids & {c.pmcid for c in retriever.retrieve(query, k=5)})
        rows.append((q.id, found, q.question, query, seconds))
    return rows


def p95(values):
    return sorted(values)[max(0, round(0.95 * len(values)) - 1)]


def test_CR9_rewriting_finds_missed_papers(retrieval_run):
    print("\nCR-9 missed questions, rewritten:")  # step 3
    for qid, found, question, query, seconds in retrieval_run:
        print(f"  {'found' if found else 'not found':9}  {qid}  {seconds:.2f} s\n      {question}\n   -> {query}")
    times = [seconds for *_, seconds in retrieval_run]
    found = sum(found for _, found, *_ in retrieval_run)
    print(f"CR-9: found {found}/{len(retrieval_run)}; rewrite p50 {sorted(times)[len(times) // 2]:.2f} s, "
          f"p95 {p95(times):.2f} s")

    assert len(retrieval_run) == 8  # q30, q31, q33, q36, q37, q38, q39, q40 on 2026-10-21
    assert found >= MIN_FOUND


def test_CR10_rewrite_time_is_measured(retrieval_run):
    """The CR-10 timing run: the 8 CR-9 times plus 20 known-paper questions."""
    times = [seconds for *_, seconds in retrieval_run]  # step 2: reused
    rewriter = Rewriter()
    with open(KNOWN_PAPERS, encoding="utf-8") as f:
        for question in [json.loads(line)["question"] for line in f if line.strip()]:
            start = time.perf_counter()
            rewriter.rewrite(question)
            times.append(time.perf_counter() - start)
    print(f"\nCR-10: {len(times)} rewrites; p50 {sorted(times)[len(times) // 2]:.2f} s, "
          f"p95 {p95(times):.2f} s")  # step 4

    assert len(times) == 28  # step 1; no limit checked (spec, choice 6)
