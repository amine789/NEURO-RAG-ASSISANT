# Observability: spec

What this module must do. Written when its row in [ROADMAP.md](../../ROADMAP.md)
starts.

## Goal

Trace every request: steps, prompts, tokens, latency and cost.

## In and out

- **In:** each `POST /ask` request, and the steps the pipeline runs for it.
- **Out:** one trace per request in Langfuse Cloud (the choice in ARCHITECTURE
  section 1), sent in the background so it never slows the answer:

```
trace "ask"   input: question   output: answer + source pmcids   id → returned to the client
 ├─ span "retrieve"     the 20 fused chunks: chunk_id, pmcid, page, score       duration
 ├─ span "rerank"       the 5 kept chunks, with the reranker's scores           duration
 └─ generation "generate"   model, the 5 chunk texts sent, the answer,          duration
                            input / output tokens, cost in dollars
```

- **Reads:** `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and the Langfuse host
  from the environment (`.env` locally, never committed).

## Settings

| Setting | Start | Why |
|---|---|---|
| backend | Langfuse Cloud, its Python SDK | ARCHITECTURE section 1: self-hosting needs its own database, analytics store, cache and storage |
| what is sent | question, chunk texts, answer, timings, tokens, cost | enough to see why an answer was wrong; the trade-off (questions leave the server) is in ARCHITECTURE |
| cost | computed by us from the tokens and Haiku's price ($0.10 / $0.50 per 1M) | the same numbers the eval reports; doesn't depend on Langfuse knowing the model's price |
| sampling | every request | traffic is small; nothing to save by dropping traces |

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
Most examples use a recording tracer, a fake that keeps every trace and span in
a list instead of sending them, and the same fake pipeline as the API spec: one
chunk from paper PMC1, page 3, "Place cells in the hippocampus fire when the
animal is at a specific location." How each one is run is in
[validation.md](validation.md).

### What a trace contains

**OB-1: one request makes one trace, with its three steps in order.**
- **Given** the API with the recording tracer and the fake pipeline.
- **When** a client sends `POST /ask` with `{"question": "What do place cells do?"}`.
- **Then** exactly one trace was recorded, named "ask". Its input is the
  question, its output is the answer text and the source `pmcid`s (["PMC1"]).
  It has three steps, in this order: "retrieve", "rerank", "generate", each
  with a start and end time. The response's `trace_id` is this trace's ID.
- **Why:** a slow or wrong answer is investigated by opening its trace; the
  steps show where the time went, and the ID in the response is how a user's
  report is matched to its trace.

**OB-2: the retrieve and rerank steps show which chunks were chosen.**
- **Given** the API with the recording tracer and the fake pipeline.
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the "retrieve" step's output lists every fused chunk with its
  `chunk_id`, `pmcid`, `page` and score, and the "rerank" step's output lists
  the chunks kept, with the reranker's scores. Chunk texts are not repeated
  here; they appear once, in "generate".
- **Why:** when an answer is wrong, the first question is whether the right
  chunk was found (retrieve) and then whether it was kept (rerank). Repeating
  the texts three times would triple every trace's size for nothing.

**OB-3: the generate step records the model, tokens and cost.**
- **Given** the API with the recording tracer, and a fake pipeline whose
  Claude call reports 3,000 input tokens and 400 output tokens.
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the "generate" step records the model `claude-haiku-5-5`, the chunk
  texts it was sent, the answer, 3,000 input and 400 output tokens, and a cost
  of $0.0005 (3,000 × $0.10 / 1M + 400 × $0.50 / 1M).
- **Why:** cost per request is a system target in the ROADMAP ("measured per
  request from traces"); without tokens and cost per trace there is nothing to
  measure it from.

**OB-4: a failed request is traced, with its error.**
- **Given** the API with the recording tracer, and a fake pipeline whose
  retrieve step raises `RetrievalError("Qdrant is unreachable")`.
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the response is `503` (API spec, AP-5), and one trace was still
  recorded: its "retrieve" step is marked as an error with the message "Qdrant
  is unreachable", and there is no "rerank" or "generate" step. The response's
  `trace_id` is this trace's ID.
- **Why:** failures are exactly the requests someone will want to look up;
  a trace that disappears when something breaks is useless when it matters.

### Tracing never breaks answering

**OB-5: Langfuse unreachable doesn't slow or break an answer.**
- **Given** the real service, configured with a Langfuse host that refuses
  connections (`http://localhost:9`).
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the response is `200` with an answer, it arrives no more than
  0.5 s later than with tracing turned off, and the service log has a warning
  that traces couldn't be sent.
- **Why:** tracing is for us, not for the user; Langfuse Cloud being down must
  never take the product down with it.

**OB-6: without Langfuse keys, tracing is off and nothing fails.**
- **Given** the service started with no `LANGFUSE_PUBLIC_KEY` or
  `LANGFUSE_SECRET_KEY` in the environment.
- **When** a client sends `{"question": "What do place cells do?"}`.
- **Then** the response is `200` with an answer and a `trace_id` (generated
  locally, so error reports still have an ID), and the log says once, at
  startup, that tracing is off.
- **Why:** tests, the eval and a fresh checkout run without Langfuse keys;
  they must work without them, and the startup line makes a forgotten key on
  the server obvious.

### Secrets

**OB-7: no API key ever appears in a trace.**
- **Given** the API with the recording tracer, and the environment holding
  `ANTHROPIC_API_KEY=sk-ant-test-123`, `LANGFUSE_SECRET_KEY=sk-lf-test-456`
  and `QDRANT_API_KEY=qd-test-789`.
- **When** a client sends `{"question": "What do place cells do?"}`, and once
  more with the fake pipeline raising `GenerationError`.
- **Then** none of "sk-ant-test-123", "sk-lf-test-456" or "qd-test-789"
  appears anywhere in the recorded traces, their steps, inputs, outputs,
  metadata or error messages.
- **Why:** traces leave the server for Langfuse Cloud. The ROADMAP's security
  target says keys are never in logs or traces; an error message that includes
  a request header would break that silently.

### In Langfuse Cloud

**OB-8: a real request shows up in Langfuse, complete.**
- **Given** the real service with the real index, Claude, and Langfuse keys.
- **When** a person sends `{"question": "What do place cells do?"}` and opens
  the `trace_id` from the response in Langfuse Cloud.
- **Then** the trace is there within a minute, with the three steps, their
  durations, the model, tokens and cost, and the cost matches the eval's cost
  for a similar answer (about $0.0005).
- **Why:** the recording tracer proves what the code sends; only a real
  request proves Langfuse receives it and shows it the way the investigation
  needs.

## Out of scope

- Dashboards and alerts in Langfuse (after deployment, once there is traffic).
- Sending eval runs to Langfuse; the eval keeps its own `runs.jsonl`.
- User feedback (thumbs up/down) on traces (with the UI, row 9, if wanted).
- Tracing the offline index build.
