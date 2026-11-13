from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from neuro_rag.generation.answer import Answer
from neuro_rag.retrieval.search import Hit

CORRECTNESS_PROMPT = """You grade an answer to a neuroscience question against a reference answer written by an expert.

- correct: the answer states the reference's main findings and contradicts none of them. Different wording and extra true detail are fine.
- partial: the answer states some of the reference's main findings and contradicts none, but misses at least one.
- wrong: the answer contradicts the reference, answers a different question, or says the papers don't cover it.

Judge the content only, not the style or the citations. Give the verdict and one sentence saying why."""

FAITHFULNESS_PROMPT = """You check whether an answer is supported by the sources it cites. The sources are numbered as in the answer.

- faithful: every claim in the answer is stated in, or follows directly from, the text of a source it cites.
- unfaithful: at least one claim is not in the sources it cites. Quote the first such claim.

Use only the source texts given, not your own knowledge."""


class Correctness(BaseModel):
    verdict: Literal["correct", "partial", "wrong"]
    reason: str


class Faithfulness(BaseModel):
    faithful: bool
    unsupported_claim: str

   

def judge_correctness(question: str, reference: str, answer_text: str, llm)-> tuple[Correctness, int, int]:
    text = f"Question: {question}\n\nReference answer: {reference}\n\nAnswer to grade: {answer_text}"
    out = llm.with_structured_output(Correctness, include_raw=True).invoke(
            [SystemMessage(CORRECTNESS_PROMPT), HumanMessage(text)]
        )
    input_tokens = out["raw"].usage_metadata["input_tokens"]
    output_tokens = out["raw"].usage_metadata["output_tokens"]
    if out["parsed"] is None:
        raise ValueError(f"judge reply didn't parse: {out['parsing_error']}")
    return out["parsed"], input_tokens, output_tokens

    


def judge_faithfulness(result: Answer, hits: list[Hit], llm) -> tuple[Faithfulness, int, int]:
    by_n = {}
    for c in result.citations:
        by_n.setdefault(c.n, set()).add(c.hit_index)
    sources = "\n".join(
        f"[{n}] " + " … ".join(hits[i].text for i in sorted(indexes))
        for n, indexes in sorted(by_n.items())
    )
    text = f"Answer: {result.text}\n\nSources:\n{sources}"
    out = llm.with_structured_output(Faithfulness, include_raw=True).invoke(
            [SystemMessage(FAITHFULNESS_PROMPT), HumanMessage(text)]
        )
    input_tokens = out["raw"].usage_metadata["input_tokens"]
    output_tokens = out["raw"].usage_metadata["output_tokens"]
    if out["parsed"] is None:
        raise ValueError(f"judge reply didn't parse: {out['parsing_error']}")
    return out["parsed"], input_tokens, output_tokens


