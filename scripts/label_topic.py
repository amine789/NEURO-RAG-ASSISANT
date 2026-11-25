"""Row 10, choice 24: ground-truth labels for comparing on-topic checks, from a three-model jury.

Each of the 90 questions in eval/topic/questions.jsonl (none from the eval) is shown
to the same three frontier models as the grader jury (choice 18), from three providers,
none from Anthropic, through OpenRouter. Each says whether a neuroscience and memory
assistant should answer the question ("keep") or decline it as out of scope
("decline"). The majority is the label. The file holds only ids and questions, in a
shuffled order: no group or hint of the writer's intent, so the labels are the judges'
alone. Split votes (2-1) are listed for a human look. Votes are saved as they come, so a
crashed run resumes.

Paid (about $0.30 for 270 short calls); needs OPENROUTER_API_KEY in .env:

    python scripts/label_topic.py

Writes eval/topic/votes.jsonl (one line per question and judge) and
eval/topic/labels.jsonl (one line per question: the majority label).
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

import neuro_rag.config  # noqa: F401  (loads .env)

ROOT = Path(__file__).parents[1]
QUESTIONS = ROOT / "eval" / "topic" / "questions.jsonl"
VOTES = ROOT / "eval" / "topic" / "votes.jsonl"
LABELS = ROOT / "eval" / "topic" / "labels.jsonl"

OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
JUDGES = ["openai/gpt-5.6-sol", "~google/gemini-pro-latest", "x-ai/grok-4.7"]   # as choice 18
TRIES = 3

# the judges' instructions, fixed before any vote is seen (spec choice 24)
PROMPT = """You are building ground truth for a question-answering assistant.

The assistant answers questions about neuroscience, the brain, the nervous system, memory, learning, sleep and behaviour, for students, researchers and curious members of the public. Everyday questions about how the mind and brain work (memory, attention, sleep, stress, habits) are in scope. Questions about other topics, including medicine that is not about the brain or nervous system, are out of scope.

Should the assistant answer this question, or decline it as out of scope?
- "keep": in scope, the assistant should answer it.
- "decline": out of scope, the assistant should politely decline.

Question: {question}

Reply with JSON only: {{"label": "keep" or "decline", "reason": "one sentence"}}"""


def ask(judge: str, question: str, key: str) -> dict:
    """One judge's vote on one question, through OpenRouter's chat endpoint.

    Same call as label_ground_truth.ask: model=judge, the prompt as one user message,
    response_format json_object, max_tokens 4000 (room for hidden reasoning before the
    short JSON), usage.include=true (OpenRouter reports the cost). The reply is parsed as
    JSON; "label" must be "keep" or "decline". Up to TRIES attempts, 5 s apart, on a
    network error, a non-200 or an unreadable reply; after that the vote is recorded
    with label None and the error. Connect timeout 5 s, read 180 s (see graders.TIMEOUT).

    Returns: e.g. {"label": "decline", "reason": "Statins are cardiovascular...",
      "model": "x-ai/grok-4.7", "cost": 0.0011, "error": None}.
    """
    body = {"model": judge, "messages": [{"role": "user", "content": PROMPT.format(question=question)}],
            "response_format": {"type": "json_object"}, "max_tokens": 4000, "usage": {"include": True}}
    error = None
    for _ in range(TRIES):
        try:
            response = requests.post(OPENROUTER, json=body, timeout=(5, 180),
                                     headers={"Authorization": f"Bearer {key}"})
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            vote = json.loads(content)
            if vote.get("label") not in ("keep", "decline"):
                raise ValueError(f"label {vote.get('label')!r}")
            return {"label": vote["label"], "reason": vote.get("reason", ""), "model": data.get("model"),
                    "cost": (data.get("usage") or {}).get("cost"), "error": None}
        except (requests.RequestException, KeyError, ValueError) as e:
            error = str(e)[:300]
            time.sleep(5)
    return {"label": None, "reason": "", "model": None, "cost": None, "error": error}


def main():
    """Collects the missing votes, then writes the majority labels and prints a summary.

    1. Reads the key (never printed); stops if it is missing.
    2. For each question, every judge without a successful vote in votes.jsonl is
       asked; each vote is appended at once (so a rerun skips it).
    3. labels.jsonl: per question, the label at least 2 judges gave, "unanimous" and
       the votes. Prints the counts, each judge's agreement with the majority, the
       split (2-1) questions for a human look, failed votes and the total cost.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key or key == "your-openrouter-key-here":
        raise SystemExit("OPENROUTER_API_KEY is not set in .env")

    questions = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    done = set()
    if VOTES.exists():
        done = {(v["id"], v["judge"]) for v in map(json.loads, VOTES.open(encoding="utf-8")) if v["label"]}

    for q in questions:
        for judge in JUDGES:
            if (q["id"], judge) in done:
                continue
            vote = ask(judge, q["question"], key)
            with VOTES.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"id": q["id"], "judge": judge, **vote}) + "\n")
            print(f"{q['id']} {judge:<28} {vote['label'] or 'FAILED: ' + str(vote['error'])}")
            sys.stdout.flush()

    latest = {}
    for v in map(json.loads, VOTES.open(encoding="utf-8")):
        if v["label"]:
            latest[(v["id"], v["judge"])] = v["label"]
    rows = []
    for q in questions:
        votes = {j: latest.get((q["id"], j)) for j in JUDGES}
        given = [v for v in votes.values() if v]
        label = next((x for x in ("keep", "decline") if given.count(x) >= 2), None)
        rows.append({"id": q["id"], "question": q["question"], "label": label,
                     "unanimous": len(given) == 3 and len(set(given)) == 1, "votes": votes})
    with LABELS.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    labelled = [r for r in rows if r["label"]]
    print(f"\n{len(labelled)}/{len(rows)} labelled: {sum(r['label'] == 'keep' for r in labelled)} keep, "
          f"{sum(r['label'] == 'decline' for r in labelled)} decline; {sum(r['unanimous'] for r in rows)} unanimous")
    for judge in JUDGES:
        print(f"  {judge:<28} agrees with the majority on {sum(r['votes'][judge] == r['label'] for r in labelled)}/{len(labelled)}")
    split = [r for r in labelled if not r["unanimous"]]
    print(f"split votes ({len(split)}): look at these")
    for r in split:
        print(f"  {r['id']} -> {r['label']:<7} {r['votes']}  {r['question']}")
    missing = [r["id"] for r in rows if not r["label"]]
    if missing:
        print(f"no majority (failed votes), rerun to retry: {missing}")
    cost = sum(v["cost"] or 0 for v in map(json.loads, VOTES.open(encoding="utf-8")))
    print(f"total cost so far ${cost:.3f}\nwrote {LABELS}")


if __name__ == "__main__":
    main()
