# Tracing: spec

Roadmap row 6: every request is traced: its steps, timings, tokens and cost.

## Goal

Every `POST /ask` leaves one trace in LangSmith: a tree with the request at
the top, then search, then answer with Claude's call inside it. Each step has
its duration; the Claude call has its input and output tokens and its cost.
Tracing never changes what the client gets: if LangSmith is down or the key
is wrong, the request still answers.

## In and out

- **In:** the API from row 5, unchanged for the client, and three environment
  variables in `.env` (gitignored):
  ```
  LANGSMITH_TRACING=true
  LANGSMITH_API_KEY=<key from smith.langchain.com>
  LANGSMITH_PROJECT=neuro-rag
  ```
- **Out:** one trace per request in the LangSmith project `neuro-rag`:
  ```
  ask                      1 run, total duration, the question in, the answer out
  ├── search               duration, the question in, the 5 chunk IDs out
  └── answer               duration, the question and hits in, the answer out
      └── ChatAnthropic    duration, input/output tokens, cost (added by LangChain on its own)
  ```
- **Runs:** as row 5's server; nothing new to start.

## Settings

| Setting | Value | Why |
|---|---|---|
| tool | LangSmith (cloud, free Developer plan) | LangChain traces every `ChatAnthropic` call into it with tokens and cost and no code; one `@traceable` decorator adds our own steps; nothing to host; to confirm |
| on or off | on only when `LANGSMITH_TRACING=true` | the unit tests and anyone without a key run with tracing off; `@traceable` is then a no-op |
| project | `neuro-rag`, from `LANGSMITH_PROJECT` | all traces in one place |
| key | `LANGSMITH_API_KEY` in `.env`, loaded by `config.py`'s `load_dotenv()` like the Anthropic key | never printed, logged or committed; a Kubernetes Secret in row 7 |
| cost | LangSmith's own price table for `claude-haiku-4-5` ($1 / $5 per million) | checked on the first trace (TR-2); if it shows no cost, the price is set once in LangSmith's model settings |
| sending | LangSmith's client sends traces from a background thread | the request doesn't wait for LangSmith, and a LangSmith failure is a log warning, not an error |
| free plan limits | about 5,000 traces a month, kept 14 days (to check on signup) | far above our use: the eval is 50 requests |

## How it is built

### Files

| File | Contents |
|---|---|
| `pyproject.toml` | dependencies gain `langsmith` (already installed with LangChain; listed because we now import it) |
| `src/neuro_rag/api/app.py` | `create_app` wraps the two steps and `ask` with `@traceable` |
| `.env` | the three variables above (not committed) |

`search.py`, `answer.py` and the eval don't change.

### `api/app.py` changes

In `create_app`, after the `build_pipeline()` line:

```python
@traceable(name="search")
def traced_search(question):
    hits = search_fn(question)
    return hits

@traceable(name="answer")
def traced_answer(question, hits):
    return answer_fn(question, hits)
```

and `ask` gets `@traceable(name="ask")` under `@app.post("/ask")`, and calls
`traced_search` / `traced_answer` instead of `search_fn` / `answer_fn`.

- **Wrapping in `create_app`, not in `build_pipeline`,** so the unit tests'
  fakes go through the same wrappers: AP-1 to AP-6 exercise the traced path
  with tracing off.
- **Wrapping with a small `def`, not `traceable(...)(search_fn)` directly,**
  because the tests pass objects (`FakeSearch()`) rather than functions, and
  a `def` has the name and signature `@traceable` reads.
- **The Claude call needs nothing:** `ChatAnthropic` is a LangChain object,
  and LangChain sends its run (tokens, cost, duration) to LangSmith whenever
  `LANGSMITH_TRACING=true`, nested under the `answer` step that called it.
- **A failing step shows as an error in the trace:** `@traceable` records the
  exception and re-raises it, so `ask`'s `try/except` still turns it into the
  503.

**What a trace holds for q01** (illustrative; the real numbers are recorded
in validation.md after the first trace):

