"""Row 9, choice 18: the ground-truth labels for comparing graders, from a three-model jury.

For each of the 50 English eval questions, row 8's search is re-run (dense top 20,
reranked, top 5), and three frontier models from three providers each decide whether
those 5 chunks contain the information needed to answer the question. The majority is
the label. Votes are saved as they come, so a crashed run resumes where it stopped.
Paid (about $1 for 150 calls, through OpenRouter); needs OPENROUTER_API_KEY in .env
and Qdrant running:

    docker compose up -d qdrant
    python scripts/label_ground_truth.py

Writes eval/ground_truth/votes.jsonl (one line per question and judge) and
eval/ground_truth/labels.jsonl (one line per question: the majority label).
"""
import json
import os
import time
from pathlib import Path

import requests
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient

from neuro_rag.config import EMBED_MODEL, QDRANT_URL, QUESTIONS_PATH, RERANK_MODEL, RESULTS_DIR, SPARSE_MODEL
from neuro_rag.retrieval.search import search

OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
JUDGES = ["openai/gpt-5.6-sol", "~google/gemini-pro-latest", "x-ai/grok-4.7"]   # three providers, no Anthropic
ROW8_RUN = RESULTS_DIR / "2026-11-18_2157_rerank" / "runs.jsonl"
OUT_DIR = Path(__file__).parents[1] / "eval" / "ground_truth"
VOTES = OUT_DIR / "votes.jsonl"
LABELS = OUT_DIR / "labels.jsonl"
WITH_REFERENCE = {"answer_from_corpus", "correct_premise"}   # the other kinds' references give the answer away
TRIES = 3                                                    # attempts per call before it is recorded as failed

# the judges' instructions, fixed before any vote is seen
PROMPT = """You are building ground truth for a retrieval system over neuroscience papers.

Decide whether the passages below contain the information needed to answer the question well.
- "good": the passages contain the information needed to answer the question, fully or in its main points.
- "weak": they do not (off-topic, only loosely related, or missing the key facts).
If the question rests on a false premise, passages that show the premise is wrong count as "good":
the system should answer by correcting it.
Judge the passages only, not your own knowledge.{reference}

Question: {question}

Passages:
{passages}

Reply with JSON only: {{"label": "good" or "weak", "reason": "one sentence"}}"""

REFERENCE = """
A reference answer written for this question is given to help you; the passages need to support its main points.

Reference answer: {reference}"""


def load_questions() -> list[dict]:
    """The 50 English eval questions: those in row 8's run, with their kind and reference answer.

    Row 8's runs.jsonl has the 50 questions that are run (the 4 non-English ones are
    not); eval/questions.jsonl has every question's reference_answer. The two are
    joined on "id".

    Returns: e.g. [{"id": "q01", "question": "How does m6A...", "kind":
    "answer_from_corpus", "reference": "The m6A reader Ythdf1...", "chunk_ids":
    [...row 8's 5 chunk ids...]}, ...], 50 long, in row 8's order.
    """
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        references = {q["id"]: q.get("reference_answer") or "" for q in map(json.loads, f)}
    with open(ROW8_RUN, encoding="utf-8") as f:
        runs = [json.loads(line) for line in f]
    return [{"id": r["id"], "question": r["question"], "kind": r["expected_behavior"],
             "reference": references[r["id"]], "chunk_ids": r["chunk_ids"]} for r in runs]


def build_prompt(q: dict, hits) -> str:
    """Fills PROMPT for one question and its hits.

    The hits' texts are numbered [1]..[5], as the graders see them. The reference
    answer is added only for answer_from_corpus and correct_premise questions
    (WITH_REFERENCE) and only if it is not empty: for decline and web_fallback
    questions the reference says things like "Not covered by the hippocampus corpus",
    which would hand the judge the label.

    Returns: the full prompt text.
    """
    passages = "\n\n".join(f"[{i}] {hit.text}" for i, hit in enumerate(hits, start=1))
    reference = REFERENCE.format(reference=q["reference"]) if q["kind"] in WITH_REFERENCE and q["reference"] else ""
    return PROMPT.format(reference=reference, question=q["question"], passages=passages)


