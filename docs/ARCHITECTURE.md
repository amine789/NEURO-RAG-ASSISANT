# Neuro-RAG Assistant: Architecture

The frame every functionality plugs into. What gets built, in which order, is in
[ROADMAP.md](ROADMAP.md); what each module must do is in [specs/](specs/); why it
is built this way is in [decisions/](decisions/).

Only decisions that are expensive to change later belong here. Everything else
goes in a module's spec, when the roadmap reaches it.

## 1. System context

Deployed on one server with Docker Compose ([decision 001](decisions/001-deployment-target.md)).

```
                       ┌────────────── one server (Docker Compose) ──────────────┐
 user ── browser ──►   │  UI (Streamlit) ──HTTP──► API (FastAPI + graph) ──► Qdrant │
                       └──────────────────────────────┬──────────────────────────┘
                                                      │ HTTPS
                              Anthropic · Firecrawl · Langfuse Cloud

 offline, on a laptop:  PubMed Central PDFs ──► index build job ──► snapshot ──► server's Qdrant
```

**Inside the boundary** (built and run here): the Streamlit UI, the FastAPI API
with the corrective graph and the embedding model, the Qdrant container, and the
offline index build job.

| External system | Provides | Used |
|---|---|---|
| Anthropic (`claude-haiku-5-5`) | LLM calls: grading, rewriting, generation | every question |
| Firecrawl | web search and page scraping | web fallback only |
| Langfuse Cloud | tracing: steps, prompts, tokens, latency, cost | every question |
| Hugging Face (`all-MiniLM-L6-v2`, `Qdrant/bm25`) | dense and sparse encoders, downloaded once, run locally | index build and every question |
| PubMed Central | the corpus PDFs and their licenses | offline, once |

Choices behind this picture:

- **Qdrant runs as our own container**, not Qdrant Cloud: free, identical locally
  and on the server, no single-process limit, the index stays with us.
- **Langfuse Cloud**, not self-hosted: self-hosting needs its own database,
  analytics store, cache and storage. Trade-off: questions and prompts leave the
  server.
- **One model, Claude Haiku 5.5, for every LLM call**: cheapest and fastest,
  which the latency target needs; a stronger model is tried only if the eval
  shows Haiku isn't good enough.
- **The UI calls the API over HTTP**: one entry point, so every request gets the
  same validation, errors and tracing; the UI stays a thin display layer.

## 2. Building blocks

Each module has its own spec in [specs/](specs/).

| Module | Responsible for |
|---|---|
| `ingest/` | parsing PDFs, cleaning, chunking; the index build job |
| `retrieval/` | the dense and sparse encoders; the hybrid query to Qdrant |
| `grading/` | judging whether retrieved chunks are relevant to the question |
| `correction/` | rewriting the query; web search |
| `generation/` | writing the cited answer; checking its citations |
| `orchestration/` | the graph: its state, steps and routing |
| `api/` | the HTTP entry point: input validation, errors, starting a trace |
| `ui/` | the Streamlit display |
| `config` | settings read from environment variables |
| `observability` | Langfuse setup |

Dependency rules:

- **Dependencies point one way:** `ui` → (HTTP) → `api` → `orchestration` →
  steps (`grading`, `correction`, `generation`) → `retrieval` and the LLM client.
  Nothing depends on a module above it.
- **Steps never import each other.** Only `orchestration` wires them together, so
  each step can be tested and replaced alone.
- **`ui` reaches the system only over HTTP.** It imports no other module.
- **`ingest` and `retrieval` share one definition** of the encoders and the chunk
  schema. If indexing and querying encoded text differently, search would get
  worse without any error.

## 3. Data

```
PubMed Central ──► catalog ──► PDFs ──► pages ──► chunks ──► dense + sparse vectors ──► Qdrant ──► snapshot
```

- **Source:** open-access papers from PubMed Central, picked by hand into a
  catalog (`data/candidates.csv`) that records each paper's title, citation and
  license. The catalog, not the PDF, is the source of truth for citations.
- **Built offline, on the laptop.** The index build job runs locally, is checked
  with the eval, and is shipped to the server as a Qdrant snapshot. The server
  only answers questions; it holds no PDFs and no build code.
- **Each chunk carries** its text, a dense vector, a sparse keyword vector
  ([decision 002](decisions/002-keyword-search-in-qdrant.md)), and enough
  metadata to cite it: paper and page.
- **Rebuilds are full, never in place,** into a new versioned collection behind
  an alias, so the API never reads a half-built index and rolling back means
  moving the alias back.
- **The encoders are fixed per index.** Changing the embedding model or the
  keyword encoder means building a new index.
