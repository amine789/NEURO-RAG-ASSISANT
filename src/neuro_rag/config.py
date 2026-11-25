import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parents[2] / "data"
CATALOG_PATH = DATA_DIR / "candidates.csv"
RAW_DIR = DATA_DIR / "raw"
TEI_DIR = DATA_DIR / "tei"
QUESTIONS_PATH = Path(__file__).parents[2] / "eval" / "questions.jsonl"
RESULTS_DIR = Path(__file__).parents[2] / "eval" / "results"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_SIZE = 384
SPARSE_MODEL = "Qdrant/bm25"
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"  # row 8: cross-encoder, fastembed
COLLECTION = "papers"
BATCH = 64
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
GROBID_URL = os.environ.get("GROBID_URL", "http://localhost:8070")
# row 9, grader G2: llama.cpp server for Gemma 3 1B (docker-compose service gemma1b)
GEMMA_URL = os.environ.get("GEMMA_URL", "http://localhost:8081")
# row 9, grader G3: llama.cpp server for Laya (docker-compose service laya)
LAYA_URL = os.environ.get("LAYA_URL", "http://localhost:8082")

# row 9, the corrective loop (docs/specs/crag/spec.md, phase 2)
GRADE_CUT = 0.5      # good if the grader's P(yes) >= GRADE_CUT, else weak; fixed, never fitted on the eval (choice 2)
MAX_REWRITES = 2     # weak -> rewrite the query and retry, at most twice; still weak -> the web (choice 5)
GRADER = "jev"       # the loop's grader: Jev via OpenRouter (choice 20); the others stay for compare_graders.py
FALLBACK = True      # row 9 trial (2026-11-22): weak everywhere -> Claude answers from the first search's hits
                     # (it says "the papers don't cover it" if they don't) instead of "not covered" (spec choice 23)
TOPIC_CUT = 0.5      # row 10: declined if P(on topic) < 0.5; was 0.2 until choice 24's comparison (2026-11-25):
                     # Jev at 0.5 made 0 false declines and 1 miss on 90 jury-labelled questions (kept ones all >= 0.85)
WEB_DOMAINS = [      # the web fallback only keeps pages from these vetted sites ("vetted web sources", roadmap)
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "www.ncbi.nlm.nih.gov",
    "www.nature.com",
    "www.science.org",
    "www.cell.com",
    "elifesciences.org",
    "www.jneurosci.org",
    "en.wikipedia.org",
]

LLM_MODEL = "claude-haiku-4-5"
PRICE_IN = 1.00
PRICE_OUT = 5.00
