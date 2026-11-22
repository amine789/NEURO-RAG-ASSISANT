import json
import time
from datetime import datetime
from pathlib import Path
import argparse

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient

from neuro_rag.config import (EMBED_MODEL, FALLBACK, GRADER, PRICE_IN, PRICE_OUT, QDRANT_URL, QUESTIONS_PATH, RERANK_MODEL,
                              SPARSE_MODEL, RESULTS_DIR, TOPIC_CUT)
from neuro_rag.crag.loop import rewrite, run_loop, web_hits
from neuro_rag.eval.judge import judge_correctness, judge_faithfulness
from neuro_rag.eval.report import build_report
from neuro_rag.generation.answer import Answer, answer, make_llm
from neuro_rag.ingest.chunk import TokenCounter
from neuro_rag.retrieval.search import Hit, search


# every key of a record besides the question's own fields and "error"; None when a run fails
RESULT_KEYS = [
    "chunk_ids", "answer", "sources",
    "paper_hit", "page_hit", "cites_expected", "not_covered", "cites_papers",
    "search_s", "answer_s", "correctness", "faithfulness", "cost_usd",
]
# row 9/10 runs (--crag or --topic) also record these
PIPELINE_KEYS = ["path", "used_web", "rewrites", "total_s"]


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]:
    questions = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [q for q in questions if not q["type"].startswith("multilingual_")]


def measure(question: dict, hits: list[Hit], result: Answer) -> dict:
    m = {"paper_hit": None, "page_hit": None, "cites_expected": None,
         "not_covered": None, "cites_papers": None}

    if question["expected_sources"]:
        papers = {s["pmcid"] for s in question["expected_sources"]}
        pages = {(s["pmcid"], s["page"]) for s in question["expected_sources"]}
        m["paper_hit"] = any(h.pmcid in papers for h in hits)
        m["page_hit"] = any((h.pmcid, h.page) in pages for h in hits)
        m["cites_expected"] = any(s.pmcid in papers for s in result.sources)

    if question["expected_behavior"] in ("decline", "web_fallback"):
        m["not_covered"] = len(result.sources) == 0

    if question["expected_behavior"] == "not_declined":
        m["cites_papers"] = len(result.sources) > 0

    return m


def cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * PRICE_IN + output_tokens * PRICE_OUT) / 1_000_000


def run_one(question: dict, repeat: int, search_fn, answer_fn, llm, pipeline=None) -> dict:
    """One eval run. Without pipeline: row 8's search then answer, timed separately.

    With pipeline (rows 9 and 10, --crag / --topic): pipeline(question text) returns
    (hits, result, path, used_web), where hits are the chunks the answer was written
    from (or the last search's, if there was no answer); the whole call is timed as
    total_s, and the record gains path, used_web, rewrites and total_s. search_s and
    answer_s are then None. The measures and judges run on those hits and that answer.
    """
    # 1. ask the system, timed
    extra = {}
    if pipeline is None:
        t0 = time.perf_counter()
        hits = search_fn(question["question"])
        t1 = time.perf_counter()
        result = answer_fn(question["question"], hits)
        t2 = time.perf_counter()
    else:
        t0 = time.perf_counter()
        hits, result, path, used_web = pipeline(question["question"])
        total = time.perf_counter() - t0
        extra = {"path": path, "used_web": used_web, "rewrites": path.count("rewrite"), "total_s": round(total, 2)}

    # 2. the record: what was asked, what came back, the code measures
    record = {
        "id": question["id"],
        "type": question["type"],
        "expected_behavior": question["expected_behavior"],
        "repeat": repeat,
        "question": question["question"],
        "chunk_ids": [h.chunk_id for h in hits],
        "answer": result.text,
        "sources": [{"n": s.n, "pmcid": s.pmcid, "page": s.page} for s in result.sources],
        **measure(question, hits, result),
        "search_s": round(t1 - t0, 2) if pipeline is None else None,
        "answer_s": round(t2 - t1, 2) if pipeline is None else None,
        **extra,
    }
    input_tokens, output_tokens = result.input_tokens, result.output_tokens

    # 3. correctness, only for questions answered from the papers with a reference
    record["correctness"] = None
    if question["expected_behavior"] in ("answer_from_corpus", "correct_premise") and question["reference_answer"]:
        try:
            verdict, i_tok, o_tok = judge_correctness(question["question"], question["reference_answer"], result.text, llm)
            record["correctness"] = {"verdict": verdict.verdict, "reason": verdict.reason}
            input_tokens += i_tok
            output_tokens += o_tok
        except Exception as e:  # 5. a failed judge loses its verdict, not the run
            record["correctness"] = {"error": str(e)}

    # 4. faithfulness, only when the answer cites something
    record["faithfulness"] = None
    if result.sources:
        try:
            verdict, i_tok, o_tok = judge_faithfulness(result, hits, llm)
            record["faithfulness"] = {"faithful": verdict.faithful, "unsupported_claim": verdict.unsupported_claim}
            input_tokens += i_tok
            output_tokens += o_tok
        except Exception as e:
            record["faithfulness"] = {"error": str(e)}

    # 6. cost of the answer plus the judges
    record["cost_usd"] = round(cost(input_tokens, output_tokens), 6)
    record["error"] = None
    return record


