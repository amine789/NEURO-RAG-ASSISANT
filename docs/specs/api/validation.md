# API: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** FastAPI's test client and a fake pipeline; no Qdrant, no Claude.
- **Service test:** the real service with the real index and Claude, started by
  the test. Marked `llm`; costs about $0.02 (40 answers).

| Criterion | Kind | Test |
|---|---|---|
| AP-1 | unit | `test_AP1_question_gets_answer_sources_and_trace_id` |
| AP-2 | unit | `test_AP2_uncovered_question_is_an_answer` |
| AP-3 | unit | `test_AP3_empty_question_is_rejected` |
| AP-4 | unit | `test_AP4_question_over_1000_characters_is_rejected` |
| AP-5 | unit | `test_AP5_qdrant_down_gives_503` |
| AP-6 | unit | `test_AP6_claude_unavailable_gives_503` |
| AP-7 | unit | `test_AP7_unexpected_error_gives_500_and_reveals_nothing` |
| AP-8 | service (fake generator) | `test_AP8_models_load_at_startup` |
| AP-9 | unit + service | `test_AP9_health_ok`, `test_AP9_health_unavailable`, `test_AP9_health_with_real_qdrant_up_and_down` |
| AP-10 | service | `test_AP10_answer_takes_at_most_6s` (also prints p95 with 4 at a time) |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-20 | `hippocampus-v1`, reranker on (20, ONNX), `claude-haiku-5-5` | all 10 criteria pass | First AP-8 run failed (first request 5.78 s, second 4.29 s): Claude's call-to-call variation, not model loading. AP-8 now uses a fake in place of Claude and passes. AP-10 timings not recorded |
