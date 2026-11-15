import pytest
from fastapi.testclient import TestClient

from neuro_rag.api.app import ANSWER_DOWN, SEARCH_DOWN, create_app
from neuro_rag.generation.answer import Answer, Citation, Source
from neuro_rag.retrieval.search import Hit

HIT = Hit("PMC1-p3-c0", "PMC1", 3, "Title 1", "Citation 1", "CC BY", "Place cells fire at one location.", 0.9)

ANSWER = Answer(
    text="Place cells fire at one location [1].",
    sources=[Source(1, "PMC1", 3, "Title 1", "Citation 1", "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/")],
    citations=[Citation(1, 0, "Place cells fire at one location.")],
    input_tokens=1000,
    output_tokens=100,
)


class FakeSearch:
    """Stands in for search: the same single hit for every question, no Qdrant.
    calls: every question it was given, in order."""

    def __init__(self):
        self.calls = []

    def __call__(self, question):  # lets the object be called like a function
        self.calls.append(question)
        return [HIT]


class FakeAnswer:
    """Stands in for answer: the same fixed ANSWER every time, no API call.
    calls: every (question, hits) it was given, in order."""

    def __init__(self):
        self.calls = []

    def __call__(self, question, hits):
        self.calls.append((question, hits))
        return ANSWER


def test_AP1_answer_and_sources_as_json():
    client = TestClient(create_app(FakeSearch(), FakeAnswer()))

    response = client.post("/ask", json={"question": "What do place cells do?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Place cells fire at one location [1].",
        "sources": [{
            "n": 1, "pmcid": "PMC1", "page": 3, "title": "Title 1", "citation": "Citation 1",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/",
        }],
    }


def test_AP2_question_stripped_and_hits_passed():
    search, answer = FakeSearch(), FakeAnswer()
    client = TestClient(create_app(search, answer))
    client.post("/ask", json={"question": " What do place cells do?"})
    assert search.calls == ["What do place cells do?"]
    assert answer.calls == [("What do place cells do?", [HIT])]


@pytest.mark.parametrize("body", [
    {"question": ""},             # empty
    {"question": "   "},          # only spaces: empty once stripped
    {"question": "a" * 1001},     # over 1000 characters
    {},                           # no question
    {"question": 42},             # not a string
])
def test_AP3_bad_question_422_nothing_searched(body):
    search = FakeSearch()
    client = TestClient(create_app(search, FakeAnswer()))

    response = client.post("/ask", json=body)

    assert response.status_code == 422
    assert search.calls == []


def test_AP3_question_of_1000_characters_accepted():
    client = TestClient(create_app(FakeSearch(), FakeAnswer()))

    response = client.post("/ask", json={"question": "a" * 1000})

    assert response.status_code == 200


def test_AP4_search_failure_503():
    def failing_search(question):
        raise ConnectionError("[Errno 61] Connection refused: localhost:6333")

    answer = FakeAnswer()
    client = TestClient(create_app(failing_search, answer))

    response = client.post("/ask", json={"question": "What do place cells do?"})

    assert response.status_code == 503
    assert response.json() == {"detail": SEARCH_DOWN}
    assert "6333" not in response.text
    assert answer.calls == []


def test_AP5_answer_failure_503():
    def failing_answer(question, hits):
        raise RuntimeError("anthropic: 529 overloaded")

    client = TestClient(create_app(FakeSearch(), failing_answer))

    response = client.post("/ask", json={"question": "What do place cells do?"})

    assert response.status_code == 503
    assert response.json() == {"detail": ANSWER_DOWN}


def test_AP6_health_calls_nothing():
    search, answer = FakeSearch(), FakeAnswer()
    client = TestClient(create_app(search, answer))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert search.calls == []
    assert answer.calls == []
