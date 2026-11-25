"""Row 10, choice 24: which model should decide "on topic?", and at which cut.

Scores the 90 questions of eval/topic/labels.jsonl (jury labels, scripts/label_topic.py;
none from the eval) with each candidate, all asked the same question (graders.TOPIC_QUESTION):

  jev      Jev through OpenRouter (graders.on_topic, what row 10 ships today); P(yes)
  haiku    Claude Haiku 4.5, "yes"/"no" -> 1.0 / 0.0 (no probabilities from Anthropic's API)
  laya     Laya on the local llama.cpp server (docker compose service laya); P(yes)
  gemma1b  Gemma 3 1B on the local llama.cpp server (service gemma1b); P(yes) from logprobs

Each score becomes a decision at each cut in CUTS: decline if score < cut, else keep.
Counted per model and cut, against the jury label:
  - false declines: label keep, decided decline (the costly mistake: no answer at all);
  - missed: label decline, decided keep (the mild one: the loop's slow path);
  - accuracy, median and p95 seconds a call.
A failing call counts as "keep" (the API never declines because a service is down)
and is reported.

The rule (spec choice 24, fixed before any result): fewest false declines; then fewest
missed; then lower median latency; then lower cost. Applied to every (model, cut) pair.

    docker compose --profile graders up -d laya gemma1b     # only for the local models
    python scripts/compare_topic.py                         # all four
    python scripts/compare_topic.py --models jev haiku      # a subset

Writes eval/results/<date>_topic_compare/scores.csv (one row per question and model) and
table.csv (one row per model and cut), and prints the table and the choice.
"""
import argparse
import csv
import json
import math
import statistics
import time
from datetime import datetime
from pathlib import Path

import requests
from langchain_anthropic import ChatAnthropic

from neuro_rag.config import GEMMA_URL, LAYA_URL, LLM_MODEL, RESULTS_DIR
from neuro_rag.crag.graders import NO, TIMEOUT, TOPIC_QUESTION, YES, on_topic

LABELS = Path(__file__).parents[1] / "eval" / "topic" / "labels.jsonl"
CUTS = [0.2, 0.3, 0.5]                     # 0.2 is row 10's current cut; 0.5 is the even-odds cut
COST = {"gemma1b": 0, "laya": 0, "jev": 1, "haiku": 2}   # tie-break order only: free, ~$0.000002, ~$0.0001
HAIKU = ChatAnthropic(model=LLM_MODEL, max_tokens=10, temperature=0, timeout=60)
ASK = f"Question: {{question}}\n\n{TOPIC_QUESTION} Answer yes or no."
# Haiku only: with max_tokens=5 and no format instruction its replies were cut to
# "# Answer\n\n**Yes" (first run, 2026-11-25), counted as "no"; the question is unchanged
HAIKU_ASK = ASK + " Reply with only the word yes or no."


def haiku_topic(question: str) -> float:
    """Haiku's yes/no: 1.0 for yes, 0.0 for no (so every cut gives the same decision).

    The reply's first word that is "yes" or "no", after dropping markdown and
    punctuation (e.g. "**Yes**", "Yes."), decides; neither word found raises
    ValueError, which score_all records as an error (counted as keep).
    """
    reply = str(HAIKU.invoke(HAIKU_ASK.format(question=question)).content).lower()
    for word in "".join(c if c.isalpha() else " " for c in reply).split():
        if word in ("yes", "no"):
            return 1.0 if word == "yes" else 0.0
    raise ValueError(f"no yes/no in reply: {reply[:60]!r}")


