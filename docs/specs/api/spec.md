# API: spec

Roadmap row 5: `POST /ask` answers over HTTP.

## Goal

Put search (row 2) and the cited answer (row 3) behind one HTTP endpoint. A
client sends a question and gets the answer and its numbered sources as JSON.
A bad question gets a clear 422; a failing Qdrant or Claude gets a 503 with a
fixed message, never a crash and never the internal error text.

## In and out

- **In:** `POST /ask` with the JSON body `{"question": "<text>"}`.
- **Out:** `200` with `{"answer": "<text with [n] markers>", "sources": [...]}`,
  or an error status with `{"detail": ...}`.
- **Also:** `GET /health` → `200 {"status": "ok"}`, for row 7's Kubernetes
  probes.
- **Runs:** as a server:
  ```
  docker compose up -d                      # Qdrant
  uvicorn neuro_rag.api.app:create_app --factory --port 8000
  curl -s localhost:8000/ask -H 'Content-Type: application/json' \
       -d '{"question": "How does m6A RNA methylation support hippocampus-dependent learning and memory?"}'
  ```

```
POST /ask {"question"} ─► validate (strip, 1–1000 chars; else 422)
                       ─► search(question)          (fails → 503 "Search is unavailable…")
                       ─► answer(question, hits)    (fails → 503 "Answering is unavailable…")
                       ─► 200 {"answer", "sources"}
```

## Settings

