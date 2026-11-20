"""Row 9's graders: is what retrieval found good enough to answer the question from?

Each grader takes the question and the hits and returns a number in [0, 1], the
probability that the hits contain the information needed (see docs/specs/crag/spec.md,
phase 1). Compared locally by scripts/compare_graders.py; only the winner ships.
"""
import math                                   # math.exp: logprob -> probability

import requests                               # HTTP calls to the local llama.cpp server

from neuro_rag.config import GEMMA_URL        # http://localhost:8081 locally; an env var so k8s can override it
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
