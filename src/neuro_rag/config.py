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
COLLECTION = "papers"
BATCH = 64
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
GROBID_URL = os.environ.get("GROBID_URL", "http://localhost:8070")

LLM_MODEL = "claude-haiku-4-5"
PRICE_IN = 1.00
PRICE_OUT = 5.00
