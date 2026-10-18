# Eval: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** fake retriever, fake generator and fake judge; no API calls.
  Tests the runner, the code measures and the report.
- **Judge test:** the real judge model on the spec's two examples (EV-8, EV-9).
  Marked `llm`; costs a fraction of a cent.
- **Human check:** a person grades 20 runs by hand (EV-11).
- **Full run:** the baseline itself, on all 54 questions.

| Criterion | Kind | Test |
|---|---|---|
| EV-1 | unit | `test_EV1_every_question_runs_the_requested_number_of_times` |
| EV-2 | unit | `test_EV2_failing_run_is_recorded_and_the_eval_continues` |
| EV-3 | unit | `test_EV3_interrupted_eval_resumes` |
| EV-4 | unit | `test_EV4_cost_is_shown_before_any_call` |
| EV-5 | unit | `test_EV5_retrieval_hit_from_expected_sources` |
| EV-6 | unit | `test_EV6_cites_expected_from_source_list` |
| EV-7 | unit | `test_EV7_not_covered_when_nothing_is_cited` |
| EV-8 | judge | `test_EV8_partial_answer_is_judged_partial` |
| EV-9 | judge | `test_EV9_unsupported_claim_is_judged_unfaithful` |
| EV-10 | unit | `test_EV10_judge_failure_keeps_the_run` |
| EV-11 | human | `eval/judge_check.py` picks 20 runs and writes a grading sheet; the person fills it; the script prints the agreement |
| EV-12 | unit | `test_EV12_report_has_every_score_by_type` |
| EV-13 | unit | `test_EV13_two_reports_compare_side_by_side` |
| EV-14 | unit | `test_EV14_rerank_run_is_labelled` |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-18 | `hippocampus-v1`, baseline | EV-1 to EV-10, EV-12, EV-13 pass; EV-11 not done | 162 runs, 0 failed, ~$0.08. English questions: correctness 0.68, faithful 0.80, retrieval hit 0.88, cites expected 0.84, not covered 1.00, p95 4.8 s. Weakest: `casual_loose_terms` (retrieval hit 0.25), multilingual (0). Judge seen flagging a supported claim (q06 #1); EV-11 left open: no expert grader available. Borderline questions (q45–q50) are not measured yet; all six said "not covered" |
