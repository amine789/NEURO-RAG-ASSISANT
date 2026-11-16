# Tracing: spec

Roadmap row 6: every request is traced: its steps, timings, tokens and cost.

## Goal

Every `POST /ask` leaves one trace in Langfuse: a tree with the request at
the top, then search, then answer with Claude's call inside it. Each step has
its duration; the Claude call has its input and output tokens and its cost.
Tracing never changes what the client gets: if Langfuse is down or a key is
wrong, the request still answers.

## In and out

- **In:** the API from row 5, unchanged for the client, and these variables in
  `.env` (gitignored; the three keys are already there from v2):
  ```
  LANGFUSE_PUBLIC_KEY=<pk-lf-…>
  LANGFUSE_SECRET_KEY=<sk-lf-…>
  LANGFUSE_BASE_URL=https://cloud.langfuse.com
  ```
- **Out:** one trace per request in the Langfuse project:
  ```
  ask                      duration, the question in, the answer out
  ├── search               duration, the question in, the 5 hits out
  └── answer               duration, the question and hits in, the answer out
      └── ChatAnthropic    duration, input/output tokens, cost (a generation, from the LangChain callback)
  ```
- **Runs:** as row 5's server; nothing new to start.

## Settings

| Setting | Value | Why |
|---|---|---|
| tool | Langfuse Cloud, free Hobby plan | decided 2026-11-15: open source, keys already in `.env`, nothing to host; could be self-hosted later for free |
| our steps | `@observe(name=...)` from `langfuse` | one decorator per step |
| Claude call | `CallbackHandler()` from `langfuse.langchain`, attached with `make_llm().with_config(callbacks=[...])` | LangChain hands each call (tokens, model, duration) to the callback; `with_config` attaches it to the LLM object, so `answer.py` doesn't change |
| on or off | on when the keys are set (Langfuse's default); `LANGFUSE_TRACING_ENABLED=false` turns it off | the unit tests set it to `false` in `tests/conftest.py`, so they never send anything |
| keys | in `.env`, loaded by `config.py`'s `load_dotenv()` | never printed, logged or committed; a Kubernetes Secret in row 7 |
| cost | Langfuse's own price table for `claude-haiku-4-5` ($1 / $5 per million) | TR-6 checks it equals our formula (row 4's `cost`); if it shows no cost, the price is added once in Langfuse's model settings |
| sending | Langfuse's client sends from a background thread | the request doesn't wait for Langfuse, and a Langfuse failure is a log warning, not an error |
| free plan limits | about 50,000 units a month, kept 30 days (to check in the Langfuse settings) | far above our use: a request is 4 observations |

## How it is built

### Files

| File | Contents |
|---|---|
| `pyproject.toml` | dependencies gain `langfuse`; markers gain `langfuse: sends traces to and reads them from real Langfuse` |
| `src/neuro_rag/api/app.py` | `build_pipeline` attaches the callback to the LLM; `create_app` wraps the two steps and `ask` with `@observe` |
| `tests/conftest.py` | `os.environ.setdefault("LANGFUSE_TRACING_ENABLED", "false")`: tests send nothing unless a run sets it to `true` |
| `tests/test_tracing_live.py` | TR-6: Langfuse's cost against ours, marked `integration`, `llm` and `langfuse` |

`search.py`, `answer.py` and the eval don't change.

### `api/app.py` changes

In `build_pipeline`:

```python
llm = make_llm().with_config(callbacks=[CallbackHandler()])
```

In `create_app`, after the `build_pipeline()` line:

```python
@observe(name="search")
def traced_search(question):
    return search_fn(question)

@observe(name="answer")
def traced_answer(question, hits):
    return answer_fn(question, hits)
```

and `ask` gets `@observe(name="ask")` under `@app.post("/ask")`, and calls
`traced_search` / `traced_answer` instead of `search_fn` / `answer_fn`.

- **Wrapping in `create_app`, not in `build_pipeline`,** so the unit tests'
  fakes go through the same wrappers: AP-1 to AP-6 exercise the traced path
  with tracing off.
- **Wrapping with a small `def`, not `observe(...)(search_fn)` directly,**
  because the tests pass objects (`FakeSearch()`) rather than functions, and
  a `def` has the name and signature the decorator reads.
- **`@observe` keeps `ask`'s signature** (it uses `functools.wraps`), so
  FastAPI still sees `request: AskRequest` and validates the body.
- **The callback nests under the current step:** the `ChatAnthropic`
  generation appears inside `answer`, because the call happens while
  `answer`'s observation is open.
- **A failing step shows as an error in the trace:** `@observe` records the
  exception and re-raises it, so `ask`'s `try/except` still turns it into the
  503.

**What a trace holds for q01** (illustrative; the real numbers are recorded
in validation.md after the first trace):

| Observation | Duration | In | Out | Tokens | Cost |
|---|---|---|---|---|---|
| ask | 3.1 s | the question | `AskResponse` | | |
| search | 0.1 s | the question | 5 `Hit`s | | |
| answer | 3.0 s | the question, 5 `Hit`s | `Answer` | | |
| ChatAnthropic | 2.9 s | system prompt, 5 documents, question | the text blocks | 2,293 in, 179 out | $0.003188 |

