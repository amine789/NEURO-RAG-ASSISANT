"""Row 9's graders: is what retrieval found good enough to answer the question from?

Each grader takes the question and the hits and returns a number in [0, 1], the
probability that the hits contain the information needed (see docs/specs/crag/spec.md,
phase 1). Compared locally by scripts/compare_graders.py; only the winner ships.
"""
import math                                   # math.exp: logprob -> probability
import os                                     # OPENROUTER_API_KEY for jev_grader

import requests                               # HTTP calls to the local llama.cpp server

from neuro_rag.config import GEMMA_URL, LAYA_URL   # localhost:8081 / :8082 locally; env vars so k8s can override them
from neuro_rag.retrieval.search import Hit    # what search() returns: .text is the chunk

CUT = 0.5            # good if P(yes) >= CUT; fixed, never fitted on the eval (spec choice 2)
TIMEOUT = 60         # seconds per grade call; a slow CPU prompt (~1,100 tokens) can take ~10 s

# The grading prompt, fixed before any result is seen (spec, "Keeping the test set clean").
# {passages} is the 5 hits' texts, numbered [1]..[5]; {question} the user's question.
PROMPT = (
    "Passages:\n{passages}\n\n"
    "Question: {question}\n\n"
    "Do these passages contain the information needed to answer the question? "
    "Answer yes or no."
)

# First-token spellings counted as yes / no: the smoke test showed "Yes" and "yes"
# (and "No", "no") all in the top 5, so each side's probabilities are summed.
YES = {"yes", "Yes", "YES"}
NO = {"no", "No", "NO"}


def gemma_grader(question: str, hits: list[Hit], url: str = GEMMA_URL) -> float:
    """G2: asks a local Gemma whether the hits can answer the question; returns P(yes).

    Steps:
      1. The hits' texts are numbered "[1] ...", "[2] ..." and put into PROMPT with the
         question.
      2. One POST to llama.cpp's OpenAI-style endpoint <url>/v1/chat/completions with:
         messages = the prompt as one user message; max_tokens=1 (only the first
         token, "Yes" or "No", is needed); temperature=0 (no sampling randomness);
         logprobs=true and top_logprobs=5 (the 5 likeliest first tokens with their
         log-probabilities, not just the one picked).
      3. From choices[0].logprobs.content[0].top_logprobs, every token that is a
         spelling of yes (YES) or no (NO), after stripping spaces (" Yes" counts), has
         its logprob turned into a probability with exp and added to its side.
         Smoke test: Yes 0.92 + yes 0.02 = 0.94 yes; No 0.06 + no 0.0004 = 0.06 no.
      4. The two sides are normalised: P(yes) = yes / (yes + no), so the other tokens
         in the top 5 (e.g. "но" at 0.00003) don't shrink the score.

    The model is whichever one the server at `url` serves: Gemma 3 1B at
    GEMMA_URL (localhost:8081, docker-compose service gemma1b).

    Args: question, the user's question; hits, the retrieved chunks (only .text is
    used; normally 5); url, the llama.cpp server's base address.
    Returns: a float in [0, 1], e.g. 0.94; compare with CUT (>= 0.5 means good).
    0.0 if no yes/no spelling is in the top 5 (the model answered something else),
    so an unclear answer counts as weak retrieval: the safe side, it leads to a
    rewrite, not to answering from bad chunks.
    Raises: requests.RequestException (server down, timeout after TIMEOUT s, non-200
    answer via raise_for_status). Not caught here: the loop catches it and degrades
    (spec CR-8), and compare_graders.py counts it.
    """
    passages = "\n\n".join(f"[{i}] {hit.text}" for i, hit in enumerate(hits, start=1))
    body = {
        "messages": [{"role": "user", "content": PROMPT.format(passages=passages, question=question)}],
        "max_tokens": 1,
        "temperature": 0,
        "logprobs": True,
        "top_logprobs": 5,
    }
    response = requests.post(f"{url}/v1/chat/completions", json=body, timeout=TIMEOUT)
    response.raise_for_status()
    top = response.json()["choices"][0]["logprobs"]["content"][0]["top_logprobs"]

    yes = sum(math.exp(t["logprob"]) for t in top if t["token"].strip() in YES)
    no = sum(math.exp(t["logprob"]) for t in top if t["token"].strip() in NO)
    if yes + no == 0:
        return 0.0
    return yes / (yes + no)


