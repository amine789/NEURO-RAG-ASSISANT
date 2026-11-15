# API: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test** (`tests/test_api.py`): FastAPI's `TestClient` on
  `create_app(fake_search, fake_answer)`. The fakes record what they got. No
  Qdrant, no API call, no cost.
- **Live test** (`tests/test_api_live.py`, marked `integration` and `llm`):
  `TestClient(create_app())` on real Qdrant and Claude Haiku 4.5. One call,
  about $0.003.
- **Server:** run by hand with uvicorn and curl.

| Criterion | Kind | Test |
|---|---|---|
| AP-1 | unit | `test_AP1_answer_and_sources_as_json` |
| AP-2 | unit | `test_AP2_question_stripped_and_hits_passed` |
| AP-3 | unit | `test_AP3_bad_question_422_nothing_searched` |
| AP-4 | unit | `test_AP4_search_failure_503` |
| AP-5 | unit | `test_AP5_answer_failure_503` |
| AP-6 | unit | `test_AP6_health_calls_nothing` |
| AP-7 | live | `test_AP7_real_app_answers_q01` |
| AP-8 | server | start uvicorn; curl `/ask` with q01 and `/health`; read the log |

Commands:
```
pip install -e ".[dev]"
pytest tests/test_api.py -v
docker compose up -d
pytest tests/test_api_live.py -m "integration and llm" -v
uvicorn neuro_rag.api.app:create_app --factory --port 8000
```

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-13 | v3, uncommitted | spec written | not built yet |
| 2026-11-15 | v3, uncommitted | **AP-1 to AP-8 passed** | `pytest tests/test_api.py -v` (11 unit tests, fakes) and AP-7 (`pytest tests/test_api_live.py -m "integration and llm" -v`, one real request). AP-8 by hand: uvicorn on port 8000; curl q01 returned 3 sentences each ending "[1]", one source PMC6226095 page 6 with its PMC link, only `answer` and `sources` in the body; `/health` returned `{"status":"ok"}`; no API key in the server log |
