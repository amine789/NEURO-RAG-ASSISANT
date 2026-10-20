"""Settings shared across modules. Values that differ per machine come from the environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CATALOG_PATH = DATA_DIR / "candidates.csv"
RAW_DIR = DATA_DIR / "raw"
SNAPSHOT_DIR = DATA_DIR / "snapshots"

QDRANT_URL = os.getenv("QDRANT_URL") or "http://localhost:6333"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None

# The API always reads through this alias; each build is a new collection "<alias>-v<N>".
COLLECTION_ALIAS = "hippocampus"

# Encoders (specs/ingest/spec.md, Settings). Ingest and retrieval must use the same ones.
DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DENSE_SIZE = 384
SPARSE_MODEL = "Qdrant/bm25"

# Optional reranker (specs/retrieval/spec.md, Reranking).
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"  # ONNX export of cross-encoder/ms-marco-MiniLM-L6-v2

# Every LLM call uses this model (ARCHITECTURE section 1).
LLM_MODEL = "claude-haiku-5-5"
LLM_EFFORT = "low"
# Haiku 5.5 price in dollars per token (prompts under 100K tokens); used by the eval and by tracing.
PRICE_IN, PRICE_OUT = 0.10 / 1e6, 0.50 / 1e6

# Chunking, in tokens of the dense model's own tokenizer.
CHUNK_SIZE = 200
CHUNK_OVERLAP = 64
