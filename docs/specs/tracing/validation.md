# Tracing: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** row 5's `tests/test_api.py`, run with tracing off. No
  LangSmith, no cost.
- **By hand:** the server with tracing on, curl, and the LangSmith web UI
  (project `neuro-rag`). Each request costs about $0.003.

| Criterion | Kind | Check |
|---|---|---|
| TR-1 | unit | `pytest tests/test_api.py -v` with `LANGSMITH_TRACING` unset: 11 passed |
| TR-2 | by hand | q01 with tracing on; open the trace: `ask` → `search`, `answer` → `ChatAnthropic`; durations, tokens, cost |
| TR-3 | by hand | stop Qdrant, send q01; 503 in curl, `search` marked as an error in the trace |
| TR-4 | by hand | start the server with `LANGSMITH_API_KEY=wrong`; q01 still gets a 200 |
| TR-5 | by hand | search the TR-2 trace's runs for "sk-ant" and the LangSmith key |

Commands:
```
LANGSMITH_TRACING= pytest tests/test_api.py -v
docker compose up -d
uvicorn neuro_rag.api.app:create_app --factory --port 8000
curl -s localhost:8000/ask -H 'Content-Type: application/json' \
     -d '{"question": "How does m6A RNA methylation support hippocampus-dependent learning and memory?"}'
docker compose stop qdrant                                            # TR-3
LANGSMITH_API_KEY=wrong uvicorn neuro_rag.api.app:create_app --factory --port 8000   # TR-4
```

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-15 | v3, uncommitted | spec written | not built yet |