| Run | Duration | In | Out | Tokens | Cost |
|---|---|---|---|---|---|
| ask | 3.1 s | the question | `AskResponse` | | |
| search | 0.1 s | the question | 5 `Hit`s | | |
| answer | 3.0 s | the question, 5 `Hit`s | `Answer` | | |
| ChatAnthropic | 2.9 s | system prompt, 5 documents, question | the text blocks | 2,293 in, 179 out | $0.0032 |

## Choices, to confirm

1. **LangSmith.** Langfuse could be self-hosted, but that is 4 more
   containers (its server, Postgres, ClickHouse, Redis) to run and later
   deploy; plain JSON log lines would need tokens and cost computed by hand
   and have no trace view. LangSmith is the LangChain default, free at our
   size, and needs no hosting.
2. **Our steps traced in `app.py` only.** Rows 2 and 3 stay untouched; the
   API is where requests come in.
3. **Off by default.** No key, no tracing, no error: the unit tests, a fresh
   clone and CI all work without a LangSmith account.
4. **Cost from LangSmith's price table,** not computed by us; the eval keeps
   its own cost (row 4) so the two can be compared.
5. **What is sent to LangSmith:** questions, chunk texts and answers. The
   papers are open access; user questions could hold personal details, which
   is accepted for this project and noted for row 7.
6. **The eval is not traced step by step.** When tracing is on, its Claude
   calls (answers and judges) appear in LangSmith on their own; its search
   steps don't. Tracing the eval's steps is a later candidate.

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is checked is in [validation.md](validation.md).

### Tracing off (unit, no LangSmith, no cost)

**TR-1: with tracing off, the API behaves exactly as in row 5.**
- **Given** `LANGSMITH_TRACING` unset, and the fakes of row 5's unit tests.
- **When** `pytest tests/test_api.py -v` runs.
- **Then** AP-1 to AP-6 pass unchanged: 11 passed, and no request goes to
  LangSmith (the tests run with no LangSmith key).
- **Why:** tracing is an add-on; with it off, nothing may change, and the
  tests must not need an account.

### Tracing on (real LangSmith, by hand)

**TR-2: one request leaves one trace with steps, timings, tokens and cost.**
- **Given** the three variables in `.env`, Qdrant running, and the server
  started with `uvicorn neuro_rag.api.app:create_app --factory --port 8000`.
- **When** q01 is sent with row 5's curl.
- **Then** within a minute the project `neuro-rag` has one new trace named
  `ask`, with children `search` then `answer`, and a `ChatAnthropic` run
  inside `answer`; every run has a duration; the `ChatAnthropic` run shows
  input and output tokens and a cost above $0.
- **Why:** this is the row's "done when"; the cost per request is what the
  roadmap's cost target is set from.

**TR-3: a failing step shows as an error in the trace, and the client still gets the 503.**
- **Given** the server as in TR-2, then Qdrant stopped (`docker compose stop qdrant`).
- **When** q01 is sent.
- **Then** curl gets `{"detail":"Search is unavailable. Try again later."}`;
  the new trace's `search` run is marked as an error with the connection
  error, and it has no `answer` child.
- **Why:** a trace is most needed when something fails; it must say which
  step failed while the client still sees only the fixed sentence.

**TR-4: a wrong LangSmith key doesn't break requests.**
- **Given** the server started with `LANGSMITH_API_KEY=wrong` and Qdrant running.
- **When** q01 is sent.
- **Then** curl gets a 200 with an answer and sources; the server log may
  show a LangSmith warning; no trace appears.
- **Why:** observability must never take the product down.

**TR-5: no secret ends up in a trace.**
- **Given** the TR-2 trace.
- **When** its runs are opened in LangSmith (inputs, outputs, metadata).
- **Then** neither "sk-ant" nor the LangSmith key appears anywhere in them.
- **Why:** the roadmap's security target: keys never in logs or traces.

## Out of scope

- Tracing the eval's search steps (choice 6).
- Alerts, dashboards and sampling.
- Running LangSmith or another tracer ourselves.
- Returning a trace ID to the client.
- Setting the roadmap's cost target: done after the baseline, from these traces.