def laya_topic(question: str) -> float:
    """Laya's P(yes) for TOPIC_QUESTION: the same "noul" request as on_topic, to the local server."""
    body = {"state": f"Question: {question}",
            "questions": {"on_topic": {"type": "noul", "instructions": TOPIC_QUESTION}}}
    response = requests.post(f"{LAYA_URL}/v1/systemone", json=body, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["answers"]["on_topic"]["noul"]


def gemma_topic(question: str) -> float:
    """Gemma 3 1B's P(yes): one token, top 5 logprobs, yes spellings / (yes + no), as gemma_grader."""
    body = {"messages": [{"role": "user", "content": ASK.format(question=question)}],
            "max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 5}
    response = requests.post(f"{GEMMA_URL}/v1/chat/completions", json=body, timeout=TIMEOUT)
    response.raise_for_status()
    top = response.json()["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    yes = sum(math.exp(t["logprob"]) for t in top if t["token"].strip() in YES)
    no = sum(math.exp(t["logprob"]) for t in top if t["token"].strip() in NO)
    return yes / (yes + no) if yes + no else 0.0


MODELS = {"jev": on_topic, "haiku": haiku_topic, "laya": laya_topic, "gemma1b": gemma_topic}


def score_all(rows: list[dict], names: list[str]) -> list[dict]:
    """Every model scores every question, timed; a failure is recorded as score None.

    Returns one dict per question and model: {"id", "question", "label", "model",
    "score" (float or None), "seconds", "error" (str or None)}.
    """
    out = []
    for r in rows:
        for name in names:
            start = time.perf_counter()
            try:
                score, error = MODELS[name](r["question"]), None
            except Exception as e:                     # counted, the run goes on
                score, error = None, str(e)[:200]
                print(f"  {r['id']} {name}: {error}")
            out.append({"id": r["id"], "question": r["question"], "label": r["label"], "model": name,
                        "score": score, "seconds": round(time.perf_counter() - start, 3), "error": error})
        print(f"{r['id']} {r['label']:<7} " + "  ".join(
            f"{o['model']}={o['score'] if o['score'] is None else round(o['score'], 2)}" for o in out[-len(names):]))
    return out


def summarise(scores: list[dict], names: list[str]) -> list[dict]:
    """One row per (model, cut): false declines, missed, accuracy, latency, errors.

    A None score (failed call) counts as keep. e.g. {"model": "jev", "cut": 0.2, "n": 90,
    "false_declines": 1, "missed": 4, "accuracy": 0.944, "median_s": 0.31, "p95_s": 0.52,
    "errors": 0, "declined_keeps": "t47"}.
    """
    table = []
    for name in names:
        mine = [s for s in scores if s["model"] == name]
        secs = sorted(s["seconds"] for s in mine)
        for cut in CUTS:
            decide = {s["id"]: "decline" if s["score"] is not None and s["score"] < cut else "keep" for s in mine}
            fd = [s["id"] for s in mine if s["label"] == "keep" and decide[s["id"]] == "decline"]
            missed = [s["id"] for s in mine if s["label"] == "decline" and decide[s["id"]] == "keep"]
            table.append({
                "model": name, "cut": cut, "n": len(mine),
                "false_declines": len(fd), "missed": len(missed),
                "accuracy": round(1 - (len(fd) + len(missed)) / len(mine), 3),
                "median_s": round(statistics.median(secs), 2),
                "p95_s": secs[max(0, math.ceil(0.95 * len(secs)) - 1)],
                "errors": sum(s["error"] is not None for s in mine),
                "declined_keeps": " ".join(fd), "missed_declines": " ".join(missed),
            })
    return table


def choose(table: list[dict]) -> dict:
    """The rule: fewest false declines, then fewest missed, then lower median latency, then lower cost."""
    return min(table, key=lambda r: (r["false_declines"], r["missed"], r["median_s"], COST[r["model"]]))


def main():
    """Loads the jury labels, scores, writes scores.csv and table.csv, prints the table and the choice."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", choices=list(MODELS), default=list(MODELS))
    args = parser.parse_args()
    if not LABELS.exists():
        raise SystemExit(f"{LABELS} missing: run scripts/label_topic.py first")
    rows = [r for r in map(json.loads, LABELS.open(encoding="utf-8")) if r["label"]]

    scores = score_all(rows, args.models)
    table = summarise(scores, args.models)
    out = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_topic_compare"
    out.mkdir(parents=True, exist_ok=False)
    for path, data in ((out / "scores.csv", scores), (out / "table.csv", table)):
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)

    print(f"\n{len(rows)} questions: {sum(r['label'] == 'keep' for r in rows)} keep, "
          f"{sum(r['label'] == 'decline' for r in rows)} decline (jury labels)")
    print(f"{'model':<8} {'cut':>4} {'false decl':>10} {'missed':>6} {'accuracy':>8} {'median s':>8} {'p95 s':>6} {'errors':>6}")
    for r in table:
        print(f"{r['model']:<8} {r['cut']:>4} {r['false_declines']:>10} {r['missed']:>6} {r['accuracy']:>8} "
              f"{r['median_s']:>8} {r['p95_s']:>6} {r['errors']:>6}")
    best = choose(table)
    print(f"\nchosen by the rule: {best['model']} at cut {best['cut']} "
          f"(false declines {best['false_declines']}: {best['declined_keeps'] or '-'}; "
          f"missed {best['missed']}: {best['missed_declines'] or '-'})")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
