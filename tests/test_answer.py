from types import SimpleNamespace

from langchain_core.messages import HumanMessage, SystemMessage

from neuro_rag.generation.answer import NOT_FOUND, REFUSED, SYSTEM, Citation, Source, answer, make_llm
from neuro_rag.retrieval.search import Hit

PLACE = "Place cells in the hippocampus fire when the animal is at a specific location."
GRID = "Grid cells in the entorhinal cortex fire in a hexagonal pattern across space."
FIELD = "Each place cell has its own place field, the spot where it fires most."

HITS = [
    Hit("PMC1-p3-c0", "PMC1", 3, "Title 1", "Citation 1", "CC BY", PLACE, 0.9),
    Hit("PMC2-p7-c0", "PMC2", 7, "Title 2", "Citation 2", "CC BY", GRID, 0.8),
    Hit("PMC1-p3-c1", "PMC1", 3, "Title 1", "Citation 1", "CC BY", FIELD, 0.7),
]


def cite(index, text):
    return {"type": "char_location", "document_index": index, "cited_text": text}


BLOCKS = [
    {"type": "text", "text": "Place cells fire at a specific location", "citations": [cite(0, PLACE)]},
    {"type": "text", "text": ", each with its own place field", "citations": [cite(2, FIELD)]},
    {"type": "text", "text": ", while grid cells fire in a hexagonal pattern", "citations": [cite(1, GRID)]},
    {"type": "text", "text": "."},
]


class FakeLLM:
    """Stands in for ChatAnthropic: returns the given blocks, counts calls, records the messages."""

    def __init__(self, content, stop_reason="end_turn", input_tokens=100, output_tokens=20):
        self.content = content
        self.stop_reason = stop_reason
        self.tokens = {"input_tokens": input_tokens, "output_tokens": output_tokens}
        self.calls = 0
        self.messages = None

    def invoke(self, messages):
        self.calls += 1
        self.messages = messages
        return SimpleNamespace(content=self.content, response_metadata={"stop_reason": self.stop_reason},
                               usage_metadata=self.tokens)


def test_CA1_markers_numbered_and_match_sources():
    result = answer("What do place cells and grid cells do?", HITS, FakeLLM(BLOCKS))

    assert result.text == (
        "Place cells fire at a specific location [1], each with its own place field [1], "
        "while grid cells fire in a hexagonal pattern [2]."
    )
    assert result.sources == [
        Source(1, "PMC1", 3, "Title 1", "Citation 1", "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/"),
        Source(2, "PMC2", 7, "Title 2", "Citation 2", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2/"),
    ]


def test_CA2_same_page_shares_one_source():
    result = answer("What do place cells and grid cells do?", HITS, FakeLLM(BLOCKS))

    assert len(result.sources) == 2
    assert result.citations == [
        Citation(1, 0, PLACE),
        Citation(1, 2, FIELD),
        Citation(2, 1, GRID),
    ]


def test_CA3_no_hits_no_call():
    llm = FakeLLM(BLOCKS)

    result = answer("What do place cells do?", [], llm)

    assert result.text == "I couldn't find anything in the papers about this."
    assert result.text == NOT_FOUND
    assert (result.sources, result.citations) == ([], [])
    assert (result.input_tokens, result.output_tokens) == (0, 0)
    assert llm.calls == 0


def test_CA4_refusal_gives_fixed_sentence():
    llm = FakeLLM([], stop_reason="refusal", input_tokens=1200, output_tokens=3)

    result = answer("What do place cells and grid cells do?", HITS, llm)

    assert result.text == "I can't answer this question."
    assert result.text == REFUSED
    assert (result.sources, result.citations) == ([], [])
    assert (result.input_tokens, result.output_tokens) == (1200, 3)


def test_CA5_request_sends_documents_in_order():
    llm = FakeLLM(BLOCKS)
    question = "What do place cells and grid cells do?"

    answer(question, HITS, llm)

    system, human = llm.messages
    assert isinstance(system, SystemMessage) and system.content == SYSTEM
    assert isinstance(human, HumanMessage)
    documents, last = human.content[:3], human.content[3]
    assert len(human.content) == 4
    assert [d["type"] for d in documents] == ["document"] * 3
    assert [d["source"]["data"] for d in documents] == [PLACE, GRID, FIELD]
    assert documents[0]["title"] == "Title 1, page 3"
    assert documents[0]["citations"] == {"enabled": True}
    assert last == {"type": "text", "text": question}
    assert make_llm().model == "claude-haiku-4-5"


def test_CA6_heading_lines_removed():
    blocks = [{"type": "text", "text": "# Place cells\n"}] + BLOCKS

    result = answer("What do place cells and grid cells do?", HITS, FakeLLM(blocks))

    assert result.text == (
        "Place cells fire at a specific location [1], each with its own place field [1], "
        "while grid cells fire in a hexagonal pattern [2]."
    )
    assert not any(line.lstrip().startswith("#") for line in result.text.splitlines())
