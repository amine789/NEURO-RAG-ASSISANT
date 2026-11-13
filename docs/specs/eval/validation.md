# Eval and baseline score: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test** (`tests/test_eval.py`): fake `search_fn`, `answer_fn` and
  judge LLM, questions written in the test or picked from
  `eval/questions.jsonl`, a temporary results folder. No API call, no Qdrant.
- **LLM test** (`tests/test_eval_llm.py`, marked `llm`): the two judges on
  real Haiku 4.5. Five calls, about $0.005.
- **Full run:** the baseline, run by hand: 50 runs, about $0.25 and 4
  minutes.

| Criterion | Kind | Test |
|---|---|---|
| EV-1 | unit | `test_EV1_every_question_run_repeats_times` |
| EV-2 | unit | `test_EV2_failing_run_recorded_and_eval_continues` |
| EV-3 | unit | `test_EV3_cost_estimate_printed_before_any_call` |
| EV-4 | unit | `test_EV4_search_hits_from_expected_sources` |
| EV-5 | unit | `test_EV5_cites_expected_from_answer_sources` |
| EV-6 | unit | `test_EV6_not_covered_for_decline_questions` |
| EV-7 | unit | `test_EV7_only_answered_questions_judged_for_correctness` |
| EV-8 | unit | `test_EV8_cost_from_tokens` |
| EV-9 | unit | `test_EV9_judge_failure_recorded_run_kept` |
| EV-10 | llm | `test_EV10_correctness_judge_tells_three_apart` |
| EV-11 | llm | `test_EV11_faithfulness_judge_catches_unsupported_claim` |
| EV-12 | unit | `test_EV12_report_overall_and_by_type` |
| EV-13 | unit | `test_EV13_report_lists_not_correct_with_reasons` |
| EV-14 | full run | run it; copy the `all` row below |

Commands:
```
pytest tests/test_eval.py -v
pytest tests/test_eval_llm.py -m llm -v
python -m neuro_rag.eval.run --name baseline
```

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-09 | v3, uncommitted | spec written | not built yet |
