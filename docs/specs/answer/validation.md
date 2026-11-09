# Cited answer: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.
The examples are in the spec; this file says where each one runs.

## Checks

- **Unit test** (`tests/test_answer.py`): a fake LLM (an object with `invoke`) that returns
  the blocks written in the test, counts its calls and records what it was
  sent. No API call, no Qdrant, no cost.
- **LLM test** (`tests/test_answer_llm.py`, marked `llm`): the real Claude
  Haiku 4.5 API through `ChatAnthropic` with the key from `.env`, on hits written in the test. Four
  calls, about $0.005 in total.
- **Command:** run by hand, against Qdrant and the real API.

| Criterion | Kind | Test |
|---|---|---|
| CA-1 | unit | `test_CA1_markers_numbered_and_match_sources` |
| CA-2 | unit | `test_CA2_same_page_shares_one_source` |
| CA-3 | unit | `test_CA3_no_hits_no_call` |
| CA-4 | unit | `test_CA4_refusal_gives_fixed_sentence` |
| CA-5 | unit | `test_CA5_request_sends_documents_in_order` |
| CA-6 | unit | `test_CA6_heading_lines_removed` |
| CA-7 | llm | `test_CA7_citations_point_at_sent_chunks` |
| CA-8 | llm | `test_CA8_not_covered_cites_nothing` |
| CA-9 | llm | `test_CA9_false_premise_corrected` |
| CA-10 | llm | `test_CA10_instructions_in_chunk_ignored` |
| CA-11 | command | run it on q01; check markers, source lines, token line; run with no question |

Commands:
```
pytest tests/test_answer.py -v
pytest tests/test_answer_llm.py -m llm -v
python -m neuro_rag.generation.answer "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
python -m neuro_rag.generation.answer; echo $?
```

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-11-07 | v3, uncommitted | spec written | not built yet |
| 2026-11-08 | v3, uncommitted | CA-11 first run (q01), by hand | answer with 3 sentences, each ending "[1]" before the full stop; one source, PMC6226095 page 6 with its PMC link; 2,293 in / 179 out tokens (≈ $0.003). Citations come back through `ChatAnthropic` as specified. Markers moved before end punctuation after the first run showed "Ythdf1. [1]" |
| 2026-11-08 | v3, uncommitted | **CA-1 to CA-10 passed** | `pytest tests/test_answer.py -v` (6 unit, fake LLM) and `pytest tests/test_answer_llm.py -m llm -v` (4 real Haiku 4.5 calls); CA-11 run by hand earlier the same day |
