"""Row 9, phase 1 (CR-3): the graders on the 50 eval questions, and the one chosen.

For each eval question: row 8's search (dense top 20, reranked, top 5) is run again,
every grader scores those 5 hits, and the decision (good if score >= CUT) is compared
with the question's label taken from row 8's eval run (spec, "Labels"). Prints one
table row per grader and the grader chosen by the spec's rule; writes the per-question
scores and the table to eval/results/<timestamp>_graders/. Free: everything runs
locally. Needs Qdrant and each grader's server running:

    docker compose up -d qdrant
    docker compose --profile graders up -d gemma1b laya
    python scripts/compare_graders.py                    # every grader
    python scripts/compare_graders.py --graders haiku    # only some (names in GRADERS)

The Haiku grader is paid (about $0.0011 a grade, about $0.05 for the 44 questions)
and needs ANTHROPIC_API_KEY in .env.
"""
import argparse
import csv
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from langchain_anthropic import ChatAnthropic
from qdrant_client import QdrantClient

from neuro_rag.config import EMBED_MODEL, LLM_MODEL, QDRANT_URL, RERANK_MODEL, RESULTS_DIR, SPARSE_MODEL
from neuro_rag.crag.graders import CUT, gemma_grader, haiku_grader, laya_grader
from neuro_rag.retrieval.search import search

# row 8's eval run: the labels come from its verdicts, and its chunk_ids are checked
# against today's search so we know the grader sees the same hits row 8 answered from
ROW8_RUN = RESULTS_DIR / "2026-11-18_2157_rerank" / "runs.jsonl"

# Haiku for grading: a few output tokens ("Yes"/"No"), temperature 0. Building it makes
# no API call; the key is read from .env when the first grade is sent.
HAIKU = ChatAnthropic(model=LLM_MODEL, max_tokens=5, temperature=0)

# the graders compared: name -> (function (question, hits) -> float, RAM in MB on the VM
# for the tie-break, cost a grade as shown in the table).
GRADERS = {
    "gemma1b": (gemma_grader, 800, "$0"),
    "laya": (laya_grader, 450, "$0"),
    "haiku": (lambda question, hits: haiku_grader(question, hits, HAIKU), 0, "~$0.0011"),
}

CLOSE = 0.05    # spec rule: another grader within this accuracy of the best, with fewer
                # "weak judged good" mistakes, is preferred


def label(run: dict) -> str | None:
    """The row 8 label of one eval question: "good", "weak", or None (left out).

    From the spec's "Labels" section, using the question's row in ROW8_RUN:
      - "good": expected_behavior is answer_from_corpus or correct_premise, and the
        correctness judge said "correct" or "partial" (the papers could answer it);
      - "weak": the same kinds judged "wrong", plus every "decline" (off-domain, e.g.
        sourdough) and "web_fallback" (neuroscience outside the papers) question;
      - None: "not_declined" (borderline) questions, which have no verdict.
    A proxy: a wrong answer may be the generation's fault, not retrieval's, but every
    grader is scored on the same labels.

    Returns: e.g. "good". On row 8's run: 32 good, 12 weak, 6 left out.
    """
    kind = run["expected_behavior"]
    if kind in ("decline", "web_fallback"):
        return "weak"
    if kind in ("answer_from_corpus", "correct_premise"):
        verdict = (run.get("correctness") or {}).get("verdict")
        return "good" if verdict in ("correct", "partial") else "weak"
    return None


def load_runs(path: Path = ROW8_RUN) -> list[dict]:
    """Reads row 8's runs.jsonl (one JSON object per line, one per eval question).

    Each object has, among others, "id" ("q01"), "question", "expected_behavior",
    "chunk_ids" (the 5 hits row 8 answered from, e.g. "PMC6226095-p6-c1") and
    "correctness" ({"verdict": "correct", ...}, or null for decline questions).

    Returns: the 50 dicts, in file order.
    """
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def grade_all(runs: list[dict], search_fn, names: list[str]) -> list[dict]:
    """Runs search once per labelled question, then the graders in `names` on those hits.

    For each question with a label (left-out ones are skipped):
      1. search_fn(question) gives the 5 hits; whether their chunk_ids equal row 8's
         is recorded as same_hits (should be true: search is deterministic and the
         index hasn't changed; if not, that question's label may not fit its hits);
      2. each grader in GRADERS is called and timed (time.perf_counter); its score
         becomes a decision, "good" if score >= CUT else "weak";
      3. a grader that raises (llama.cpp server down or timed out, Anthropic error)
         gets score None and decision "error" for that question, and the run goes on.

    Returns: one dict per (question, grader), e.g.
    {"id": "q01", "label": "good", "grader": "gemma1b", "score": 0.998,
     "decision": "good", "seconds": 4.1, "same_hits": True}.
    """
    rows = []
    for run in runs:
        gold = label(run)
        if gold is None:
            continue
        hits = search_fn(run["question"])
        same_hits = [h.chunk_id for h in hits] == run["chunk_ids"]
        for name in names:
            grader = GRADERS[name][0]
            start = time.perf_counter()
            try:
                score = grader(run["question"], hits)
                decision = "good" if score >= CUT else "weak"
            except Exception as e:                      # any failure: counted, the run goes on
                score, decision = None, "error"
                print(f"  {run['id']} {name}: {e}")
            seconds = time.perf_counter() - start
            rows.append({"id": run["id"], "label": gold, "grader": name,
                         "score": None if score is None else round(score, 4),
                         "decision": decision, "seconds": round(seconds, 2), "same_hits": same_hits})
            print(f"{run['id']} {gold:<4} {name}: {decision:<5} {score if score is None else round(score, 3)} "
                  f"({seconds:.1f} s)")
    return rows


