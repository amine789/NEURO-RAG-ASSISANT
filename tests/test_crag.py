"""Row 9's corrective loop, CR-4 to CR-8 (docs/specs/crag/spec.md, phase 2).

Unit tests with fakes only: no Qdrant, no grader, no Claude, no web, no cost.
Every step run_loop calls is a fake that records what it got:

  - FakeSearch: returns hits whose text is "good" or "weak", chosen per query
    (a dict query -> "good"/"weak"; any query not listed gets "weak"), and records
    the queries it was called with;
  - fake_grade: reads that mark: 0.9 for "good" hits, 0.1 for "weak" (GRADE_CUT is 0.5);
  - FakeAnswer: records (question, hits) and returns a fixed Answer;
  - FakeRewrite: returns "clear query 1", then "clear query 2", ... and counts calls;
  - FakeWeb: returns "good" or "weak" hits and records its queries.

Run: pytest tests/test_crag.py -v
"""
import pytest

from neuro_rag.config import MAX_REWRITES
from neuro_rag.crag.loop import run_loop
from neuro_rag.generation.answer import NOT_FOUND, Answer
from neuro_rag.retrieval.search import Hit

QUESTION = "why do I keep forgetting where I put my keys?"
ANSWER = Answer("Place cells ... [1]", [], [], 100, 20)


def hits(mark: str) -> list[Hit]:
    """Two hits whose text is the mark ("good" or "weak"), so fake_grade can read it."""
    return [Hit(f"PMC1-p1-c{i}", "PMC1", 1, "Title", "Citation", "CC BY", mark, 0.5) for i in range(2)]


def fake_grade(question, hits_):
    """P(yes) from the mark: good hits score above GRADE_CUT, weak hits below."""
    return 0.9 if hits_[0].text == "good" else 0.1


class FakeSearch:
    """search_fn: hits marked per query (default weak); records every query."""

    def __init__(self, marks: dict[str, str]):
        self.marks = marks
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        return hits(self.marks.get(query, "weak"))


class FakeAnswer:
    """answer_fn: records (question, hits), returns ANSWER."""

    def __init__(self):
        self.calls = []

    def __call__(self, question, hits_):
        self.calls.append((question, hits_))
        return ANSWER


class FakeRewrite:
    """rewrite_fn: "clear query 1", "clear query 2", ...; records (question, last_query)."""

    def __init__(self):
        self.calls = []

    def __call__(self, question, last_query):
        self.calls.append((question, last_query))
        return f"clear query {len(self.calls)}"


class FakeWeb:
    """web_fn: hits with the given mark; records every query."""

    def __init__(self, mark: str):
        self.mark = mark
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        return hits(self.mark)


def raising(*args):
    """A step that always fails, as a network error would."""
    raise RuntimeError("service down")


def test_CR4_good_retrieval_answers_directly():
    search, answer, rewrite, web = FakeSearch({QUESTION: "good"}), FakeAnswer(), FakeRewrite(), FakeWeb("good")

    result = run_loop(QUESTION, search, fake_grade, answer, rewrite, web)

    assert result.path == ["retrieve", "grade:good", "generate"]
    assert rewrite.calls == []
    assert web.queries == []
    assert result.used_web is False
    assert result.answer == ANSWER
    assert answer.calls == [(QUESTION, hits("good"))]


def test_CR5_weak_is_rewritten_and_retried_original_question_answered():
    search, answer, rewrite, web = FakeSearch({"clear query 1": "good"}), FakeAnswer(), FakeRewrite(), FakeWeb("good")

    result = run_loop(QUESTION, search, fake_grade, answer, rewrite, web)

    assert result.path == ["retrieve", "grade:weak", "rewrite", "retrieve", "grade:good", "generate"]
    assert search.queries == [QUESTION, "clear query 1"]
    assert answer.calls[0][0] == QUESTION                  # the user's question, not the rewrite
    assert rewrite.calls == [(QUESTION, QUESTION)]
    assert web.queries == []
    assert result.used_web is False


def test_CR6_stops_after_max_rewrites_then_the_web():
    search, answer, rewrite, web = FakeSearch({}), FakeAnswer(), FakeRewrite(), FakeWeb("good")

    result = run_loop(QUESTION, search, fake_grade, answer, rewrite, web)

    assert MAX_REWRITES == 2
    assert len(rewrite.calls) == 2
    assert result.path.count("retrieve") == 3
    assert result.path[-3:] == ["web", "grade:good", "generate"]
    assert result.used_web is True
    assert web.queries == ["clear query 2"]                # the last rewrite searches the web
    assert search.queries == [QUESTION, "clear query 1", "clear query 2"]
    assert rewrite.calls[1] == (QUESTION, "clear query 1") # the second rewrite sees the first
    assert answer.calls[0][0] == QUESTION


def test_CR7_weak_everywhere_is_not_covered_with_no_answer_call():
    search, answer, rewrite, web = FakeSearch({}), FakeAnswer(), FakeRewrite(), FakeWeb("weak")

    result = run_loop(QUESTION, search, fake_grade, answer, rewrite, web)

    assert result.path == ["retrieve", "grade:weak", "rewrite",
                           "retrieve", "grade:weak", "rewrite",
                           "retrieve", "grade:weak",
                           "web", "grade:weak", "not_covered"]
    assert result.answer.text == NOT_FOUND
    assert result.answer.sources == []
    assert answer.calls == []
    assert result.used_web is False


@pytest.mark.parametrize("failing", ["grade", "rewrite", "web", "all"])
def test_CR8_failures_degrade_never_crash(failing):
    search, answer = FakeSearch({}), FakeAnswer()
    grade_fn = raising if failing in ("grade", "all") else fake_grade
    rewrite_fn = raising if failing in ("rewrite", "all") else FakeRewrite()
    web_fn = raising if failing in ("web", "all") else FakeWeb("weak")

    result = run_loop(QUESTION, search, grade_fn, answer, rewrite_fn, web_fn)   # must not raise

    assert result.path[-1] == "not_covered"
    assert answer.calls == []
    if failing == "rewrite":
        assert search.queries == [QUESTION] * 3            # a failed rewrite keeps the last query


def test_CR8_a_failing_grade_counts_as_weak_even_on_good_hits():
    search, answer, rewrite, web = FakeSearch({QUESTION: "good"}), FakeAnswer(), FakeRewrite(), FakeWeb("good")

    result = run_loop(QUESTION, search, raising, answer, rewrite, web)

    assert "grade:good" not in result.path                 # never answered from ungraded chunks
    assert result.path[-1] == "not_covered"
    assert answer.calls == []
