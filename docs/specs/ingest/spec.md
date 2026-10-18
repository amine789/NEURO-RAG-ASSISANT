# Ingest and index: spec

What this module must do. Written when its row in [ROADMAP.md](../../ROADMAP.md)
starts.

## Goal

Turn the catalog of papers into a Qdrant collection where every chunk can be
searched and cited, and ship it as a snapshot.

## In and out

- **In:** the catalog (`data/candidates.csv`: pmcid, title, citation, license,
  PDF checksum, `keep`) and the PDFs in `data/raw/`.
- **Out:** a Qdrant collection of chunks, and a snapshot file of it.
- **Runs:** offline, on the laptop, as one command, against a local Qdrant
  container ([ARCHITECTURE section 3](../../ARCHITECTURE.md#3-data)).

## Settings

Starting values, revisited once the eval can measure them (roadmap row 4).

| Setting | Start | Why |
|---|---|---|
| chunk size | 200 tokens | below the embedding model's 256-token input limit |
| chunk overlap | 64 tokens | a sentence cut at a chunk edge stays whole in one chunk |
| dense encoder | `all-MiniLM-L6-v2` (384 numbers) | small and fast on a CPU |
| sparse encoder | FastEmbed `Qdrant/bm25` | [decision 002](../../decisions/002-keyword-search-in-qdrant.md) |

## Acceptance criteria

Numbered WHEN/THEN statements. Each one is checked in [validation.md](validation.md).

Input:

- **IN-1**: WHEN a PDF is not in the catalog with `keep=yes`, THEN it is skipped
  and reported, because it couldn't be cited.
- **IN-2**: WHEN a PDF's checksum doesn't match the catalog, THEN it is skipped
  and reported.
- **IN-3**: WHEN a PDF has no extractable text or can't be parsed, THEN it is
  reported and the build continues with the other papers.

Chunks:

- **IN-4**: Each chunk comes from one page and keeps that page's number.
- **IN-5**: Each chunk's `pmcid`, `title`, `citation` and `license` come from the
  catalog, never from the PDF's own metadata.
- **IN-6**: Text that repeats on every page (running headers, footers, page
  numbers) and reference lists are not indexed.
- **IN-7**: No chunk is longer than the embedding model's input limit, so no
  text is silently cut off when it is encoded.
- **IN-8**: WHEN the same PDFs are built with the same settings, THEN the chunks
  get the same IDs and the same text.

Collection:

- **IN-9**: Each chunk is stored as one point holding its text, chunk ID, dense
  vector, sparse vector, `pmcid`, `title`, `citation`, `license` and `page`.
- **IN-10**: Each build writes a new collection, `hippocampus-v<N>`. The alias
  `hippocampus` is moved to it only after every chunk is written and the point
  count equals the chunk count.
- **IN-11**: WHEN the build fails at any step, THEN the alias still points at the
  previous collection.
- **IN-12**: The collection records what built it: the catalog checksum, the
  settings above, and the encoder versions.
- **IN-13**: WHEN the build succeeds, THEN it writes a snapshot of the new
  collection and reports the number of papers, pages and chunks.

## Out of scope

- Downloading the PDFs (done once, by `scripts/collect_corpus.py`).
- OCR of scanned PDFs; tables, figures and equations.
- Adding papers to an existing collection (every build is full).
- Copying the snapshot to the server (roadmap row 10).
