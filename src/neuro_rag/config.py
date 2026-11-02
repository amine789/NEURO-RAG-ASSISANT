import os
from pathlib import Path

DATA_DIR = Path(__file__).parents[2] / "data"
CATALOG_PATH = DATA_DIR / "candidates.csv"
RAW_DIR = DATA_DIR / "raw"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_SIZE = 384
COLLECTION = "papers"
BATCH = 64
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
