# Neuro-RAG Assistant: Roadmap

What the product is, and every functionality in the order it is built. The frame
is in [ARCHITECTURE.md](ARCHITECTURE.md); each module's spec and validation are in
[specs/](specs/).

## Product

**Purpose.** Answer questions about hippocampus and memory neuroscience with
grounded, cited answers. Answers come from a curated corpus of open-access papers
and, only when the corpus can't answer, from vetted web sources. Wrong answers in
a science domain are costly, so the system must say when it doesn't know.

**Users.** Students and researchers with some neuroscience background, asking in
their own words: precise terminology, casual phrasing or typos. English only.

**Scope.**

| Question kind | Behaviour |
|---|---|
| Neuroscience, covered by the corpus | answer from the papers, with citations |
| Neuroscience, not covered by the corpus | correct the search, then fall back to the web; the answer says it used the web |
| Outside neuroscience | decline briefly as out of scope |
| Borderline (psychology of memory, sleep, brain health) | in scope; when in doubt, never decline |
| False premise | correct the premise from the sources |

**Non-goals.** Multi-turn chat memory, user accounts, non-open-access literature,
medical advice for individuals.

**System-wide targets.**

| Area | Target |
|---|---|
| Latency (p95) | corpus path ≤ 6 s total; web path ≤ 30 s |
| Reliability | a failing optional part (web search, a parse) degrades the answer, never crashes the request |
| Citations | every `[n]` in an answer maps to a listed source |
| Cost | measured per request from traces; target set after the first measured run |
| Security | API keys only in environment variables; never in images, logs or traces |

## Functionalities

Built in this order. A module's spec is written when its row starts, not before.
Status: planned → spec written → built → validated.

| # | Functionality | Modules | Done when | Status |
|---|---|---|---|---|
| 1 | Ingest and index | `ingest` | the 52 papers are a searchable, citable Qdrant collection, with a snapshot | validated |
| 2 | Hybrid search | `retrieval` | a question returns its top chunks from dense + keyword search | validated |
| 3 | Cited answer | `generation` | a question gets an answer citing paper and page | validated |
| 4 | Eval set and baseline score | `eval` | functionalities 1–3 have a measured score | built: baseline measured; EV-11 (judge vs a person) open |
| 5 | API and tracing | `api`, `observability` | `POST /ask` answers, and each request is traced | planned |
| 6a | Reranker | `retrieval`, `eval` | compared with the baseline: kept if correctness or retrieval hit rises, no score drops by more than 0.05, and p95 stays ≤ 6 s | built: kept, 20 chunks on ONNX ([decision 005](decisions/005-reranker.md)) |
| 6b | Relevance judging (grading with thresholds) | `grading` | measured against the baseline | planned |
| 7 | Correction: rewrite and web search | `correction`, `orchestration` | out-of-corpus questions improve, measured against the baseline | planned |
| 8 | Declining off-domain questions | `grading`, `orchestration` | off-domain questions declined, no false declines | planned |
| 9 | UI | `ui` | the app works in a browser | planned |
| 10 | Deployment | `deployment` | public URL; the eval passes against it | planned |

1–5 is the walking skeleton: the simplest version that works end to end. Each
row after it is an improvement, kept only if the eval shows it helps.

Candidates for later, each measured before it is kept: Contextual Retrieval
(LLM-written context added to each chunk at ingest), per-step retrieval metrics,
streaming answers.
