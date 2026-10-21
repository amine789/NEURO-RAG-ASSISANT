"""Rewrite tests for specs/correction/spec.md with the real Claude (CR-5 to CR-8). They cost money.

    pytest tests/test_rewrite_llm.py -m llm -v -s
"""
import os

import pytest

from neuro_rag.correction.rewrite import Rewriter

pytestmark = [pytest.mark.llm,
              pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY")]


@pytest.fixture(scope="module")
def rewriter():
    return Rewriter()


def rewritten(rewriter, question):
    query = rewriter.rewrite(question)
    print(f"\n  {question}\n  -> {query}")
    return query


def test_CR5_everyday_words_become_papers_terms(rewriter):
    query = rewritten(rewriter, "How do the fear center and the memory center keep their rhythms in step "
                                "when people form unpleasant memories?").lower()

    assert "amygdala" in query
    assert "hippocampus" in query or "hippocampal" in query


def test_CR6_other_language_becomes_english_query(rewriter):
    query = rewritten(rewriter, "Welche Rolle spielt der ventrale Hippocampus dabei, sich zu merken, "
                                "wo es Futter gibt?").lower()

    assert "ventral hippocampus" in query
    assert any(word in query for word in ("food", "foraging", "reward"))
    assert not any(word in query for word in ("rolle", "dabei", "merken", "futter"))


def test_CR7_rewrite_is_a_query_not_an_answer(rewriter):
    query = rewritten(rewriter, "is there some pill you can take right after studying that makes the stuff "
                                "stick better?")

    assert len(query.split(" ")) <= 30
    assert not query.lower().startswith(("yes", "no"))
    assert any(term in query.lower() for term in ("consolidation", "pharmacolog", "enhanc", "post-training"))


def test_CR8_precise_question_keeps_exact_terms(rewriter):
    query = rewritten(rewriter, "What is the role of Ythdf1 in m6A-dependent translation in the hippocampus?")

    assert "Ythdf1" in query
    assert "m6A" in query
