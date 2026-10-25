"""Run the eval: retrieve -> generate (or Pipeline.ask) -> measure in code -> judge (EV-1 to EV-10, EV-15 to EV-19).

    python -m neuro_rag.eval.run                              # all 54 questions, 3 repeats
    python -m neuro_rag.eval.run --ids q01,q51 --repeats 1    # a quick dry run
    python -m neuro_rag.eval.run --rerank --name rerank       # with the reranker (EV-14)
    python -m neuro_rag.eval.run --corrective --name corrective  # rerank + grade + rewrite (EV-15)
    python -m neuro_rag.eval.run --out eval/results/<folder>  # resume an interrupted run

Then: python -m neuro_rag.eval.report eval/results/<folder>
"""
import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from datetime import datetime
from pathlib import Path

from neuro_rag import config

QUESTIONS_PATH = config.PROJECT_ROOT / "eval" / "questions.jsonl"
RESULTS_DIR = config.PROJECT_ROOT / "eval" / "results"

PRICE_IN, PRICE_OUT = config.PRICE_IN, config.PRICE_OUT
# Rough tokens per call, for the estimate before a run (EV-4); real usage is recorded per run.
EST_ANSWER = (3000, 400)
EST_JUDGE = (1500, 150)
EST_GRADE = (3000, 80)
EST_REWRITE = (500, 40)

JUDGED_FOR_CORRECTNESS = {"answer_from_corpus", "correct_premise"}
NOT_COVERED_TYPES = {"off_domain", "out_of_corpus"}


@dataclass(frozen=True)
class Question:
    id: str
    type: str
    expected_behavior: str
    question: str
    reference_answer: str | None
    expected_pmcids: frozenset[str]


def load_questions(path: Path = QUESTIONS_PATH) -> list[Question]:
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return [Question(r["id"], r["type"], r["expected_behavior"], r["question"], r.get("reference_answer"),
                     frozenset(s["pmcid"] for s in r.get("expected_sources") or [])) for r in rows]


def base_type(question_type: str) -> str:
    """'off_domain_casual' -> 'off_domain'; used to pick which measures apply."""
    for t in NOT_COVERED_TYPES:
        if question_type.startswith(t):
            return t
    return question_type


def estimate_cost(questions: list[Question], repeats: int, corrective: bool = False) -> tuple[int, float]:
    """Number of runs and their rough cost in dollars: one answer and up to two judge calls each.

    A corrective run is estimated on its most expensive path: two answers, two grades, one rewrite.
    """
    runs = len(questions) * repeats
    calls = [EST_ANSWER, EST_JUDGE, EST_JUDGE]
    if corrective:
        calls += [EST_ANSWER, EST_GRADE, EST_GRADE, EST_REWRITE]
    per_run = sum(i for i, _ in calls) * PRICE_IN + sum(o for _, o in calls) * PRICE_OUT
    return runs, runs * per_run


def system_meta(rerank: bool, corrective: bool = False) -> dict:
    """What the run measured, written to meta.json so a comparison can't be read backwards (EV-14, EV-15)."""
    if corrective:
        return {"system": "rerank + grade + rewrite (row 7a)", "system_model": config.LLM_MODEL,
                "judge_model": config.LLM_MODEL, "reranker": config.RERANK_MODEL,
                "grader_model": config.LLM_MODEL, "rewriter_model": config.LLM_MODEL}
    meta = {"system": "baseline + rerank" if rerank else "baseline (retrieve -> generate)",
            "system_model": config.LLM_MODEL, "judge_model": config.LLM_MODEL}
    if rerank:
        meta["reranker"] = config.RERANK_MODEL
    return meta


class CountingClient:
    """Wraps an Anthropic client and adds up every call's tokens (EV-17). One per run."""

    def __init__(self, client):
        self.client, self.lock = client, threading.Lock()
        self.messages = self  # so Generator, Grader and Rewriter can call client.messages.create(...)
        self.calls = self.input_tokens = self.output_tokens = 0

    def create(self, **kwargs):
        response = self.client.messages.create(**kwargs)
        with self.lock:  # grade, rewrite and generate call it from different threads
            self.calls += 1
            self.input_tokens += response.usage.input_tokens
            self.output_tokens += response.usage.output_tokens
        return response