def ask(judge: str, prompt: str, key: str) -> dict:
    """Sends the prompt to one judge through OpenRouter and returns its vote.

    One POST to OpenRouter's OpenAI-style chat endpoint with: model=judge; the prompt as
    one user message; response_format json_object (the reply must be a JSON object);
    max_tokens 4000 (room for the model's hidden reasoning before the short JSON);
    usage.include=true (OpenRouter then reports the call's cost in dollars). No
    temperature: GPT-5.6 doesn't accept one.
    The reply's content is parsed as JSON; "label" must be "good" or "weak". Tried up
    to TRIES times, 5 s apart, on a network error, a non-200 answer or an unreadable
    reply; after that the vote is recorded with label None and the error.

    Returns: e.g. {"label": "good", "reason": "Passage [3] states...", "model":
    "google/gemini-3.5-pro" (what the alias resolved to), "cost": 0.0061, "error": None}.
    """
    body = {"model": judge, "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}, "max_tokens": 4000, "usage": {"include": True}}
    error = None
    for _ in range(TRIES):
        try:
            response = requests.post(OPENROUTER, json=body, timeout=180,
                                     headers={"Authorization": f"Bearer {key}"})
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            vote = json.loads(content)
            if vote.get("label") not in ("good", "weak"):
                raise ValueError(f"label {vote.get('label')!r}")
            return {"label": vote["label"], "reason": vote.get("reason", ""), "model": data.get("model"),
                    "cost": (data.get("usage") or {}).get("cost"), "error": None}
        except (requests.RequestException, KeyError, ValueError) as e:   # json errors are ValueErrors
            error = str(e)[:300]
            time.sleep(5)
    return {"label": None, "reason": "", "model": None, "cost": None, "error": error}


def done_votes() -> set[tuple[str, str]]:
    """The (question id, judge) pairs already in votes.jsonl with a label, so a rerun skips them.

    Failed votes (label None) are not counted as done: a rerun tries them again.
    Returns: e.g. {("q01", "openai/gpt-5.6-sol"), ...}; empty if the file doesn't exist yet.
    """
    if not VOTES.exists():
        return set()
    with open(VOTES, encoding="utf-8") as f:
        return {(v["id"], v["judge"]) for v in map(json.loads, f) if v["label"] is not None}


def majority(questions: list[dict]) -> list[dict]:
    """Turns votes.jsonl into one label per question, and writes labels.jsonl.

    For each question, the latest successful vote of each judge is used. The label is
    the one at least 2 judges gave; "unanimous" says whether all 3 agreed. A question
    with fewer than 2 matching votes (judges failed) gets label None and is reported.

    Returns: e.g. [{"id": "q12", "label": "good", "unanimous": False, "votes":
    {"openai/gpt-5.6-sol": "good", ...}}, ...].
    """
    latest = {}
    with open(VOTES, encoding="utf-8") as f:
        for v in map(json.loads, f):
            if v["label"] is not None:
                latest[(v["id"], v["judge"])] = v["label"]
    rows = []
    for q in questions:
        votes = {j: latest.get((q["id"], j)) for j in JUDGES}
        given = [v for v in votes.values() if v]
        label = next((x for x in ("good", "weak") if given.count(x) >= 2), None)
        rows.append({"id": q["id"], "kind": q["kind"], "label": label,
                     "unanimous": len(given) == 3 and len(set(given)) == 1, "votes": votes})
    with open(LABELS, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return rows


def main():
    """Re-runs row 8's search, collects the missing votes, then writes and summarises the labels.

    1. Reads the key from the environment (.env is loaded by neuro_rag.config);
       stops with a message if it is missing. The key is never printed.
    2. For each question: search; a warning if the hits differ from row 8's; then
       every judge that has no successful vote yet is asked, and its vote is appended
       to votes.jsonl at once (with the hits' chunk ids and the prompt's kind).
    3. majority() writes labels.jsonl; prints the label counts, how many were
       unanimous, each judge's agreement with the majority, the questions whose label
       differs from the row 8 proxy, failed votes, and the total cost.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key or key == "your-openrouter-key-here":
        raise SystemExit("OPENROUTER_API_KEY is not set in .env")

    client = QdrantClient(url=QDRANT_URL)
    embed = TextEmbedding(EMBED_MODEL).embed
    sparse_embed = SparseTextEmbedding(SPARSE_MODEL).query_embed
    rerank = TextCrossEncoder(RERANK_MODEL).rerank

    questions = load_questions()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = done_votes()
    for q in questions:
        todo = [j for j in JUDGES if (q["id"], j) not in done]
        if not todo:
            continue
        hits = search(q["question"], client, embed, sparse_embed, rerank=rerank)
        if [h.chunk_id for h in hits] != q["chunk_ids"]:
            print(f"  {q['id']}: hits differ from row 8's")
        prompt = build_prompt(q, hits)
        for judge in todo:
            vote = ask(judge, prompt, key)
            with open(VOTES, "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": q["id"], "judge": judge, **vote,
                                    "chunk_ids": [h.chunk_id for h in hits]}) + "\n")
            print(f"{q['id']} {q['kind']:<18} {judge:<28} {vote['label'] or 'FAILED: ' + str(vote['error'])}")

    rows = majority(questions)
    labelled = [r for r in rows if r["label"]]
    print(f"\n{len(labelled)}/{len(rows)} labelled: "
          f"{sum(r['label'] == 'good' for r in labelled)} good, {sum(r['label'] == 'weak' for r in labelled)} weak; "
          f"{sum(r['unanimous'] for r in rows)} unanimous")
    for judge in JUDGES:
        agree = sum(r["votes"][judge] == r["label"] for r in labelled)
        print(f"  {judge:<28} agrees with the majority on {agree}/{len(labelled)}")
    missing = [r["id"] for r in rows if not r["label"]]
    if missing:
        print(f"no majority (failed votes), rerun to retry: {missing}")

    with open(VOTES, encoding="utf-8") as f:
        cost = sum(v["cost"] or 0 for v in map(json.loads, f))
    print(f"total cost so far ${cost:.3f}")
    print(f"wrote {LABELS}")


if __name__ == "__main__":
    main()
