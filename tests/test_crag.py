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

CR-9 replaces requests.post with a fake Firecrawl reply (no network, no credits)
and gives answer() a fake LLM, as tests/test_answer.py does.

Run: pytest tests/test_crag.py -v
"""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from neuro_rag.config import MAX_REWRITES
from neuro_rag.api.app import SEARCH_DOWN, create_app
from neuro_rag.crag import loop
from neuro_rag.crag.loop import run_loop, web_hits
from neuro_rag.generation.answer import NOT_FOUND, Answer, answer
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


# --- CR-9: the web path, with a fake Firecrawl reply -------------------------------

NATURE = "https://www.nature.com/articles/s41586-0001"
BLOG = "https://random-blog.example/dopamine"
DOPAMINE = "Loss of dopamine neurons in the substantia nigra causes the motor symptoms of Parkinson's disease."


class FakeFirecrawl:
    """Stands in for requests.post: returns a fixed Firecrawl /v2/search reply and records the request."""

    def __init__(self, results):
        self.results = results
        self.calls = []

    def __call__(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json})
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"success": True, "data": {"web": self.results}})


def fake_rerank(query, texts):
    """Row 8's reranker stand-in: every chunk scores 1.0."""
    return [1.0] * len(texts)


def word_count(text):
    """TokenCounter stand-in: one token per word."""
    return len(text.split())


def test_CR9_only_allow_listed_pages_become_web_hits(monkeypatch):
    firecrawl = FakeFirecrawl([
        {"url": NATURE, "title": "Dopamine and Parkinson's", "markdown": DOPAMINE},
        {"url": BLOG, "title": "My blog", "markdown": DOPAMINE},
    ])
    monkeypatch.setattr(loop.requests, "post", firecrawl)
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

    result = web_hits("dopamine loss substantia nigra Parkinson's", fake_rerank, word_count)

    assert [h.url for h in result] == [NATURE]             # the blog is dropped
    hit = result[0]
    assert (hit.pmcid, hit.page, hit.citation, hit.title) == ("web", 0, "www.nature.com", "Dopamine and Parkinson's")
    assert hit.text == DOPAMINE
    assert firecrawl.calls[0]["json"]["includeDomains"] == loop.WEB_DOMAINS   # Firecrawl is asked to filter too


def test_CR9_web_search_failure_returns_no_hits(monkeypatch):
    monkeypatch.setattr(loop.requests, "post", raising)
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

    assert web_hits("any query", fake_rerank, word_count) == []


def test_CR9_web_source_links_to_its_page_paper_source_unchanged():
    web = Hit("web-0-c0", "web", 0, "Dopamine and Parkinson's", "www.nature.com", "", DOPAMINE, 1.0, NATURE)
    paper = Hit("PMC1-p3-c0", "PMC1", 3, "Title 1", "Citation 1", "CC BY", "Place cells fire at a location.", 0.9)
    blocks = [
        {"type": "text", "text": "Dopamine loss causes the motor symptoms",
         "citations": [{"type": "char_location", "document_index": 0, "cited_text": DOPAMINE}]},
        {"type": "text", "text": ", unlike place cells",
         "citations": [{"type": "char_location", "document_index": 1, "cited_text": "Place cells fire at a location."}]},
        {"type": "text", "text": "."},
    ]
    llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(
        content=blocks, response_metadata={"stop_reason": "end_turn"},
        usage_metadata={"input_tokens": 100, "output_tokens": 20}))

    result = answer("What causes Parkinson's motor symptoms?", [web, paper], llm)

    assert [s.url for s in result.sources] == [NATURE, "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/"]


def test_CR9_two_web_pages_are_two_sources():
    pages = [Hit(f"web-{n}-c0", "web", 0, f"Page {n}", "en.wikipedia.org", "", f"Fact {n}.", 1.0,
                 f"https://en.wikipedia.org/wiki/P{n}") for n in range(2)]
    blocks = [{"type": "text", "text": f"Fact {n}",
               "citations": [{"type": "char_location", "document_index": n, "cited_text": f"Fact {n}."}]}
              for n in range(2)]
    llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(
        content=blocks, response_metadata={"stop_reason": "end_turn"},
        usage_metadata={"input_tokens": 100, "output_tokens": 20}))

    result = answer("Two facts?", pages, llm)

    assert [s.n for s in result.sources] == [1, 2]          # same pmcid "web" and page 0, still two sources
    assert [s.url for s in result.sources] == [p.url for p in pages]


# --- CR-10: the API returns the path ----------------------------------------------

def test_CR10_api_returns_path_and_used_web():
    search, answer_ = FakeSearch({"clear query 1": "good"}), FakeAnswer()
    client = TestClient(create_app(search, answer_, fake_grade, FakeRewrite(), FakeWeb("good")))

    response = client.post("/ask", json={"question": QUESTION})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == ANSWER.text
    assert body["sources"] == []
    assert body["path"] == ["retrieve", "grade:weak", "rewrite", "retrieve", "grade:good", "generate"]
    assert body["used_web"] is False


def test_CR10_api_web_answer_says_used_web():
    client = TestClient(create_app(FakeSearch({}), FakeAnswer(), fake_grade, FakeRewrite(), FakeWeb("good")))

    body = client.post("/ask", json={"question": QUESTION}).json()

    assert body["path"][-3:] == ["web", "grade:good", "generate"]
    assert body["used_web"] is True


def test_CR10_search_failure_inside_the_loop_is_still_503():
    client = TestClient(create_app(raising, FakeAnswer(), fake_grade, FakeRewrite(), FakeWeb("good")))

    response = client.post("/ask", json={"question": QUESTION})

    assert response.status_code == 503
    assert response.json() == {"detail": SEARCH_DOWN}
