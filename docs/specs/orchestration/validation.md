# Orchestration: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** fakes for every step and the recording tracer; free.
- **Eval:** the corrective system on the 54 questions, compared with the
  reranker run (eval spec, next).

| Criterion | Kind | Test |
|---|---|---|
| OR-1 | unit | `test_OR1_passing_chunks_answered_at_once` |
| OR-2 | unit | `test_OR2_failed_grade_rewritten_and_answered_from_papers` |
| OR-3 | unit | `test_OR3_two_failed_grades_end_with_couldnt_find` |
| OR-4 | unit | `test_OR4_grade_rewrite_and_generate_run_together` |
| OR-5 | unit | `test_OR5_passing_question_doesnt_wait_for_rewrite` |
| OR-6 | unit | `test_OR6_grading_error_counts_as_passed` |
| OR-7 | unit | `test_OR7_rewrite_error_ends_with_couldnt_find` |
| OR-8 | unit | `test_OR8_without_grader_flow_is_row_5s` |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-21 | v2, uncommitted | OR-1 to OR-8 pass | unit tests with fakes; the timing checks (OR-3, OR-4, OR-5) confirm grade, rewrite and generate run in parallel. OB-1 and the API tests still pass with the new pipeline. Eval still to run. |
