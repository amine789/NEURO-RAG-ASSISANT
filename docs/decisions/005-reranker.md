# 005: Rerank the top 20 fused chunks with a small cross-encoder on ONNX

- **Status:** accepted, 2026-10-18
- **Evidence:** measured (one eval run per setting; run-to-run noise not yet measured)

## Context

The baseline (rows 1–4) scored correctness 0.68 on the English questions.
RT-7 showed that some right papers are among the 40 search candidates but
below the top 5 that reach the answer. Fusion (RRF) orders chunks only by their
positions in the two search lists; it never reads the question and the chunk
together. A cross-encoder does, at the cost of running a model per chunk on
every question. The system target is p95 ≤ 6 s per answer; generation alone
has p95 about 4.5 s. Everything here was measured on the development laptop, a
2020 Intel Core i5 with 4 cores and no GPU; the deployment server is expected
to be no faster.

## Options

| Option | For | Against |
|---|---|---|
| A. No reranker | fastest (retrieval p95 20–40 ms) | keeps the baseline's 0.68 |
| B. Rerank the top 20, PyTorch | correctness 0.75 in the eval | retrieval p95 701 ms alone; eval p95 6.4 s, over target |
| C. Rerank the top 20, ONNX | same model; retrieval p95 561 ms alone | over RT-17's original 500 ms |
| D. Rerank the top 10, ONNX | retrieval p95 about 300 ms; eval p95 4.7 s | correctness 0.69: most of B's gain lost |
| E. A bigger reranker (`BAAI/bge-reranker-v2-m3`) | stronger, multilingual | 568M parameters: several times slower on this CPU |

## Decision

Rerank the top 20 fused chunks with `cross-encoder/ms-marco-MiniLM-L6-v2`,
run on ONNX through FastEmbed (`Xenova/ms-marco-MiniLM-L-6-v2`), and keep the
best 5. RT-17's limit is raised from 500 ms to 750 ms to fit it.

## Consequences

- Each question costs about 0.45–0.55 s more on one CPU (RT-13 vs RT-17), with
  no extra API cost.
- Under concurrent load it gets worse: with 4 questions at once the PyTorch
  version took 1.5 s at p50, because the copies share the CPU. Before
  deployment (row 10), measure p95 under the expected load on the real server.
- No new dependency: FastEmbed already runs the BM25 encoder.
- The reranker is optional (`Retriever(..., reranker=Reranker())`), so the
  baseline stays runnable for comparison.

## Evidence so far

English questions, 3 repeats of 50 questions each; latency is per answer in the
eval (4 questions at once), and per retrieval alone in RT-13 / RT-17.

| | Baseline | B: 20, PyTorch | C: 20, ONNX | D: 10, ONNX |
|---|---|---|---|---|
| Correctness | 0.68 | 0.75 | not run | 0.69 |
| Faithful | 0.80 | 0.81 | not run | 0.84 |
| Retrieval hit | 0.88 | 0.89 | not run | 0.92 |
| Cites expected | 0.84 | 0.85 | not run | 0.84 |
| Eval retrieval p50 / p95 | 0.03 / 0.10 s | 1.48 / 2.56 s | not run | 0.32 / 0.71 s |
| Eval total p50 / p95 | 2.5 / 4.8 s | 3.9 / 6.4 s | not run | 2.8 / 4.7 s |
| Retrieval alone p50 / p95 | 17 / 38 ms | 576 / 701 ms | 448 / 561 ms | not measured |
| Known papers in top 5 (RT-15) | 18–19 / 20 | 18 / 20 | 18 / 20 | not measured |

- With B, 12 of the 40 judged questions improved and 4 got worse. Consistent
  across B and D: gains on `multi_paper` (0.58 → 0.75) and `casual_typos`
  (0.67 → 0.83); losses on q26 (1.0 → 0.33 / 0.17) and `loose_terms`
  (1.00 → 0.67 / 0.58).
- RT-15: PMC6560047 moves into the top 5 with the reranker; PMC10541893 moves
  out. PMC9613775 is never among the candidates, so no reranker can fix it
  (row 7, rewrite).
- Single questions swing between runs with nothing changed in their retrieval
  (q01: 0.5, 1.0, 0.5), so part of each difference above is noise.

## How it will be validated

- Run the eval with C (`--rerank`) to confirm ONNX keeps B's correctness and
  brings p95 under 6 s.
- Run the baseline a second time: the difference between two identical
  baselines is the noise floor. The reranker stays only if its gain over the
  baseline is larger than that.
- Before deployment, measure retrieval p95 under load on the server.
