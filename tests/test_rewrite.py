"""Unit tests for specs/correction/spec.md (rewrite): a fake Claude client; free."""
import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from neuro_rag.correction.rewrite import PROMPT, REWRITE_SCHEMA, Rewriter, RewriteError

FEAR = ("How do the fear center and the memory center keep their rhythms in step "
        "when people form unpleasant memories?")


def reply(text, stop_reason="end_turn"):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], stop_reason=stop_reason)


def query_reply(query):
    return reply(json.dumps({"query": query}))


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


def test_CR1_request_sends_question_with_rules_and_examples():
    claude = FakeClaude(query_reply("amygdala hippocampus theta phase synchrony"))

    Rewriter(claude).rewrite(FEAR)

    assert len(claude.calls) == 1
    call = claude.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["thinking"] == {"type": "disabled"}
    assert call["output_config"] == {"effort": "low", "format": {"type": "json_schema", "schema": REWRITE_SCHEMA}}
    prompt = call["messages"][0]["content"]
    assert prompt == PROMPT.format(question=FEAR)
    assert prompt.rsplit("Question: ", 1)[1] == FEAR


def test_CR2_query_comes_back_as_one_clean_line():
    claude = FakeClaude(query_reply("  amygdala hippocampus\ntheta phase synchrony  "))

    assert Rewriter(claude).rewrite(FEAR) == "amygdala hippocampus theta phase synchrony"


def test_CR3_empty_or_overlong_rewrite_is_an_error():
    with pytest.raises(RewriteError, match=r"^rewrite is empty$"):
        Rewriter(FakeClaude(query_reply("   "))).rewrite(FEAR)
    with pytest.raises(RewriteError, match=r"^rewrite is 74 words, more than 60$"):
        Rewriter(FakeClaude(query_reply(" ".join(["word"] * 74)))).rewrite(FEAR)
    sixty = " ".join(["word"] * 60)
    assert Rewriter(FakeClaude(query_reply(sixty))).rewrite(FEAR) == sixty


def test_CR4_failed_refused_or_unreadable_call_is_an_error():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")

    with pytest.raises(RewriteError, match="^rewrite call failed: "):
        Rewriter(FakeClaude(error=anthropic.APIConnectionError(request=request))).rewrite(FEAR)
    with pytest.raises(RewriteError, match="^rewriter refused$"):
        Rewriter(FakeClaude(reply("", stop_reason="refusal"))).rewrite(FEAR)
    with pytest.raises(RewriteError, match=r"^rewriter reply isn't JSON: 'amygdala hippocampus'$"):
        Rewriter(FakeClaude(reply("amygdala hippocampus"))).rewrite(FEAR)