## Choices, accepted 2026-11-15

1. **Langfuse Cloud, free Hobby plan** (switched from LangSmith the same
   day: the keys were already in `.env` from v2, and the code difference is
   one line). Self-hosted Langfuse would be 4 more containers (its server,
   Postgres, ClickHouse, Redis); Arize Phoenix one more container; plain JSON
   log lines would need tokens and cost computed by hand and have no trace
   view.
2. **Our steps traced in `app.py` only.** Rows 2 and 3 stay untouched; the
   API is where requests come in.
3. **Tests send nothing.** `tests/conftest.py` turns tracing off unless a run
   asks for it; the app itself traces whenever the keys are set.
4. **Cost from Langfuse's price table, checked against ours.** The eval
   keeps its own formula (row 4: `(in × $1 + out × $5) / 1M`); TR-6 checks
   Langfuse's cost for a real call equals it, so the trace numbers and the
   eval numbers can be compared.
5. **What is sent to Langfuse:** questions, chunk texts and answers. The
   papers are open access; user questions could hold personal details, which
   is accepted for this project and noted for row 7.
6. **The eval is not traced.** It builds its own LLM without the callback.
   Tracing the eval is a later candidate.

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is checked is in [validation.md](validation.md).

### Tracing off (unit, no Langfuse, no cost)

**TR-1: with tracing off, the API behaves exactly as in row 5.**
- **Given** `tests/conftest.py` setting `LANGFUSE_TRACING_ENABLED=false`, and
  the fakes of row 5's unit tests.
- **When** `pytest tests/test_api.py -v` runs.
- **Then** AP-1 to AP-6 pass unchanged: 11 passed, and no new trace appears in
  Langfuse.
- **Why:** tracing is an add-on; with it off, nothing may change, and the
  tests must not fill the project with fake traces.

### Tracing on (real Langfuse, by hand)

**TR-2: one request leaves one trace with steps, timings, tokens and cost.**
- **Given** the keys in `.env`, Qdrant running, and the server started with
  `uvicorn neuro_rag.api.app:create_app --factory --port 8000`.
- **When** q01 is sent with row 5's curl.
- **Then** within a minute Langfuse has one new trace named `ask`, with
  children `search` then `answer`, and a `ChatAnthropic` generation inside
  `answer`; every observation has a duration; the generation shows input and
  output tokens and a cost above $0.
- **Why:** this is the row's "done when"; the cost per request is what the
  roadmap's cost target is set from.

**TR-3: a failing step shows as an error in the trace, and the client still gets the 503.**
- **Given** the server as in TR-2, then Qdrant stopped (`docker compose stop qdrant`).
- **When** q01 is sent.
- **Then** curl gets `{"detail":"Search is unavailable. Try again later."}`;
  the new trace's `search` observation has level ERROR with the connection
  error, and there is no `answer` observation.
- **Why:** a trace is most needed when something fails; it must say which
  step failed while the client still sees only the fixed sentence.

**TR-4: a wrong Langfuse key doesn't break requests.**
- **Given** the server started with `LANGFUSE_SECRET_KEY=wrong` and Qdrant running.
- **When** q01 is sent.
- **Then** curl gets a 200 with an answer and sources; the server log may
  show a Langfuse warning; no trace appears.
- **Why:** observability must never take the product down.

**TR-5: no secret ends up in a trace.**
- **Given** the TR-2 trace.
- **When** its observations are opened in Langfuse (input, output, metadata).
- **Then** neither "sk-ant" nor "sk-lf" appears anywhere in them.
- **Why:** the roadmap's security target: keys never in logs or traces.

### Cost (real Langfuse and Claude, automated)

**TR-6: Langfuse's cost for a Claude call equals ours.**
- **Given** the keys in `.env`, Qdrant running, the test run with
  `LANGFUSE_TRACING_ENABLED=true`, and `t0` the time just before the request.
- **When** `TestClient(create_app())` gets `POST /ask` with q01, then
  `get_client().flush()` sends the traces, then
  `get_client().api.observations.get_many(type="GENERATION",
  from_start_time=t0, fields="core,basic,usage")` is read every 5 s for up
  to 60 s until it returns a generation with a `total_cost`.
- **Then** that generation's `total_cost` equals
  `cost(usage_details["input"], usage_details["output"])` from
  `neuro_rag.eval.run`, to 6 decimals; for 2,293 in and 179 out that is
  0.003188.
- **Why:** the eval's cost and the traces' cost must describe the same thing;
  a wrong price in either would make one of them lie. The test skips unless
  `LANGFUSE_TRACING_ENABLED` is `true`; one call, about $0.003.

## Out of scope

- Tracing the eval (choice 6).
- Alerts, dashboards and sampling.
- Self-hosting Langfuse.
- Returning a trace ID to the client.
- Setting the roadmap's cost target: done after the baseline, from these traces.