def _record(q: Question, repeat: int) -> dict:
    return {"id": q.id, "type": q.type, "expected_behavior": q.expected_behavior, "repeat": repeat,
            "question": q.question, "error": None, "judge_error": None}


def run_one(q: Question, repeat: int, retriever, generator, judge) -> dict:
    """One question, one repeat: a complete record, even when something fails (EV-2, EV-10)."""
    record = _record(q, repeat)
    try:
        start = time.perf_counter()
        chunks = retriever.retrieve(q.question)
        record["retrieval_s"] = round(time.perf_counter() - start, 3)
        start = time.perf_counter()
        answer = generator.answer(q.question, chunks)
        record["generation_s"] = round(time.perf_counter() - start, 3)
    except Exception as e:
        record["error"] = f"{type(e).__name__}: {e}"
        return record
    return measure(record, q, answer, chunks, judge)


def run_one_corrective(q: Question, repeat: int, make_pipeline, judge, client) -> dict:
    """One question through Pipeline.ask: the same measures, plus path, query, total time, every call (EV-15 to EV-19)."""
    from neuro_rag.observability.tracing import Tracer

    record = _record(q, repeat)
    counter = CountingClient(client)
    pipeline = make_pipeline(counter)  # a new pipeline per run, so the counter holds only this run's calls
    try:
        start = time.perf_counter()
        with Tracer().trace("ask", input=q.question) as trace:  # tracing off: nothing is sent
            outcome = pipeline.ask(q.question, trace)
        total_s = round(time.perf_counter() - start, 3)
    except Exception as e:
        record["error"] = f"{type(e).__name__}: {e}"
        return record
    finally:
        pipeline.pool.shutdown(wait=True)  # background calls end before the counter is read

    measure(record, q, outcome.answer, outcome.chunks, judge)
    record.update(claude_calls=counter.calls, input_tokens=counter.input_tokens, output_tokens=counter.output_tokens,
                  cost_usd=counter.input_tokens * PRICE_IN + counter.output_tokens * PRICE_OUT,
                  path=outcome.path, query=outcome.query, total_s=total_s)
    return record


def measure(record: dict, q: Question, answer, chunks: list, judge) -> dict:
    """The code measures and the judge's verdicts for one answer (EV-5 to EV-10)."""
    cited: dict[int, list[str]] = {}
    for c in answer.citations:
        text = chunks[c.chunk_index].text
        if text not in cited.setdefault(c.n, []):
            cited[c.n].append(text)
    source_pmcids = {s.pmcid for s in answer.sources}
    record.update(
        answer=answer.text,
        sources=[{"n": s.n, "pmcid": s.pmcid, "page": s.page} for s in answer.sources],
        retrieved=[{"chunk_id": c.chunk_id, "pmcid": c.pmcid, "page": c.page} for c in chunks],
        cited_chunks={str(n): texts for n, texts in cited.items()},
        input_tokens=answer.usage.input_tokens,
        output_tokens=answer.usage.output_tokens,
        cost_usd=answer.usage.input_tokens * PRICE_IN + answer.usage.output_tokens * PRICE_OUT,
        # code measures (EV-5 to EV-7); None where a measure doesn't apply
        retrieval_hit=bool(q.expected_pmcids & {c.pmcid for c in chunks}) if q.expected_pmcids else None,
        cites_expected=bool(q.expected_pmcids & source_pmcids) if q.expected_pmcids else None,
        not_covered=not answer.sources if base_type(q.type) in NOT_COVERED_TYPES else None,
        correctness=None, correctness_reason=None, faithful=None, unsupported_claim=None,
    )
    try:
        if q.reference_answer and q.expected_behavior in JUDGED_FOR_CORRECTNESS:
            verdict = judge.correctness(q.question, q.reference_answer, answer.text)
            record.update(correctness=verdict.verdict, correctness_reason=verdict.reason)
        if cited:
            faith = judge.faithfulness(answer.text, cited)
            record.update(faithful=faith.faithful, unsupported_claim=faith.unsupported_claim)
    except Exception as e:
        record["judge_error"] = f"{type(e).__name__}: {e}"
    return record


