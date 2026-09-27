"""Settings shared across the pipeline. Add a setting here when a step starts using it."""

from pathlib import Path

# Paths. config.py is src/neuro_rag/config.py, so the project root is two folders up.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CATALOG_PATH = PROJECT_ROOT / "data" / "candidates.csv"  # written by collect_corpus.py
PAGES_PATH = PROJECT_ROOT / "data" / "pages.jsonl"

# Vector store: local on-disk Qdrant (no server needed).
QDRANT_PATH = PROJECT_ROOT / "data" / "qdrant"
COLLECTION_NAME = "hippocampus"

# Embedding model (sentence-transformers). all-MiniLM-L6-v2 reads at most 256 tokens.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# Length of each embedding vector; must match EMBEDDING_MODEL (all-MiniLM-L6-v2 -> 384).
VECTOR_SIZE = 384

# Chunking: sizes are tiktoken tokens; keep CHUNK_SIZE below the model's limit.
CHUNK_SIZE = 200
CHUNK_OVERLAP = 64

# How many BM25 results to keep before fusing with dense search.
BM25_TOP_K = 20

# Reciprocal rank fusion constant: higher = ranks matter less. 60 is the standard default.
RRF_K = 60