def summarise(rows: list[dict], names: list[str]) -> list[dict]:
    """One summary per grader, over the questions it answered (errors counted apart).

    - accuracy: share of questions where decision == label;
    - weak_judged_good: label weak, decision good, the costly mistake (Claude answers
      from chunks that can't support the answer);
    - good_judged_weak: label good, decision weak (a needless rewrite or web search);
    - errors: questions where the grader raised;
    - median_s: median seconds per grade;
    - ram_mb and cost: from GRADERS (cost: $0 for local graders, an estimate for Haiku).

    Returns: e.g. [{"grader": "gemma1b", "n": 44, "accuracy": 0.82,
    "weak_judged_good": 3, "good_judged_weak": 5, "errors": 0, "median_s": 4.1,
    "ram_mb": 800, "cost": "$0"}].
    """
    table = []
    for name in names:
        _, ram_mb, cost = GRADERS[name]
        mine = [r for r in rows if r["grader"] == name]
        done = [r for r in mine if r["decision"] != "error"]
        table.append({
            "grader": name,
            "n": len(done),
            "accuracy": round(sum(r["decision"] == r["label"] for r in done) / len(done), 3) if done else 0.0,
            "weak_judged_good": sum(r["label"] == "weak" and r["decision"] == "good" for r in done),
            "good_judged_weak": sum(r["label"] == "good" and r["decision"] == "weak" for r in done),
            "errors": len(mine) - len(done),
            "median_s": round(statistics.median(r["seconds"] for r in done), 2) if done else None,
            "ram_mb": ram_mb,
            "cost": cost,
        })
    return table


def choose(table: list[dict]) -> str:
    """The spec's rule ("Choosing the grader"): the most accurate grader, unless another
    is within CLOSE (0.05) of it with fewer weak_judged_good mistakes; a remaining tie
    goes to the one using less RAM.

    Steps: take the best accuracy; keep every grader within CLOSE of it; among those,
    the fewest weak_judged_good wins; if still tied, the smallest ram_mb.
    Returns: the chosen grader's name, e.g. "gemma1b".
    """
    best = max(row["accuracy"] for row in table)
    close = [row for row in table if row["accuracy"] >= best - CLOSE]
    return min(close, key=lambda row: (row["weak_judged_good"], row["ram_mb"]))["grader"]


def main():
    """Builds row 8's search, grades every labelled question, prints and saves the table.

    The search is built exactly as in api/app.py's build_pipeline (dense, top 20
    reranked to 5), without the LLM: no Claude call, nothing paid.
    --graders picks which graders run (default: all in GRADERS).
    Writes eval/results/<YYYY-MM-DD_HHMM>_graders/scores.csv (one row per question and
    grader) and table.csv (one row per grader).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--graders", nargs="+", choices=list(GRADERS), default=list(GRADERS))
    names = parser.parse_args().graders

    client = QdrantClient(url=QDRANT_URL)
    embed = TextEmbedding(EMBED_MODEL).embed
    sparse_embed = SparseTextEmbedding(SPARSE_MODEL).query_embed
    rerank = TextCrossEncoder(RERANK_MODEL).rerank

    def search_fn(question):
        return search(question, client, embed, sparse_embed, rerank=rerank)

    rows = grade_all(load_runs(), search_fn, names)
    table = summarise(rows, names)

    out = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_graders"
    out.mkdir(parents=True)
    for name, data in (("scores.csv", rows), ("table.csv", table)):
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)

    questions = len({r["id"] for r in rows})
    differ = len({r["id"] for r in rows if not r["same_hits"]})
    print(f"\n{questions} labelled questions; hits differ from row 8's on {differ}")
    print(f"{'grader':<10} {'n':>3} {'accuracy':>8} {'weak→good':>9} {'good→weak':>9} {'errors':>6} "
          f"{'median s':>8} {'RAM MB':>6}  cost a grade")
    for row in table:
        print(f"{row['grader']:<10} {row['n']:>3} {row['accuracy']:>8} {row['weak_judged_good']:>9} "
              f"{row['good_judged_weak']:>9} {row['errors']:>6} {str(row['median_s']):>8} {row['ram_mb']:>6}  {row['cost']}")
    print(f"chosen: {choose(table)}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
