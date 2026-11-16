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
| 2026-11-16 | v3, `24ba0d8` | free tests and EV-10/EV-11 passed; baseline run | folder `eval/results/2026-11-16_1939_baseline/` |

### Baseline, 2026-11-16

50 runs, 0 failed, 0 judge calls failed, $0.26 total.

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.67 | 0.97 | 0.89 | 0.67 | 0.86 | 1.00 | 0.00 | 1.7 | 3.9 | 0.0052 |

Read from the reasons in `report.md`:

- **6 wrong verdicts, all false "not covered":** q06, q12, q14, q21, q23, q36. The papers cover
  them, but the answer said they don't. Several are casual phrasings ("lifting weights",
  "pictures", "a pill after studying"): a search and question-rewriting problem (rows 8 and 9).
- **12 partial:** right but missing details from the reference (rescue experiments, mechanisms).
- **1 unfaithful run:** q24, a sentence about lesioned animals not supported by its source.
- **Borderline (6 runs) cites papers 0.00:** all six said "not covered"; reported only (row 10).
- **Off-domain and out-of-corpus:** all 8 correctly said "not covered".
