# Tracing: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** row 5's `tests/test_api.py`, with tracing off through
  `tests/conftest.py`. No Langfuse, no cost.
- **Live test** (`tests/test_tracing_live.py`, marked `integration`, `llm`
  and `langfuse`): TR-6, one real request, about $0.003.
- **By hand:** the server with tracing on, curl, and the Langfuse web UI.
  Each request costs about $0.003.

| Criterion | Kind | Check |
|---|---|---|
| TR-1 | unit | `pytest tests/test_api.py -v`: 11 passed; no new trace in Langfuse |
| TR-2 | by hand | q01 with tracing on; open the trace: `ask` → `search`, `answer` → `ChatAnthropic`; durations, tokens, cost |
| TR-3 | by hand | stop Qdrant, send q01; 503 in curl, `search` at level ERROR in the trace |
| TR-4 | by hand | start the server with `LANGFUSE_SECRET_KEY=wrong`; q01 still gets a 200 |
| TR-5 | by hand | search the TR-2 trace's observations for "sk-ant" and "sk-lf" |
| TR-6 | live | `test_TR6_langfuse_cost_equals_ours` |

Commands:
```
pytest tests/test_api.py -v                                                    # TR-1
docker compose up -d
LANGFUSE_TRACING_ENABLED=true pytest tests/test_tracing_live.py -m langfuse -v # TR-6, about $0.003
uvicorn neuro_rag.api.app:create_app --factory --port 8000                     # TR-2, TR-5
curl -s localhost:8000/ask -H 'Content-Type: application/json' \
     -d '{"question": "How does m6A RNA methylation support hippocampus-dependent learning and memory?"}'
docker compose stop qdrant                                                     # TR-3
LANGFUSE_SECRET_KEY=wrong uvicorn neuro_rag.api.app:create_app --factory --port 8000   # TR-4
```

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-15 | v3, uncommitted | spec written (LangSmith) | not built yet |
| 2026-11-15 | v3, uncommitted | spec rewritten for Langfuse Cloud | keys already in `.env`; not built yet |
| 2026-11-16 | v3, uncommitted | TR-1 to TR-6 passed | see below |

### 2026-11-16 details

- **TR-1:** `pytest tests/test_api.py -v`: 11 passed; no new trace.
- **TR-6:** `test_TR6_langfuse_cost_equals_ours` passed: Langfuse's cost equals `cost(input, output)` to 6 decimals.
- **TR-2:** q01 left one trace: `ask` → `search` (5 hits), `answer` (text with `[1]` markers) →
  `ChatAnthropic` (raw text, no markers; our code adds them).

  | Observation | Duration | Tokens | Cost |
  |---|---|---|---|
  | ask | 3.14 s | | |
  | ChatAnthropic | | 2,293 in, 188 out | $0.003233 |

  Checked by hand: (2,293 × $1 + 188 × $5) / 1M = $0.003233.
- **TR-5:** no "sk-ant" or "sk-lf" in any observation. The public key (`pk-lf-…`) is in each
  observation's metadata, stamped by the SDK; it is not a secret (it only names the project).
- **TR-3:** with Qdrant stopped, curl got `{"detail":"Search is unavailable. Try again later."}`;
  the new trace shows `search` at level ERROR.
- **TR-4:** with `LANGFUSE_SECRET_KEY=wrong`, curl got a 200 with an answer; no trace appeared.
- **Noted for later (not a row 6 failure):** q01's answer ended with an uncited sentence
  ("LTP is a form of synaptic plasticity thought to be important for memory formation."), from
  Claude's own knowledge. The faithfulness judge (EV-11) and rows 10–12 are where this is measured.
