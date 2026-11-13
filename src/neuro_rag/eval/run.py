import json
import time
from datetime import datetime
from pathlib import Path
import argparse

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient

from neuro_rag.config import EMBED_MODEL, PRICE_IN, PRICE_OUT, QDRANT_URL, QUESTIONS_PATH, SPARSE_MODEL, RESULTS_DIR
from neuro_rag.eval.judge import judge_correctness, judge_faithfulness
from neuro_rag.eval.report import build_report
from neuro_rag.generation.answer import Answer, answer, make_llm
from neuro_rag.retrieval.search import Hit, search


# every key of a record besides the question's own fields and "error"; None when a run fails
RESULT_KEYS = [
    "chunk_ids", "answer", "sources",
    "paper_hit", "page_hit", "cites_expected", "not_covered", "cites_papers",
    "search_s", "answer_s", "correctness", "faithfulness", "cost_usd",
]


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


def run_one(question: dict, repeat: int, search_fn, answer_fn, llm) -> dict:
    # 1. ask the system, timed
    t0 = time.perf_counter()
    hits = search_fn(question["question"])
    t1 = time.perf_counter()
    result = answer_fn(question["question"], hits)
    t2 = time.perf_counter()

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
        "search_s": round(t1 - t0, 2),
        "answer_s": round(t2 - t1, 2),
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


def run_eval(questions: list[dict], repeats: int, out_dir: Path, search_fn, answer_fn, llm) -> list[dict]:
    total = len(questions) * repeats
    print(f"{total} runs, estimated ${total * 0.005:.2f}")
    records = []
    for question in questions:
        for repeat in range(1, repeats + 1):
            try:
                record = run_one(question, repeat, search_fn, answer_fn, llm)
            except Exception as e:  # search or answer failed: keep the run, record why
                record = {
                    "id": question["id"],
                    "type": question["type"],
                    "expected_behavior": question["expected_behavior"],
                    "repeat": repeat,
                    "question": question["question"],
                    **{key: None for key in RESULT_KEYS},
                    "error": str(e),
                }
            records.append(record)
            with open(out_dir / "runs.jsonl", "a") as f:  # saved now, so a crash keeps every finished run
                f.write(json.dumps(record) + "\n")
            print(f"{len(records)}/{total} {question['id']} r{repeat}" + (" error" if record["error"] else ""))
    return records




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    out_dir = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_{args.name}"
    out_dir.mkdir(parents=True, exist_ok=False)
    client = QdrantClient(url=QDRANT_URL)
    embed = TextEmbedding(EMBED_MODEL).embed
    sparse_embed = SparseTextEmbedding(SPARSE_MODEL).query_embed
    llm = make_llm()

    def search_fn(question):
        return search(question, client, embed, sparse_embed)       # dense, top 5 (defaults)

    def answer_fn(question, hits):
        return answer(question, hits, llm)

    records = run_eval(load_questions(), args.repeats, out_dir, search_fn, answer_fn, llm)
    (out_dir / "report.md").write_text(build_report(records, args.name))
    print(f"report: {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()

