"""Dense against hybrid search on the eval questions' expected sources.

    python scripts/compare_search.py
"""
import csv
import json
from datetime import date
from pathlib import Path

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient

from neuro_rag.config import EMBED_MODEL, QDRANT_URL, SPARSE_MODEL
from neuro_rag.retrieval.search import search

ROOT = Path(__file__).parents[1]
QUESTIONS = ROOT / "eval" / "questions.jsonl"
RESULTS_DIR = ROOT / "eval" / "results"
MODES = ("dense", "hybrid")


def load_questions(path: Path) -> list[dict]:
    questions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            q = json.loads(line)
            if q["expected_sources"]:
                questions.append(q)
    return questions


def check(question: dict, hits) -> tuple[bool, bool]:
    papers = {s["pmcid"] for s in question["expected_sources"]}
    pages = {(s["pmcid"], s["page"]) for s in question["expected_sources"]}
    paper_hit = any(h.pmcid in papers for h in hits)
    page_hit = any((h.pmcid, h.page) in pages for h in hits)
    return paper_hit, page_hit


def main():
    questions = load_questions(QUESTIONS)
    client = QdrantClient(url=QDRANT_URL)
    embed = TextEmbedding(EMBED_MODEL).embed
    sparse_embed = SparseTextEmbedding(SPARSE_MODEL).query_embed

    rows = []
    for q in questions:
        for mode in MODES:
            hits = search(q["question"], client, embed, sparse_embed, k=5, mode=mode)
            paper_hit, page_hit = check(q, hits)
            rows.append({
                "id": q["id"],
                "type": q["type"],
                "mode": mode,
                "paper_hit": paper_hit,
                "page_hit": page_hit,
                "chunk_ids": " ".join(h.chunk_id for h in hits),
            })

    english = [r for r in rows if not r["type"].startswith("multilingual_")]
    multilingual = [r for r in rows if r["type"].startswith("multilingual_")]
    for label, group in ((f"{len(english) // 2} English questions", english),
                         (f"{len(multilingual) // 2} multilingual questions", multilingual)):
        total = len(group) // 2
        print(label)
        print("mode     paper@5   page@5")
        for mode in MODES:
            mine = [r for r in group if r["mode"] == mode]
            papers = sum(r["paper_hit"] for r in mine)
            pages = sum(r["page_hit"] for r in mine)
            print(f"{mode:<8} {papers:>2}/{total:<6} {pages:>2}/{total}")

    by_id = {}
    for r in rows:
        by_id.setdefault(r["id"], {})[r["mode"]] = r["page_hit"]
    differ = [f"{qid} {'hybrid' if found['hybrid'] else 'dense'}"
              for qid, found in by_id.items() if found["dense"] != found["hybrid"]]
    print("differ on page@5:", ", ".join(differ) if differ else "none")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"search_compare_{date.today().isoformat()}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "type", "mode", "paper_hit", "page_hit", "chunk_ids"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
