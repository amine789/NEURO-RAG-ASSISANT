# Ingest and index: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test** (`tests/test_ingest.py`): small inputs written in the test
  (lines, pages, a fake token counter, a tiny PDF made with PyMuPDF in a
  temporary folder) and, for IN-8, IN-10 and IN-11, the real tokenizer and
  the real PMC6226095.pdf. No Qdrant.
- **Integration test** (`tests/test_ingest_index.py`, marked `integration`):
  the running Qdrant from `docker compose up -d`, a test collection, and a
  fake embedder returning 384 numbers.
- **Full build:** `python -m neuro_rag.ingest.build` on the 52 papers.

| Criterion | Kind | Test |
|---|---|---|
| IN-1 | unit | `test_IN1_paper_not_kept_is_not_selected` |
| IN-2 | unit + integration | `test_IN2_unreadable_pdf_raises_parse_error` (unit, parse_pdf half), `test_IN2_build_continues_after_parse_error` (integration, build half) |
| IN-3 | unit | `test_IN3_lines_on_most_pages_are_dropped` |
| IN-4 | unit | `test_IN4_page_numbers_dropped_numbers_in_text_kept` |
| IN-5 | unit | `test_IN5_references_dropped_methods_after_them_kept` |
| IN-6 | unit | `test_IN6_lines_joined_keeping_hyphens` |
| IN-7 | unit | `test_IN7_pages_keep_their_numbers` |
| IN-8 | unit | `test_IN8_tokenizer_counts_real_tokens` |
| IN-9 | unit | `test_IN9_chunks_packed_from_sentences_with_overlap` |
| IN-10 | unit | `test_IN10_long_sentence_cut_between_words` |
| IN-11 | unit | `test_IN11_same_pdf_same_chunks_and_ids` |
| IN-12 | integration | `test_IN12_point_holds_text_vector_paper_and_page` |
| IN-13 | integration | `test_IN13_build_replaces_the_collection` |
| IN-14 | full build | run the command; compare the printed counts with the spec |

Commands:
```
pytest tests/test_ingest.py -v
docker compose up -d && pytest tests/test_ingest_index.py -m integration -v
python -m neuro_rag.ingest.build
```

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-30 | v3, uncommitted | IN-1 passed | `pytest tests/test_ingest.py -v`; IN-2 to IN-14 not built yet |
| 2026-10-30 | v3, uncommitted | IN-1, IN-2 (parse_pdf half) passed | 2 passed; IN-2 build half waits for `build.py`; IN-3 to IN-14 not built yet |
| 2026-10-30 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 passed | 3 passed; IN-4 to IN-14 not built yet |
| 2026-10-30 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3, IN-4 passed | 4 passed; IN-5 to IN-14 not built yet |
| 2026-10-31 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-5 passed | 5 passed; IN-6 to IN-14 not built yet |
| 2026-10-31 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-6 passed | 6 passed; IN-7 to IN-14 not built yet |
| 2026-10-31 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-7 passed | 7 passed; parse.py done; IN-8 to IN-14 not built yet |
| 2026-10-31 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-8 passed | 8 passed; IN-9 to IN-14 not built yet |
| 2026-11-01 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-9 passed | 9 passed; IN-10 to IN-14 not built yet |
| 2026-11-01 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-10 passed | 10 passed; IN-11 to IN-14 not built yet |
| 2026-11-01 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-11 passed | 11 passed; IN-12 to IN-14 not built yet |
| 2026-11-01 | v3, uncommitted | IN-1, IN-2 (parse_pdf half), IN-3 to IN-12 passed | 11 unit + 1 integration passed; IN-13, IN-14 and the IN-2 build half wait for `build.py` |
| 2026-11-02 | v3, uncommitted | IN-14 full build passed | `python -m neuro_rag.ingest.build`: report matches (52 papers, 642 pages, 4431 chunks); Qdrant `papers` holds 4,431 points, 384 cosine. IN-13 and the IN-2 build half still need their tests |
| 2026-11-02 | v3, uncommitted | **IN-1 to IN-14 all passed** | 11 unit + 3 integration tests, plus the full build (IN-14) |
