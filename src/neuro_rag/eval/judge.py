"""The LLM judge: correctness against a reference, faithfulness against cited chunks (EV-8, EV-9).

Verdicts come back as structured JSON, so they always parse. Judge model: decision 004.
"""
import json
from dataclasses import dataclass

import anthropic

from neuro_rag.config import LLM_EFFORT, LLM_MODEL

CORRECTNESS_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["correct", "partial", "wrong"]},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "reason"],
    "additionalProperties": False,
}
FAITHFULNESS_SCHEMA = {
    "type": "object",
    "properties": {
        "faithful": {"type": "boolean"},
        "unsupported_claim": {"type": "string"},
    },
    "required": ["faithful", "unsupported_claim"],
    "additionalProperties": False,
}

CORRECTNESS_PROMPT = """You grade an answer to a neuroscience question against a reference answer.

Question: {question}

Reference answer: {reference}

Answer to grade: {answer}

Ignore citation markers like [1]. Grade only what the answer claims:
- "correct": it states the reference's key findings and contradicts none of them.
- "partial": what it states is consistent with the reference, but it misses a key finding.
- "wrong": it contradicts the reference, or says the question can't be answered.
Give the verdict and one sentence saying why (what is missing or wrong, if anything)."""

FAITHFULNESS_PROMPT = """You check whether an answer says only what its cited sources say.

Answer: {answer}

Cited sources, by marker:
{sources}

The answer is faithful if every factual claim followed by a marker like [n] is supported by the text of source [n],
and it makes no factual claim that no cited source supports. Sentences saying what the sources don't cover are fine.
Give faithful true or false. If false, quote the first unsupported claim; if true, give an empty string."""


class JudgeError(Exception):
    """The judge call failed; the run is kept without a verdict (EV-10)."""


@dataclass(frozen=True)
class Correctness:
    verdict: str  # correct | partial | wrong
    reason: str


@dataclass(frozen=True)
class Faithfulness:
    faithful: bool
    unsupported_claim: str


class Judge:
    def __init__(self, client: anthropic.Anthropic | None = None, model: str = LLM_MODEL, effort: str = LLM_EFFORT):
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort

    def correctness(self, question: str, reference: str, answer: str) -> Correctness:
        data = self._ask(CORRECTNESS_PROMPT.format(question=question, reference=reference, answer=answer),
                         CORRECTNESS_SCHEMA)
        return Correctness(data["verdict"], data["reason"])

    def faithfulness(self, answer: str, cited: dict[int, list[str]]) -> Faithfulness:
        """`cited`: marker number -> the texts of the chunks that marker cites."""
        sources = "\n\n".join(f"[{n}] " + "\n".join(texts) for n, texts in sorted(cited.items()))
        data = self._ask(FAITHFULNESS_PROMPT.format(answer=answer, sources=sources), FAITHFULNESS_SCHEMA)
        return Faithfulness(data["faithful"], data["unsupported_claim"])

    def _ask(self, prompt: str, schema: dict) -> dict:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as e:
            raise JudgeError(f"judge call failed: {e}") from e
        if response.stop_reason == "refusal":
            raise JudgeError("judge refused")
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise JudgeError(f"judge reply isn't JSON: {text[:100]!r}") from e
