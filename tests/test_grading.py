"""Unit tests for specs/grading/spec.md: a fake Claude client; no models, no Qdrant."""
import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from neuro_rag.grading.grade import GRADE_SCHEMA, Grade, Grader, GradingError
from neuro_rag.retrieval.retrieve import Retrieved

PLACE = "Place cells in the hippocampus fire when the animal is at a specific location."
GRID = "Grid cells in the entorhinal cortex fire in a hexagonal pattern across space."


def chunks(*texts):
    return [Retrieved(f"PMC1-p1-c{i}", t, "PMC1", "Title", "Citation", "CC BY", 1, 0.0) for i, t in enumerate(texts)]


def reply(verdicts, stop_reason="end_turn"):
    text = json.dumps({"verdicts": [{"passage": n, "relevant": r} for n, r in verdicts]})
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], stop_reason=stop_reason)


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


def test_GR1_request_asks_one_verdict_per_numbered_passage():
    claude = FakeClaude(reply([(1, True), (2, False)]))

    Grader(claude).grade("What do place cells do?", chunks(PLACE, GRID))

    assert len(claude.calls) == 1
    call = claude.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["thinking"] == {"type": "disabled"}
    assert call["output_config"] == {"effort": "low", "format": {"type": "json_schema", "schema": GRADE_SCHEMA}}
    prompt = call["messages"][0]["content"]
    assert "Question: What do place cells do?" in prompt
    assert f'<passage n="1">\n{PLACE}\n</passage>' in prompt
    assert f'<passage n="2">\n{GRID}\n</passage>' in prompt
    assert prompt.index('<passage n="1">') < prompt.index('<passage n="2">')


def test_GR2_verdicts_become_positions_in_order():
    claude = FakeClaude(reply([(2, True), (1, False), (3, True)]))

    result = Grader(claude).grade("question", chunks("a", "b", "c"))

    assert result == Grade(passed=True, relevant=[1, 2])


def test_GR3_no_relevant_passage_fails():
    claude = FakeClaude(reply([(1, False), (2, False)]))

    assert Grader(claude).grade("question", chunks("a", "b")) == Grade(passed=False, relevant=[])


def test_GR4_no_chunks_fail_without_a_call():
    claude = FakeClaude()

    assert Grader(claude).grade("question", []) == Grade(passed=False, relevant=[])
    assert claude.calls == []


@pytest.mark.parametrize("numbers", [[1, 2, 3, 4], [1, 2, 2, 4, 5], [1, 2, 3, 4, 5, 7]])
def test_GR5_mismatched_reply_is_an_error(numbers):
    claude = FakeClaude(reply([(n, True) for n in numbers]))

    with pytest.raises(GradingError, match=r"don't match the 5 passages: got " + str(numbers).replace("[", r"\[")):
        Grader(claude).grade("question", chunks("a", "b", "c", "d", "e"))


def test_GR6_failed_or_refused_call_is_an_error():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    down = FakeClaude(error=anthropic.APIConnectionError(request=request))
    refused = FakeClaude(reply([], stop_reason="refusal"))

    with pytest.raises(GradingError, match="grading call failed"):
        Grader(down).grade("question", chunks("a"))
    with pytest.raises(GradingError, match="grader refused"):
        Grader(refused).grade("question", chunks("a"))
