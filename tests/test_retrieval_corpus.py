"""Corpus tests for specs/retrieval/spec.md, on the real `hippocampus` index.

Skipped if Qdrant isn't running or the index isn't built. Run with -s to see
the RT-7 and RT-13 reports:

    pytest tests/test_retrieval_corpus.py -s
"""
import json
import time
from pathlib import Path

import pytest
from qdrant_client import QdrantClient

from neuro_rag import config
from neuro_rag.encoders import Encoders
from neuro_rag.retrieval.retrieve import RetrievalError, Retriever

KNOWN_PAPERS = Path(__file__).parent / "data" / "known_papers.jsonl"
MORE_QUESTIONS = [  # with the 20 known-paper questions, the 50 timed by RT-13
    "What do place cells encode?", "How does sleep help memory?", "What is long-term potentiation?",
    "How does stress affect the hippocampus?", "What are grid cells?", "How are memories consolidated?",
    "What is an engram?", "Does exercise improve memory?", "What does the dentate gyrus do?",
    "How does the prefrontal cortex interact with the hippocampus?", "What is working memory?",
    "How is fear memory formed?", "What happens to memory in Alzheimer's disease?",
    "What is pattern separation?", "How does aging affect memory?", "What is memory replay?",
    "How do NMDA receptors affect learning?", "What is the role of CA1?", "What is episodic memory?",
    "How do circadian rhythms affect memory?", "What is synaptic plasticity?",
    "How is spatial memory tested in mice?", "What does the amygdala do in memory?",
    "How does radiation affect memory?", "What is remote memory?", "What is optogenetics?",
    "How does diet affect memory?", "What is systems consolidation?", "What are sharp-wave ripples?",
    "How do astrocytes affect memory?",
]


@pytest.fixture(scope="module")
def retriever():
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    r = Retriever(client, Encoders())
    try:
        r.retrieve("hippocampus")  # also loads the encoders before anything is timed
    except RetrievalError as e:
        pytest.skip(f"no index to test: {e}")
    yield r
    client.close()


def known_papers():
    with open(KNOWN_PAPERS, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_RT4_meaning_is_found_without_shared_words(retriever):
    texts = [r.text.lower() for r in retriever.retrieve("how do animals remember where things are?", k=5)]
    assert any("place cell" in t or "spatial memory" in t for t in texts)


def test_RT7_known_papers_are_found(retriever):
    questions = known_papers()
    in_top5, in_candidates, missed = 0, 0, []
    for q in questions:
        top5 = {r.pmcid for r in retriever.retrieve(q["question"], k=5)}
        found = q["pmcid"] in top5
        candidate = q["pmcid"] in retriever.candidate_pmcids(q["question"])
        in_top5 += found
        in_candidates += candidate
        if not found:
            missed.append(f"  {q['pmcid']} ({'in' if candidate else 'not in'} candidates): {q['question']}")

    print(f"\nRT-7 known papers: top 5 {in_top5}/{len(questions)}, candidates {in_candidates}/{len(questions)}")
    print("\n".join(missed))
    assert in_top5 >= 18


def test_RT13_one_retrieval_takes_at_most_500ms(retriever):
    questions = [q["question"] for q in known_papers()] + MORE_QUESTIONS
    assert len(questions) == 50
    times = []
    for q in questions:
        start = time.perf_counter()
        retriever.retrieve(q, k=5)
        times.append(time.perf_counter() - start)

    p95 = sorted(times)[int(0.95 * len(times)) - 1]
    print(f"\nRT-13 retrieval: p50 {sorted(times)[len(times) // 2] * 1000:.0f} ms, p95 {p95 * 1000:.0f} ms")
    assert p95 <= 0.5