def finished(runs_path: Path) -> set[tuple[str, int]]:
    """(id, repeat) of runs already written, so a restarted eval skips them (EV-3)."""
    if not runs_path.exists():
        return set()
    with open(runs_path, encoding="utf-8") as f:
        return {(r["id"], r["repeat"]) for r in map(json.loads, filter(str.strip, f))}


def run_eval(questions: list[Question], retriever, generator, judge, out_dir: Path, repeats: int = 3,
             workers: int = 4, meta: dict | None = None, log=print, run=None) -> Path:
    """`run(question, repeat)`, when given, does each run instead of the baseline's run_one (the corrective system)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_path = out_dir / "runs.jsonl"
    meta_path = out_dir / "meta.json"
    if meta and not meta_path.exists():
        meta_path.write_text(json.dumps({**meta, "repeats": repeats, "workers": workers}, indent=2))

    n_runs, cost = estimate_cost(questions, repeats, corrective=run is not None)
    done = finished(runs_path)
    todo = [(q, r) for q in questions for r in range(1, repeats + 1) if (q.id, r) not in done]
    log(f"{n_runs} runs ({len(done)} already done, {len(todo)} to run), "
        f"estimated cost ${cost * len(todo) / max(n_runs, 1):.2f}")  # before any call (EV-4)

    lock = threading.Lock()

    def work(item):
        record = run(*item) if run else run_one(*item, retriever, generator, judge)
        with lock:
            with open(runs_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, record in enumerate(pool.map(work, todo), start=1):
            status = record["error"] or record["judge_error"] or record.get("correctness") or "ok"
            log(f"[{i}/{len(todo)}] {record['id']} #{record['repeat']}: {status}")
    return runs_path


def main() -> None:
    import anthropic
    from qdrant_client import QdrantClient

    from neuro_rag.encoders import Encoders
    from neuro_rag.eval.judge import Judge
    from neuro_rag.correction.rewrite import Rewriter
    from neuro_rag.generation.generate import Generator
    from neuro_rag.grading.grade import Grader
    from neuro_rag.ingest.index import alias_target
    from neuro_rag.orchestration.pipeline import Pipeline
    from neuro_rag.retrieval.rerank import Reranker
    from neuro_rag.retrieval.retrieve import Retriever

    parser = argparse.ArgumentParser(description="Run the eval on the baseline system.")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--ids", help="comma-separated question ids, e.g. q01,q51")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--name", default="baseline", help="added to the results folder name")
    parser.add_argument("--out", type=Path, help="an existing results folder, to resume it")
    parser.add_argument("--rerank", action="store_true", help="rerank the fused chunks with a cross-encoder")
    parser.add_argument("--corrective", action="store_true", help="rerank + grade + rewrite, through Pipeline.ask")
    args = parser.parse_args()

    questions = load_questions()
    if args.ids:
        wanted = set(args.ids.split(","))
        questions = [q for q in questions if q.id in wanted]
    out = args.out or RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_{args.name}"

    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    try:
        meta = {**system_meta(args.rerank, args.corrective), "index": alias_target(client, config.COLLECTION_ALIAS),
                "started": datetime.now().isoformat(timespec="seconds")}
        if args.corrective:
            retriever, reranker = Retriever(client, Encoders()), Reranker()  # the pipeline reranks, as in the API
            retriever.retrieve("hippocampus")  # load the models now, so no run's time includes it
            reranker.score("warm up", ["warm up"])
            make_pipeline = lambda c: Pipeline(retriever, Generator(c), reranker, Grader(c), Rewriter(c))
            judge = Judge()
            run = partial(run_one_corrective, make_pipeline=make_pipeline, judge=judge, client=anthropic.Anthropic())
            run_eval(questions, None, None, judge, out, args.repeats, args.workers, meta, run=run)
        else:
            retriever = Retriever(client, Encoders(), reranker=Reranker() if args.rerank else None)
            retriever.retrieve("hippocampus")  # load the models now, so no run's retrieval time includes it
            run_eval(questions, retriever, Generator(), Judge(), out, args.repeats, args.workers, meta)
    finally:
        client.close()
    print(f"results: {out}\nnext: python -m neuro_rag.eval.report {out}")


if __name__ == "__main__":
    main()