def run_eval(questions: list[dict], repeats: int, out_dir: Path, search_fn, answer_fn, llm, pipeline=None) -> list[dict]:
    total = len(questions) * repeats
    print(f"{total} runs, estimated ${total * 0.005:.2f}")
    records = []
    for question in questions:
        for repeat in range(1, repeats + 1):
            try:
                record = run_one(question, repeat, search_fn, answer_fn, llm, pipeline)
            except Exception as e:  # search or answer failed: keep the run, record why
                record = {
                    "id": question["id"],
                    "type": question["type"],
                    "expected_behavior": question["expected_behavior"],
                    "repeat": repeat,
                    "question": question["question"],
                    **{key: None for key in RESULT_KEYS + (PIPELINE_KEYS if pipeline else [])},
                    "error": str(e),
                }
            records.append(record)
            with open(out_dir / "runs.jsonl", "a") as f:  # saved now, so a crash keeps every finished run
                f.write(json.dumps(record) + "\n")
            print(f"{len(records)}/{total} {question['id']} r{repeat}" + (" error" if record["error"] else ""))
    return records




def make_pipeline(search_fn, answer_fn, llm, rerank, crag: bool, topic: bool):
    """Rows 9 and 10 for the eval, the same steps as the API (api/app.py).

    Returns pipeline(question) -> (hits, result, path, used_web):
      1. --topic: row 10's on_topic (Jev); P(on topic) < TOPIC_CUT → declined:
         ([], Answer(DECLINED), ["declined"], False); a failing check keeps the question.
      2. --crag: run_loop with config.GRADER, rewrite (Haiku, the same llm) and
         web_hits (Firecrawl, the same reranker); else search then answer, path
         ["retrieve", "generate"] (CR-12's baseline).
    hits: the chunks answer_fn was given (papers or web), else the last search's,
    recorded by wrapping search_fn and answer_fn. Needs OPENROUTER_API_KEY (and
    FIRECRAWL_API_KEY with --crag). Not counted in cost_usd: the rewrite calls
    (about $0.0005 each), Jev and Firecrawl.
    """
    from neuro_rag.api.app import DECLINED, GRADERS        # here: the API module loads FastAPI
    from neuro_rag.crag.graders import on_topic
    grade_fn = GRADERS[GRADER]
    counter = []

    def web_fn(query):
        if not counter:
            counter.append(TokenCounter())
        return web_hits(query, rerank, counter[0])

    def pipeline(question):
        if topic:
            try:
                declined = on_topic(question) < TOPIC_CUT
            except Exception as e:                       # never decline because a service is down
                print(f"  on-topic check failed, question kept: {e}")
                declined = False
            if declined:
                return [], Answer(DECLINED, [], [], 0, 0), ["declined"], False
        seen = {"search": [], "answer": []}

        def searched(query):
            seen["search"] = search_fn(query)
            return seen["search"]

        def answered(q, hits):
            seen["answer"] = hits
            return answer_fn(q, hits)

        if not crag:
            hits = searched(question)
            return hits, answered(question, hits), ["retrieve", "generate"], False
        result = run_loop(question, searched, grade_fn, answered,
                          lambda q, last: rewrite(q, last, llm), web_fn, FALLBACK)
        return seen["answer"] or seen["search"], result.answer, result.path, result.used_web

    return pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--rerank", action="store_true", help="dense top 20, reranked, keep 5 (row 8)")
    parser.add_argument("--crag", action="store_true", help="row 9: the corrective loop (grade, rewrite, web)")
    parser.add_argument("--topic", action="store_true", help="row 10: decline off-topic questions first")
    args = parser.parse_args()
    out_dir = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_{args.name}"
    out_dir.mkdir(parents=True, exist_ok=False)
    client = QdrantClient(url=QDRANT_URL)
    embed = TextEmbedding(EMBED_MODEL).embed
    sparse_embed = SparseTextEmbedding(SPARSE_MODEL).query_embed
    llm = make_llm()
    rerank = TextCrossEncoder(RERANK_MODEL).rerank if args.rerank else None

    def search_fn(question):
        return search(question, client, embed, sparse_embed, rerank=rerank)  # dense, top 5; reranked if --rerank

    def answer_fn(question, hits):
        return answer(question, hits, llm)

    pipeline = make_pipeline(search_fn, answer_fn, llm, rerank, args.crag, args.topic) if (args.crag or args.topic) else None
    records = run_eval(load_questions(), args.repeats, out_dir, search_fn, answer_fn, llm, pipeline)
    (out_dir / "report.md").write_text(build_report(records, args.name))
    print(f"report: {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()