def haiku_grader(question: str, hits: list[Hit], llm) -> float:
    """Haiku as grader: the same PROMPT as gemma_grader, sent to Claude; returns 1.0 or 0.0.

    Steps:
      1. The hits are numbered and put into PROMPT exactly as in gemma_grader, so the
         two graders see the same text.
      2. llm.invoke(prompt) sends it to Claude Haiku 4.5 through LangChain's
         ChatAnthropic (the project's rule for LLM calls). `llm` is built by the caller,
         e.g. ChatAnthropic(model="claude-haiku-4-5", max_tokens=5, temperature=0):
         a few output tokens are enough for "Yes" or "No".
      3. The reply's text is stripped of spaces and punctuation and lower-cased;
         "yes..." gives 1.0, anything else 0.0.

    Unlike llama.cpp, Anthropic's API returns no log-probabilities, so there is no
    confidence: the score is 1.0 or 0.0, and CUT (0.5) just reads it as good / weak.
    Paid: about 1,100 input tokens and 1 output token, roughly $0.0011 a grade.

    Args: question; hits (only .text is used); llm, a ChatAnthropic (or a fake in tests).
    Returns: 1.0 if Claude answered yes, else 0.0 (an answer that isn't a clear yes
    counts as weak, the safe side, as in gemma_grader).
    Raises: whatever the Anthropic client raises (no key, rate limit, network); not
    caught here: the loop catches it (spec CR-8), compare_graders.py counts it.
    """
    passages = "\n\n".join(f"[{i}] {hit.text}" for i, hit in enumerate(hits, start=1))
    reply = llm.invoke(PROMPT.format(passages=passages, question=question))
    text = reply.content.strip().strip(".!").lower()
    return 1.0 if text.startswith("yes") else 0.0


# Laya's question: the yes/no part of PROMPT, word for word, so all graders are asked the same thing
LAYA_QUESTION = "Do these passages contain the information needed to answer the question?"


def laya_grader(question: str, hits: list[Hit], url: str = LAYA_URL) -> float:
    """G3: asks Laya, a local decision model, whether the hits can answer the question.

    Laya is not a chat model: it is a classifier (a BERT-style encoder with a decision
    head) that answers typed questions about a "state" in one forward pass, with no
    text generated. llama.cpp serves it at /v1/systemone (TypeSafe-compatible API).

    Steps:
      1. The state is one string: "Question: <question>" then "Passages:" and the
         hits' texts numbered [1]..[5], the same content gemma_grader sends.
      2. One POST to <url>/v1/systemone with
         {"state": <that string>,
          "questions": {"good": {"type": "noul", "instructions": LAYA_QUESTION}}}.
         "noul" is the yes/no question type.
      3. The answer is {"answers": {"good": {"type": "noul", "noul": 0.87}}, ...}:
         "noul" is the probability that the answer is yes (true), already in [0, 1],
         so it is returned as is.

    Laya was trained with a token budget: llama.cpp truncates long inputs to it, so
    with 5 chunks of about 200 tokens the last passages may be cut. compare_graders.py
    measures what that costs.

    Args: question; hits (only .text is used); url, the Laya server's base address.
    Returns: P(yes) in [0, 1], e.g. 0.87; compare with CUT.
    Raises: requests.RequestException (server down, timeout after TIMEOUT s, non-200);
    not caught here: the loop catches it (spec CR-8), compare_graders.py counts it.
    """
    passages = "\n\n".join(f"[{i}] {hit.text}" for i, hit in enumerate(hits, start=1))
    body = {
        "state": f"Question: {question}\n\nPassages:\n{passages}",
        "questions": {"good": {"type": "noul", "instructions": LAYA_QUESTION}},
    }
    response = requests.post(f"{url}/v1/systemone", json=body, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["answers"]["good"]["noul"]


OPENROUTER_SYSTEMONE = "https://openrouter.ai/api/v1/systemone"   # OpenRouter's decision-model endpoint
JEV_MODEL = "typesafe/jev-1.14"    # pinned, not ~typesafe/jev-latest: the version graded is the version shipped


def jev_grader(question: str, hits: list[Hit], model: str = JEV_MODEL) -> float:
    """Jev (TypeSafe's hosted decision model) through OpenRouter; returns P(yes).

    Same idea and same request as laya_grader: Jev is a decision model, answering typed
    questions about a "state" with probabilities and no generated text. OpenRouter
    serves decision models at /api/v1/systemone, the same TypeSafe-compatible API
    llama.cpp serves Laya with, plus a "model" field and an API key.

    Steps:
      1. The state is "Question: <question>" then "Passages:" and the hits' texts
         numbered [1]..[5], exactly as in laya_grader.
      2. One POST to OPENROUTER_SYSTEMONE with the header
         "Authorization: Bearer <OPENROUTER_API_KEY>" (from .env, never printed) and
         {"model": "typesafe/jev-1.14", "state": ...,
          "questions": {"good": {"type": "noul", "instructions": LAYA_QUESTION}}}.
      3. The answer is {"answers": {"good": {"type": "noul", "noul": 0.87}}, ...};
         "noul" is P(yes), returned as is.

    Paid but tiny: $0.042 per million input tokens, so about $0.00004 for a grade of
    about 850 tokens (the Haiku grader costs about 25 times more).

    Args: question; hits (only .text is used); model, the OpenRouter model id.
    Returns: P(yes) in [0, 1]; compare with CUT.
    Raises: KeyError if OPENROUTER_API_KEY is not set; requests.RequestException
    (network, timeout after TIMEOUT s, non-200 such as 402 when the account has no
    credit); not caught here: the loop catches it (spec CR-8), compare_graders.py
    counts it.
    """
    passages = "\n\n".join(f"[{i}] {hit.text}" for i, hit in enumerate(hits, start=1))
    body = {
        "model": model,
        "state": f"Question: {question}\n\nPassages:\n{passages}",
        "questions": {"good": {"type": "noul", "instructions": LAYA_QUESTION}},
    }
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}
    response = requests.post(OPENROUTER_SYSTEMONE, json=body, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["answers"]["good"]["noul"]
