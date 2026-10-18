# Generation: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples (chunks, question, expected result) are in the spec; this file says
where each one runs.

## Checks

- **Unit test:** a fake Claude client returns a prepared response; no API call,
  no cost. Tests the code around Claude: numbering, source list, errors.
- **Claude test:** the real Claude API with the spec's small chunks. Costs a few
  cents per run, so it is marked `llm` and run on purpose, not with every test run.
- **Corpus test:** the real index and real Claude; measures speed.
- **Inspection:** a person reads answers where only judgement can tell (did it
  answer from general knowledge?).

| Criterion | Kind | Test |
|---|---|---|
| GN-1 | Claude | `test_GN1_every_citation_points_at_a_sent_chunk_and_quotes_it` |
| GN-2 | unit | `test_GN2_markers_and_source_list_match` |
| GN-3 | unit | `test_GN3_two_chunks_from_one_page_share_one_source` |
| GN-4 | Claude + corpus + inspection | `test_GN4_uncovered_question_cites_nothing`; `test_GN4_off_topic_question_cites_nothing` (real index); read both answers |
| GN-5 | Claude + inspection | `test_GN5_false_premise_is_corrected`; read the answer |
| GN-6 | Claude | `test_GN6_instructions_in_a_chunk_are_not_followed` |
| GN-7 | unit | `test_GN7_no_chunks_means_no_call` |
| GN-8 | unit + Claude | `test_GN8_headings_are_removed` (fake response with a `#` line); `test_GN8_plain_paragraphs` |
| GN-9 | unit | `test_GN9_claude_unavailable_gives_clear_error` |
| GN-10 | unit | `test_GN10_refusal_gives_clear_message` |
| GN-11 | unit | `test_GN11_usage_is_returned` |
| GN-12 | corpus | `test_GN12_one_answer_takes_at_most_5s` |

GN-4 and GN-5 can't be fully decided by code: the test checks what code can
(GN-4: no citations; GN-5: the PMC3 chunk is cited), and a person reads the two
answers to confirm the rest.

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-18 | `hippocampus-v1`, `claude-haiku-5-5` (effort low) | all 12 criteria pass | First run failed GN-4: for an uncovered question Haiku said "not covered" but cited the chunk to describe what it did say, and asked the user to share a paper. Fixed by a stricter prompt rule (one sentence, no citation, no request for sources); all Claude tests then passed. Inspection: GN-4 (both examples) and GN-5 answers read correctly. GN-12: p50 3.4 s, p95 4.0 s, ~3,400 tokens per answer |
