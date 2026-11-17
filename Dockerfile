# The Neuro-RAG API (roadmap row 7). Build from the repo root:
#   docker buildx build --platform linux/amd64 -t ghcr.io/amine789/neuro-rag-api:<sha> .
# Keys are not in the image: they come from the environment (a k8s Secret, or --env-file .env).
FROM python:3.11-slim

WORKDIR /app

# the dependencies at the exact versions validated on the laptop, then our package alone
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

# the two embedding models, downloaded now so the pod starts without network
# (the names repeat config.py's EMBED_MODEL and SPARSE_MODEL)
ENV FASTEMBED_CACHE_PATH=/models
RUN python -c "from fastembed import TextEmbedding, SparseTextEmbedding; \
TextEmbedding('sentence-transformers/all-MiniLM-L6-v2'); SparseTextEmbedding('Qdrant/bm25')"

EXPOSE 8000

# 0.0.0.0, not uvicorn's default 127.0.0.1, so it is reachable from outside the container
CMD ["uvicorn", "neuro_rag.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
