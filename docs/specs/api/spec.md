# API: spec

What this module must do. Written when its row in [ROADMAP.md](../../ROADMAP.md)
starts.

## Goal

Expose the system as `POST /ask`, with input validation and clear errors.

## In and out

- **In:** `POST /ask` with a JSON body `{"question": "..."}`.
- **Out:** the answer, its numbered sources, and the trace ID of the request:

```json
{
  "answer": "Place cells fire when the animal is at a specific location. [1]",
  "sources": [
    {"n": 1, "pmcid": "PMC1", "title": "…", "citation": "…", "page": 3,
     "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/"}
  ],
  "trace_id": "a3f…"
}
```

- **Also:** `GET /health`, for Docker Compose and the deployment (row 10) to
  check the service is ready.

```
POST /ask ──► validate ──► pipeline: retrieve (hybrid) ──► rerank ──► generate ──► JSON
                              └── one trace per request (observability) ──┘
```

The API never calls retrieval or generation itself. It calls one function in
`orchestration`, `ask(question)`, which runs the steps in a straight line for
now; row 7 replaces that line with the corrective graph without changing the
API (ARCHITECTURE section 2: `api` → `orchestration` → steps).

## Settings

| Setting | Start | Why |
|---|---|---|
| framework | FastAPI | request validation and error responses from type hints; the choice in ARCHITECTURE |
| question length | 1 to 1,000 characters, after trimming spaces | long enough for a rambling question (the longest in the eval is about 300); short enough that nobody pastes a whole paper |
| reranker | on, 20 chunks ([decision 005](../../decisions/005-reranker.md)) | |
| models | loaded once, when the service starts | so no request pays the seconds it takes to load them |

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own:
**Given** what is running, **When** the request that is sent, **Then** what
must be true, **Why** what is broken if it fails. Most examples use a fake
pipeline, so they run without Qdrant or Claude; the fake retrieves one chunk,
from paper PMC1, page 3: "Place cells in the hippocampus fire when the animal
is at a specific location." How each one is run is in
[validation.md](validation.md).

### Answers

**AP-1: a question gets the answer, its sources and a trace ID.**
- **Given** the API, with the fake pipeline answering "Place cells fire when
  the animal is at a specific location. [1]" from the PMC1 chunk.
- **When** a client sends `POST /ask` with `{"question": "What do place cells do?"}`.
- **Then** the response is `200`, and its JSON has `answer` with that text,
  `sources` with one entry (`n` 1, `pmcid` "PMC1", the title, citation, page 3
  and the PubMed Central link), and a non-empty `trace_id`.
- **Why:** the UI (row 9) shows the answer and links each `[n]` to its source;
  the trace ID lets a user report a bad answer so it can be found in Langfuse.

**AP-2: a question the papers don't cover is an answer, not an error.**
- **Given** the API, with a fake pipeline whose answer cites nothing: "The
  provided papers don't cover this."
- **When** a client sends `POST /ask` with `{"question": "How do I fix a flat tyre?"}`.
- **Then** the response is `200`, `answer` is that sentence, and `sources` is
  an empty list.
- **Why:** "not covered" is a correct answer, not a failure; a `4xx` or `5xx`
  here would make the UI show an error for the system doing its job.

### Bad input

**AP-3: an empty question is rejected before anything runs.**
- **Given** the API, with a fake pipeline that records whether it was called.
- **When** a client sends `{"question": ""}`, then `{"question": "   "}`, then
  `{}` (no question at all).
- **Then** each response is `422` with a message saying the question is
  missing or empty, and the pipeline was never called.
- **Why:** an empty question can't be answered; letting it through would spend
  a retrieval and possibly a Claude call on nothing.

**AP-4: a question over 1,000 characters is rejected.**
- **Given** the API, with the fake pipeline.
- **When** a client sends a question of 1,001 characters, then one of exactly
  1,000.
- **Then** the first gets `422` with a message giving the 1,000-character
  limit, and the pipeline is not called; the second gets `200`.
- **Why:** every character is sent to Claude and paid for; without a limit,
  one request could paste a whole paper. The second request checks the limit
  is not off by one.

### Failures

**AP-5: Qdrant down gives `503` with a clear message.**
- **Given** the API, with a fake pipeline that raises `RetrievalError("Qdrant
  is unreachable")`.
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the response is `503`, its JSON has `detail` "The paper index is
  unavailable. Please try again shortly." and the `trace_id`, and no stack
  trace or internal address appears anywhere in the response.
- **Why:** `503` tells the UI (and the user) the service is down for a moment,
  not that the question was wrong; internal details in a response help an
  attacker and confuse a user.

**AP-6: Claude unavailable gives `503` with a clear message.**
- **Given** the API, with a fake pipeline that raises `GenerationError("Claude
  is unavailable")`.
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the response is `503`, `detail` is "The answer service is
  unavailable. Please try again shortly.", and the `trace_id` is included.
- **Why:** Claude being overloaded or down is temporary and not the user's
  fault; the message says to retry, not to rephrase.

**AP-7: an unexpected error gives `500` and reveals nothing.**
- **Given** the API, with a fake pipeline that raises `KeyError("payload")`.
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the response is `500`, `detail` is "Something went wrong.", the
  `trace_id` is included, and the response body does not contain "KeyError"
  or "payload". The full error is in the service log, with the same trace ID.
- **Why:** a bug must not leak code details to the user, but must still be
  findable: the trace ID links the user's report to the logged error.

### Service

**AP-8: the models load when the service starts, not on the first question.**
- **Given** the real service, just started, with the real index, the real
  encoders and the real reranker, and a fake in place of Claude that answers
  instantly.
- **When** the first question is sent, then a second one.
- **Then** the first question takes no more than 1 s longer than the second.
- **Why:** loading the encoders and the reranker takes several seconds; if the
  first user after each restart paid it, the first answer would miss the 6 s
  target. Claude is replaced because its time varies by 1–2 s from one call to
  the next and has nothing to do with loading models: with it, the first run
  failed at 5.78 s against 4.29 s without any model loading late.

**AP-9: `/health` says whether the service can answer.**
- **Given** two situations: (a) the service running with Qdrant up and the
  `hippocampus` alias present; (b) the same service with Qdrant stopped.
- **When** a client sends `GET /health` in each.
- **Then** (a) returns `200` with `{"status": "ok", "index": "hippocampus-v1"}`
  (the collection the alias points at); (b) returns `503` with
  `{"status": "unavailable"}`. Neither calls Claude.
- **Why:** Docker Compose and the server (row 10) restart or hold back a
  service that isn't ready; that needs a cheap check that doesn't spend
  money.

**AP-10: an answer through the API takes at most 6 s.**
- **Given** the real service with the real index and Claude, already started.
- **When** the 20 known-paper questions from retrieval are sent one after
  another, and each is timed from request to response.
- **Then** 95% take 6 s or less. The test also sends the same 20 with 4 at a
  time and reports their p95, without a limit.
- **Why:** 6 s is the system target in the ROADMAP, measured as the user sees
  it. The concurrent number is what decision 005 asked for: the reranker
  slows down when requests share the CPU, and row 10 needs to know by how much.

## Out of scope

- Authentication and rate limiting (row 10, before the URL is public: every
  request costs money).
- Streaming the answer as it is written (a later candidate).
- The corrective steps: grading, rewrite, web search, declining (rows 6b–8).
- The UI (row 9).