| Setting | Value | Why |
|---|---|---|
| framework | FastAPI, served by uvicorn | request and response checked by pydantic models (the same library the judges use), OpenAPI docs at `/docs` for free; decided 2026-11-13 |
| question length | 1 to 1000 characters, after stripping spaces | empty can't be searched; the longest eval question is far below 1000, and a cap stops someone sending a book on our API key |
| search | dense, top 5 (row 2's default) | the same as the answer command and the eval |
| endpoint function | plain `def`, not `async def` | decided 2026-11-13: this is basic code, not production; `search` and `answer` stay as they are, and FastAPI runs a plain `def` in a thread pool, so one slow request doesn't stop the others |
| port | 8000 | uvicorn's default |
| API key | `ANTHROPIC_API_KEY` from the environment (`.env` locally), as in row 3 | never printed, logged or returned |

## How it is built

### Files

| File | Contents |
|---|---|
| `pyproject.toml` | dependencies gain `fastapi` and `uvicorn`; dev gains `httpx` (FastAPI's `TestClient` needs it) |
| `src/neuro_rag/api/__init__.py` | empty |
| `src/neuro_rag/api/app.py` | `AskRequest`, `SourceOut`, `AskResponse`, `SEARCH_DOWN`, `ANSWER_DOWN`, `build_pipeline`, `create_app` |
| `tests/test_api.py` | unit tests with fake search and answer: no Qdrant, no API call, no cost |
| `tests/test_api_live.py` | one end-to-end test on real Qdrant and Claude, marked `integration` and `llm` |

`search.py` and `answer.py` don't change.

### `api/app.py`

```python
SEARCH_DOWN = "Search is unavailable. Try again later."
ANSWER_DOWN = "Answering is unavailable. Try again later."

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]

class AskRequest(BaseModel):
    question: Question

class SourceOut(BaseModel):
    n: int
    pmcid: str
    page: int
    title: str
    citation: str
    url: str

class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]

def build_pipeline() -> tuple[search_fn, answer_fn]
    # builds QdrantClient(url=QDRANT_URL), TextEmbedding(EMBED_MODEL).embed,
    # SparseTextEmbedding(SPARSE_MODEL).query_embed and make_llm() once, and returns
    #   search_fn(question) -> list[Hit]       = search(question, client, embed, sparse_embed)
    #   answer_fn(question, hits) -> Answer    = answer(question, hits, llm)
def create_app(search_fn=None, answer_fn=None) -> FastAPI
    # both None → build_pipeline(); tests pass fakes
```

`create_app` is a factory, not a module-level `app`, so importing the module
in a test loads no embedding model; uvicorn calls it once with `--factory`.
The fakes have the same shape as the eval's (row 4): `search_fn(question)`
and `answer_fn(question, hits)`.

**`POST /ask` steps** (`def ask(request: AskRequest) -> AskResponse`):
1. FastAPI validates the body against `AskRequest`. A missing `question`, a
   non-string, an empty or all-spaces question, or one over 1000 characters
   → `422` with FastAPI's own `detail` list; steps 2–4 don't run.
2. `hits = search_fn(request.question)` (the question is already stripped).
   Any exception → log it with `logger.exception("search failed")`, return
   `503 {"detail": SEARCH_DOWN}`.
3. `result = answer_fn(request.question, hits)`. Any exception → log it with
   `logger.exception("answer failed")`, return `503 {"detail": ANSWER_DOWN}`.
4. Return `200` with `answer = result.text` and one `SourceOut` per
   `result.sources`, in number order.

The 503 body is a fixed sentence: the exception's text stays in the server
log, because it can name internal hosts, ports or library details.

**`GET /health`:** returns `200 {"status": "ok"}`. It calls neither search nor
Claude, so a probe every few seconds costs nothing.

**Worked example.** Request:
```json
{"question": "  How does m6A RNA methylation support hippocampus-dependent learning and memory?  "}
```
search gets the question without the outer spaces. Response `200` (answer
text illustrative; the real one is recorded in validation.md after the first
run):
```json
{
  "answer": "Ythdf1, a protein that reads m6A marks on RNA, increases protein synthesis … [1].",
  "sources": [
    {"n": 1, "pmcid": "PMC6226095", "page": 6,
     "title": "m6A facilitates hippocampus-dependent learning and memory through Ythdf1",
     "citation": "Nature. Author manuscript; Available in PMC 2019 Apr 30.",
     "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6226095/"}
  ]
}
```

## Choices, accepted 2026-11-13

1. **Sync, basic code.** Plain `def` endpoints calling the existing `search`
   and `answer` unchanged. Async would need async twins of rows 2 and 3; not
   worth it for this project.
2. **FastAPI.** Pydantic validation and the 422 come for free; the
   alternative (Flask) would need both written by hand.
3. **The response carries the answer and its sources only.** Tokens and
   cost go to row 6's traces, not to the client; `citations` (the quoted
   text) stay internal for now: a client can follow the PMC link.
4. **Search and answer failures are both 503,** each with its own fixed
   sentence, so the caller knows to retry and the log says which part failed.
   No retries in the API: the Anthropic SDK already retries twice.
5. **A no-hits answer and a refusal are `200`,** with row 3's fixed sentences:
   the system worked; it had nothing to say.
6. **The pipeline is built once, at startup** (`build_pipeline`), not per
   request: loading the embedding model takes seconds.
7. **`create_app` takes the two functions,** so the tests swap in fakes
   without patching, as the eval does.
8. **`/health` checks nothing behind it.** A readiness check that pings
   Qdrant is decided with row 7's probes.

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is checked is in [validation.md](validation.md).

The unit tests use `TestClient(create_app(fake_search, fake_answer))`.
`fake_search` returns one hit, PMC1 page 3, and records the question it got;
`fake_answer` returns `Answer("Place cells fire at one location [1].",
[Source(1, "PMC1", 3, "Title 1", "Citation 1",
"https://pmc.ncbi.nlm.nih.gov/articles/PMC1/")], [...], 1000, 100)` and
records the hits it got.

### Requests (fake search and answer, no API call)

**AP-1: a question gets its answer and sources as JSON.**
- **Given** the fakes above.
- **When** `POST /ask` with `{"question": "What do place cells do?"}`.
- **Then** the status is 200 and the body is exactly
  `{"answer": "Place cells fire at one location [1].", "sources": [{"n": 1,
  "pmcid": "PMC1", "page": 3, "title": "Title 1", "citation": "Citation 1",
  "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/"}]}`: no tokens, no
  citations.
- **Why:** this is the contract a client is built against; an extra or
  missing field breaks it.

**AP-2: the question reaches search stripped, and answer gets search's hits.**
- **Given** the fakes above.
- **When** `POST /ask` with `{"question": "  What do place cells do?  "}`.
- **Then** `fake_search` got "What do place cells do?", and `fake_answer` got
  that question and the one hit `fake_search` returned.
- **Why:** the API is only the wiring; if it passed the wrong question or
  dropped the hits, the answer would be about something else.

**AP-3: a bad question is a 422, and nothing is searched.**
- **Given** the fakes above.
- **When** `POST /ask` with each of: `{"question": ""}`, `{"question": "   "}`,
  `{"question": "<1001 times a>"}`, `{}`, `{"question": 42}`.
- **Then** each gets 422, and `fake_search` was never called. A question of
  exactly 1000 characters gets 200.
- **Why:** an empty question would reach `search` and raise its own
  `ValueError`; a huge one would cost money on every request.

**AP-4: Qdrant failing is a 503 with a fixed sentence.**
- **Given** a `search_fn` raising `ConnectionError("[Errno 61] Connection refused: localhost:6333")`.
- **When** `POST /ask` with `{"question": "What do place cells do?"}`.
- **Then** the status is 503, the body is exactly
  `{"detail": "Search is unavailable. Try again later."}`, the body doesn't
  contain "6333", and `fake_answer` was not called.
- **Why:** a crash would give the client a bare 500; the internal host and
  port are none of the client's business.

**AP-5: Claude failing is a 503 with a fixed sentence.**
- **Given** the fake search, and an `answer_fn` raising
  `RuntimeError("anthropic: 529 overloaded")`.
- **When** `POST /ask` with `{"question": "What do place cells do?"}`.
- **Then** the status is 503 and the body is exactly
  `{"detail": "Answering is unavailable. Try again later."}`.
- **Why:** the two sentences tell the caller to retry, and the server log
  tells us which part failed.

**AP-6: the health check calls nothing.**
- **Given** the fakes above.
- **When** `GET /health`.
- **Then** the status is 200, the body is `{"status": "ok"}`, and neither fake
  was called.
- **Why:** row 7's Kubernetes probes call it every few seconds; it must cost
  nothing and not depend on Claude.

### End to end (real Qdrant and Claude, marked `integration` and `llm`)

**AP-7: the real app answers q01 with cited sources.**
- **Given** the `papers` collection in Qdrant and the API key in `.env`.
- **When** `TestClient(create_app())` gets `POST /ask` with q01, "How does
  m6A RNA methylation support hippocampus-dependent learning and memory?".
- **Then** the status is 200, there is at least one source, every `[n]` in
  the answer has a source with that `n`, and every source's `url` starts with
  `https://pmc.ncbi.nlm.nih.gov/articles/PMC`.
- **Why:** the fakes can't show the real pieces are wired together; one
  request (about $0.003) does.

### The server

**AP-8: the server starts and answers over real HTTP.**
- **Given** Qdrant running and the API key in `.env`.
- **When** `uvicorn neuro_rag.api.app:create_app --factory --port 8000` runs,
  then the `curl` in "In and out".
- **Then** curl prints JSON with `answer` and `sources`; `curl -s
  localhost:8000/health` prints `{"status":"ok"}`; and the server log never
  shows the API key.
- **Why:** this is the row's "done when", and what row 7 puts in a container.

## Out of scope

- Async endpoints and async Qdrant or Claude clients (choice 1).
- Who may call the API and how often: client keys and rate limits are
  decided in row 7, before the URL is public.
- Tracing, timings, tokens and cost per request (row 6).
- The container image and Kubernetes manifests (row 7).
- Streaming the answer; multi-turn chat; choosing dense or hybrid per request.
- Timeouts beyond the Anthropic SDK's own.
