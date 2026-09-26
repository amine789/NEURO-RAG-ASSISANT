"""Settings shared across the pipeline. Add a setting here when a step starts using it."""

# Embedding model (sentence-transformers). all-MiniLM-L6-v2 reads at most 256 tokens.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking: sizes are tiktoken tokens; keep CHUNK_SIZE below the model's limit.
CHUNK_SIZE = 200
CHUNK_OVERLAP = 64

# How many BM25 results to keep before fusing with dense search.
BM25_TOP_K = 20
