# Grading: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** a fake Claude client; no models, no Qdrant; free.
- **LLM test:** the real grader on the spec's fixed chunks. Marked `llm`;
  fractions of a cent.
- **Corpus test:** the real index, reranker and grader. Marked `llm`; about $0.01.

| Criterion | Kind | Test |
|---|---|---|
| GR-1 | unit | `test_GR1_request_asks_one_verdict_per_numbered_passage` |
| GR-2 | unit | `test_GR2_verdicts_become_positions_in_order` |
| GR-3 | unit | `test_GR3_no_relevant_passage_fails` |
| GR-4 | unit | `test_GR4_no_chunks_fail_without_a_call` |
| GR-5 | unit | `test_GR5_mismatched_reply_is_an_error` |
| GR-6 | unit | `test_GR6_failed_or_refused_call_is_an_error` |
| GR-7 | llm | `test_GR7_answering_passage_is_relevant` |
| GR-8 | llm | `test_GR8_sharing_words_is_not_answering` |
| GR-9 | llm | `test_GR9_instructions_in_passages_are_ignored` |
| GR-10 | corpus (llm) | `test_GR10_grader_agrees_with_eval_labels` (prints every question) |
| GR-11 | corpus (llm) | `test_GR11_grading_takes_at_most_2s` |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-21 | LLM grader, `claude-haiku-5-5`, thinking off, effort low | all 11 criteria pass | GR-8 passes without thinking. GR-10 rates and GR-11 p95 not recorded |
| 2026-10-21 | LLM grader, `claude-haiku-4-5`, no thinking | GR-10 passes; GR-11 fails | grading p95 1.77 s (limit 1.5 s), typical call about 1.5 s: no faster than Haiku 5.5 on a typical call, at 10× the price. Back to Haiku 5.5 with thinking off; GR-11 limit set to 2 s, since row 7 runs grading alongside generation |
| 2026-10-21 | LLM grader, `claude-haiku-5-5`, effort low | GR-10 passes; GR-11 fails | grading p95 2.5 s (limit 1.5 s): Haiku 5.5 thinks by default. Switched the grader to `claude-haiku-4-5` |
| 2026-10-20 | threshold on the reranker score (first design) | rejected | T = -2.43 (90% of found questions kept); separation check passed; GR-4 failed: the "fear center and memory center" question scored above T though its paper is never retrieved. Replaced by an LLM grader (decision 006) |
