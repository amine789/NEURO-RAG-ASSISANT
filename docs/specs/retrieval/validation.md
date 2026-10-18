# Retrieval: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples (data, question, expected result) are in the spec; this file says
where each one runs.

## Checks

- **Unit test:** no Qdrant, no models; fakes stand in for both.
- **Integration test:** a real local Qdrant and the test chunks from the spec,
  written with ingest's own code and the real encoders.
- **Corpus test:** the real `hippocampus` index; skipped if it isn't built.
- **Code reading:** checked by a person.

| Criterion | Kind | Test |
|---|---|---|
| RT-1 | integration | `test_RT1_results_are_sorted_limited_and_complete` |
| RT-2 | integration | `test_RT2_chunk_found_by_both_searches_appears_once_first` |
| RT-3 | integration | `test_RT3_exact_rare_term_is_found` |
| RT-4 | corpus | `test_RT4_meaning_is_found_without_shared_words` |
| RT-5 | integration | `test_RT5_unknown_words_still_give_results` |
| RT-6 | integration | `test_RT6_same_question_gives_same_results` |
| RT-7 | corpus | `test_RT7_known_papers_are_found` |
| RT-8 | code reading | retrieval imports `neuro_rag.encoders` and creates no model |
| RT-9 | integration | `test_RT9_new_build_is_picked_up_without_code_change` |
| RT-10 | unit | `test_RT10_encoders_load_once` |
| RT-11 | unit | `test_RT11_empty_question_is_rejected_before_qdrant` |
| RT-12 | unit + integration | `test_RT12_qdrant_unreachable_gives_clear_error`, `test_RT12_missing_alias_gives_clear_error` |
| RT-13 | corpus | `test_RT13_one_retrieval_takes_at_most_500ms` |

### RT-7 known papers: what is reported

- **Questions:** 20, in `tests/data/known_papers.jsonl`, each with its paper's
  `pmcid`. Drafted from the catalog, reviewed by hand before the test counts.
- **top 5:** how many of the 20 have their paper in the top 5. Pass: at least 18.
- **candidates:** how many have their paper anywhere among the candidates (the
  20 by meaning plus the 20 by keywords, before fusion). Reported only.
- **If top 5 fails:** a high candidates number means the paper is found but
  ranked too low, which a reranker fixes (row 6). A low one means it is never
  found, so the encoder or chunking is the problem, not the ranking.

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-18 | `hippocampus-v1` | all 13 criteria pass | RT-7: top 5 18/20, candidates 19/20. Missed PMC6560047 (in candidates: ranked too low, a reranker could fix it) and PMC9613775 (not in candidates: everyday words vs. "amygdala", "phase code"; needs query rewrite, row 7). RT-13: p50 17 ms, p95 20 ms |
