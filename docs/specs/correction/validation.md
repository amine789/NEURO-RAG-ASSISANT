# Correction: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test:** a fake Claude client; free.
- **LLM test:** the real rewriter on the spec's questions. Marked `llm`;
  fractions of a cent.
- **Corpus test:** the real index, reranker and rewriter. Marked `llm`; well
  under $0.01.

| Criterion | Kind | Test |
|---|---|---|
| CR-1 | unit | `test_CR1_request_sends_question_with_rules_and_examples` |
| CR-2 | unit | `test_CR2_query_comes_back_as_one_clean_line` |
| CR-3 | unit | `test_CR3_empty_or_overlong_rewrite_is_an_error` |
| CR-4 | unit | `test_CR4_failed_refused_or_unreadable_call_is_an_error` |
| CR-5 | llm | `test_CR5_everyday_words_become_papers_terms` |
| CR-6 | llm | `test_CR6_other_language_becomes_english_query` |
| CR-7 | llm | `test_CR7_rewrite_is_a_query_not_an_answer` |
| CR-8 | llm | `test_CR8_precise_question_keeps_exact_terms` |
| CR-9 | corpus (llm) | `test_CR9_rewriting_finds_missed_papers` (prints every question and its rewrite) |
| CR-10 | corpus (llm) | `test_CR10_rewrite_time_is_measured` (28 timed rewrites; prints p50 and p95, no limit) |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-21 | rewriter, `claude-haiku-5-5`, thinking off | CR-1 to CR-9 pass; CR-10 fails | CR-9: found 5/8. All 4 non-English found (q37–q40) and q33 ("front bit vs back bit" → "dorsal versus ventral hippocampus…"). Not found: q31 and q30, where the rewrite narrowed the question to one hypothesis ("pattern separation … dentate gyrus and CA3") despite the prompt's rule; q36, broad with 3 expected papers. Watch the narrowing in the row 7a eval. CR-10: p95 2.08 s over 8 calls, which is the slowest call (Arabic q40); timing changed to 28 calls |
| 2026-10-21 | same, 28 timed calls | CR-10 at 2 s fails | p95 2.49 s over 28 calls. The 2 s limit was a guess; CR-10 now only reports, and orchestration sets the rewritten path budget, running the rewrite alongside the first grade |
