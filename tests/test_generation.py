"""Unit tests for specs/generation/spec.md: a fake Claude client, no API calls. Named after the criteria."""
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from neuro_rag.generation.generate import NOT_FOUND, REFUSED, GenerationError, Generator
from neuro_rag.retrieval.retrieve import Retrieved

PLACE = "Place cells in the hippocampus fire when the animal is at a specific location."
GRID = "Grid cells in the entorhinal cortex fire in a hexagonal pattern across space."
PLACE_FIELD = "Each place cell has its own place field, the spot where it fires most."


def chunk(text, pmcid, page):
    return Retrieved(f"{pmcid}-p{page}-c0", text, pmcid, f"Title of {pmcid}", f"Citation of {pmcid}", "CC BY",
                     page, 0.5)


def text_block(text, *cited):
    """A response text block citing the chunks at the given indexes."""
    citations = [SimpleNamespace(type="char_location", document_index=i, cited_text=f"quote {i}") for i in cited]
    return SimpleNamespace(type="text", text=text, citations=citations or None)


def response(*blocks, stop_reason="end_turn"):
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason,
                           usage=SimpleNamespace(input_tokens=1200, output_tokens=80))


class FakeClaude:
    """Returns `reply`, or raises `error`; records every call."""

    def __init__(self, reply=None, error=None):
        self.calls = []
        self.reply, self.error = reply, error
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.reply


def generate(reply, chunks, question="What do place cells and grid cells do?"):
    return Generator(FakeClaude(reply)).answer(question, chunks)


def test_GN2_markers_and_source_list_match():
    chunks = [chunk(PLACE, "PMC1", 3), chunk(GRID, "PMC2", 7)]
    reply = response(text_block("Place cells fire at a specific location.", 0),
                     text_block(" Grid cells fire in a hexagonal pattern.", 1))

    answer = generate(reply, chunks)

    assert answer.text == "Place cells fire at a specific location. [1] Grid cells fire in a hexagonal pattern. [2]"
    assert [(s.n, s.pmcid, s.page) for s in answer.sources] == [(1, "PMC1", 3), (2, "PMC2", 7)]
    assert answer.sources[0].title == "Title of PMC1"
    assert answer.sources[0].citation == "Citation of PMC1"
    assert answer.sources[0].url == "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/"


def test_GN3_two_chunks_from_one_page_share_one_source():
    chunks = [chunk(PLACE, "PMC1", 3), chunk(PLACE_FIELD, "PMC1", 3)]
    reply = response(text_block("Place cells fire at a location.", 0),
                     text_block(" Each has its own place field.", 1))

    answer = generate(reply, chunks, "What are place cells?")

    assert answer.text == "Place cells fire at a location. [1] Each has its own place field. [1]"
    assert len(answer.sources) == 1
    assert [c.chunk_index for c in answer.citations] == [0, 1]


def test_GN7_no_chunks_means_no_call():
    claude = FakeClaude()

    answer = Generator(claude).answer("What do place cells do?", [])

    assert answer.text == NOT_FOUND
    assert answer.sources == []
    assert claude.calls == []


def test_GN8_headings_are_removed():
    chunks = [chunk(PLACE, "PMC1", 3)]
    reply = response(text_block("# Place cells\nPlace cells fire at a specific location.", 0))

    answer = generate(reply, chunks)

    assert not any(line.lstrip().startswith("#") for line in answer.text.splitlines())
    assert answer.text == "Place cells fire at a specific location. [1]"


def test_GN9_claude_unavailable_gives_clear_error():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    for error in [anthropic.APIConnectionError(request=request),
                  anthropic.InternalServerError("overloaded", response=httpx2.Response(529, request=request),
                                                body=None)]:
        with pytest.raises(GenerationError, match="Claude is unavailable"):
            Generator(FakeClaude(error=error)).answer("What do place cells do?", [chunk(PLACE, "PMC1", 3)])


def test_GN10_refusal_gives_clear_message():
    answer = generate(response(stop_reason="refusal"), [chunk(PLACE, "PMC1", 3)])

    assert answer.text == REFUSED
    assert answer.sources == []


def test_GN11_usage_is_returned():
    answer = generate(response(text_block("Place cells fire.", 0)), [chunk(PLACE, "PMC1", 3)])
    assert (answer.usage.input_tokens, answer.usage.output_tokens) == (1200, 80)


def test_each_chunk_is_sent_as_a_citable_document():
    """Supports GN-1: what reaches Claude is one document per chunk, with citations on (decision 003)."""
    claude = FakeClaude(response(text_block("Place cells fire.", 0)))

    Generator(claude).answer("What do place cells do?", [chunk(PLACE, "PMC1", 3), chunk(GRID, "PMC2", 7)])

    content = claude.calls[0]["messages"][0]["content"]
    assert [c["type"] for c in content] == ["document", "document", "text"]
    assert content[0]["source"]["data"] == PLACE
    assert content[0]["citations"] == {"enabled": True}
    assert content[0]["title"] == "Title of PMC1, page 3"
    assert content[2]["text"] == "What do place cells do?"
