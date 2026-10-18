# 002: Store keyword search as sparse vectors in Qdrant

- **Status:** accepted, 2026-10-17
- **Evidence:** design constraint

## Context

Retrieval is hybrid: meaning search (dense vectors) plus keyword search (BM25),
so exact terms like gene names and acronyms are still found. v1 kept the BM25
index in the API's memory, built at every startup from `pages.jsonl`. On a
server ([decision 001](001-deployment-target.md)) that means shipping a second
copy of the corpus next to Qdrant and keeping the two in sync.

## Options

| Option | For | Against |
|---|---|---|
| A. BM25 in API memory (v1) | exact BM25; no extra dependency | second copy of the corpus on the server; rebuilt at every startup; can drift from Qdrant |
| **B. Sparse vectors in Qdrant** | one store; written by the same build job; dense and keyword search fused in one query | BM25 length normalization uses the encoder's default average length, not the corpus's |

## Decision

Each chunk stores a sparse vector next to its dense vector. The sparse vector
holds the BM25 term-frequency part of each word in the chunk, encoded with
FastEmbed `Qdrant/bm25`. Qdrant computes word rarity (IDF) itself at search time
(the `IDF` modifier). One query searches both vectors and fuses the results with
reciprocal rank fusion.

## Consequences

- The API holds no index and needs no `pages.jsonl`; it starts faster.
- Adding chunks never requires recomputing the others, because IDF isn't stored.
- The keyword encoder is fixed per index: changing it means a new index.
- Adds the FastEmbed dependency to both the build job and the API.

## Evidence so far

- None measured yet; v1 used option A.
- Observed 2026-10-17: FastEmbed's tokenizer splits hyphenated terms (`IGF-1`
  becomes two terms, `igf` and `1`), while v1's tokenizer kept them whole. This
  may weaken exact matches on gene and receptor names; the eval should include
  such questions.

## How it will be validated

Run the eval on both options against the same index version and compare
retrieval quality and latency.
