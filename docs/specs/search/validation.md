# Search: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test** (`tests/test_search.py`): SE-4 and SE-9, with counting fake
  embedders and a counting fake client. No Qdrant.
- **Integration test** (`tests/test_search.py`, marked `integration`): the
  `papers` collection from row 1's build in the running Qdrant
  (`docker compose up -d`), and the real embedders. These tests read the
  collection and never write to it.
- **Command and script:** run by hand.

| Criterion | Kind | Test |
|---|---|---|
| SE-1 | integration | `test_SE1_dense_top_5_best_first` |
| SE-2 | integration | `test_SE2_hit_carries_citation_fields` |
| SE-3 | integration | `test_SE3_chunk_text_finds_itself` |
| SE-4 | unit | `test_SE4_empty_question_refused` |
| SE-5 | integration | `test_SE5_k_sets_number_of_hits` |
| SE-6 | integration | `test_SE6_off_topic_still_returns_hits` |
| SE-7 | integration | `test_SE7_hybrid_hits_come_from_either_list` |
| SE-8 | integration | `test_SE8_hybrid_finds_rare_term` |
| SE-9 | unit | `test_SE9_unknown_mode_refused` |
| SE-10 | command | run both; compare the dense first line with the spec; run with no question |
| SE-11 | script | run it; check the counts are out of 36 and 4, and the CSV has 80 rows |

Commands:
```
pytest tests/test_search.py -m "not integration" -v
docker compose up -d && pytest tests/test_search.py -m integration -v
python -m neuro_rag.retrieval.search "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
python -m neuro_rag.retrieval.search --hybrid "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
python -m neuro_rag.retrieval.search; echo $?
python scripts/compare_search.py
```

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-03 | v3, uncommitted | spec written (dense only) | not built yet |
| 2026-11-03 | v3, uncommitted | spec rewritten: dense and hybrid, compared | needs row 1's rebuild with the `bm25` vector first |
| 2026-11-04 | v3, uncommitted | rebuilt with `bm25`; both modes run (SE-10 by hand) | dense q01 lines match the spec; hybrid q01: PMC11319347-p1-c0, PMC6226095-p6-c1, PMC6226095-p6-c2, PMC11319347-p9-c5, PMC13144532-p3-c9 |
| 2026-11-04 | v3, uncommitted | **comparison (SE-11): dense is the default** | `python scripts/compare_search.py`, CSV `eval/results/search_compare_2026-11-04.csv` (80 rows). 36 English: dense paper@5 32/36, page@5 **24/36**; hybrid 30/36, **23/36**. 4 multilingual: both 1/4, 0/4. Differ on page@5: hybrid finds q06, q11, q21; dense finds q04, q22, q30, q33 (hybrid loses the casual and typo ones). Top hit only (from the CSV): both 27/36 paper, 15/36 page. Difference is one question; by choice 3 dense stays default, hybrid stays in the code for row 8 |
| 2026-11-07 | v3, uncommitted | **SE-1 to SE-9 passed** | `pytest tests/test_search.py -v`: 2 unit + 7 integration; SE-10 and SE-11 run by hand earlier (2026-11-04) |
