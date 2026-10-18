# Ingest and index: validation

How each acceptance criterion in [spec.md](spec.md) is checked, and the results.

## Checks

Three kinds of check:

- **Unit test:** runs in seconds with no services: a tiny catalog and a few
  generated PDFs, no Qdrant.
- **Integration test:** runs against a real local Qdrant container.
- **Inspection:** a person reads the output; some things (is this text clean?)
  only a reader can judge.

| Criterion | Checked by | Pass when |
|---|---|---|
| IN-1 | unit test: a PDF missing from the catalog, one with `keep=no` | both skipped and reported; the others built |
| IN-2 | unit test: a PDF with a wrong checksum | skipped and reported |
| IN-3 | unit test: an empty PDF and a corrupt file | both reported; the build finishes |
| IN-4 | unit test: a 3-page PDF | every chunk has one page number, matching where its text is |
| IN-5 | unit test: PDF metadata title differs from the catalog | the chunk has the catalog title |
| IN-6 | unit test: a PDF with a repeated header and a reference list; inspection of 20 random chunks from the real corpus | neither appears in any chunk |
| IN-7 | unit test over every real chunk | every chunk's length in the embedding model's tokens ≤ 256 |
| IN-8 | unit test: build twice | identical IDs and text |
| IN-9 | integration test: read back one point | every listed field is present and non-empty |
| IN-10 | integration test: build twice | two collections; the alias points at the second |
| IN-11 | integration test: make the build fail halfway | the alias still points at the first collection |
| IN-12 | integration test: read the collection's metadata | all listed values present |
| IN-13 | integration test: full build | snapshot file exists; counts printed |

## Results

| Date | Version | Result | Notes |
|---|---|---|---|
| 2026-10-17 | `hippocampus-v1` | all 13 criteria pass | 13 unit + 6 integration + 1 real-corpus test pass. Build: 52 papers, 719 pages, 5,974 chunks, 0 skipped; snapshot 36 MB. IN-6 inspection: 20 random chunks, all clean |
