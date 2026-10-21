"""Rewrite a question into a search query in the papers' words, in English.

Spec: docs/specs/correction/spec.md, "How it is built" (CR-1 to CR-10).
"""
import json
import re

import anthropic

from neuro_rag.config import LLM_EFFORT, LLM_MODEL

PROMPT = """You rewrite a user's question into a search query for a collection of scientific papers on the hippocampus and memory.

Rules:
- Write the query in English, whatever language the question is in.
- Replace everyday words with the terms the papers would use (for example "fear center" becomes "amygdala").
- Keep every specific term from the question unchanged: gene and protein names, brain regions, species, methods.
- Keep the question's meaning. Don't answer it, don't add claims, and don't narrow it to one hypothesis.
- Write one line, at most 30 words: a short question or phrase.

Examples:
Question: why do I keep forgetting where I put my keys?
Query: everyday forgetting of object locations; spatial memory retrieval and the hippocampus

Question: Est-ce que le stress abîme la mémoire ?
Query: effects of chronic stress on memory and hippocampal function

Question: {question}"""

REWRITE_SCHEMA = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
    "additionalProperties": False,
}

MAX_WORDS = 60


class RewriteError(Exception):
    """No usable query: the call failed, was refused, or the reply is empty, unreadable or too long."""


class Rewriter:
    def __init__(self, client: anthropic.Anthropic | None = None, model: str = LLM_MODEL,
                 effort: str = LLM_EFFORT):
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort

    def rewrite(self, question: str) -> str:
        prompt = PROMPT.format(question=question)  # step 1
        try:  # step 2
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": REWRITE_SCHEMA}},
            )
        except anthropic.APIError as e:  # step 3
            raise RewriteError(f"rewrite call failed: {e}") from e
        if response.stop_reason == "refusal":  # step 4
            raise RewriteError("rewriter refused")
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:  # step 5
            query = json.loads(text)["query"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise RewriteError(f"rewriter reply isn't JSON: {text[:100]!r}") from e
        query = re.sub(r"\s+", " ", query).strip()  # step 6
        if not query:  # step 7
            raise RewriteError("rewrite is empty")
        words = len(query.split(" "))
        if words > MAX_WORDS:
            raise RewriteError(f"rewrite is {words} words, more than {MAX_WORDS}")
        return query  # step 8
