# NEUR-RAG-ASSISANT

Corrective/Self-RAG assistant over a hippocampus neuroscience corpus: hybrid retrieval, LLM relevance grading, query rewrite and web fallback, cited answers.

In the diagrams, a filled green dot marks a part that is built and a hollow dot marks a part that is planned. Purple edges are the corrective path, which runs only when retrieval is weak.

## Offline: build the corpus and indexes

![Ingestion pipeline](docs/images/ingestion-pipeline.svg)

`scripts/collect_corpus.py` searches PubMed Central, and you review the candidates in `data/candidates.csv`. The script then downloads the kept PDFs from the PMC Open Access bucket and checks their md5. Each chunk keeps its source, title and page so answers can cite it. The same chunks go into a Qdrant vector index and a BM25 keyword index.

```bash
python scripts/collect_corpus.py search     # -> data/candidates.csv
python scripts/collect_corpus.py download   # keep=yes rows -> data/raw/
```

## Query time: the corrective loop

![Corrective RAG query loop](docs/images/query-loop.svg)

Each box is a LangGraph node, and the diamond is a conditional edge. When retrieval is good, the question takes the straight path across the middle. When grading fails, the query is rewritten and retried until the retry budget runs out, and then the agent falls back to web search.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
```
