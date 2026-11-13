# Search: spec

Roadmap row 2: a question returns its top 5 chunks, by dense or hybrid search,
and the two are compared on the eval questions before deployment.

## Goal

Given a question in plain words, return the 5 chunks from the `papers`
collection that best match it, each with everything an answer needs to quote
and cite it: text, paper, page, title, citation, license, and the score. Two
ways to match are built side by side, and a comparison script measures which
one finds the expected sources more often.

## In and out

- **In:** a question (a string), a mode (`"dense"` or `"hybrid"`), and the
  `papers` collection built by row 1 (4,313 points, each with a `dense` and a
  `bm25` vector).
- **Out:** a list of `Hit`, best first. By default 5.
- **Runs:**
  ```
  docker compose up -d                      # Qdrant
  python -m neuro_rag.retrieval.search "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
  python -m neuro_rag.retrieval.search --hybrid "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
  python scripts/compare_search.py          # both modes on the eval questions
  ```

```
                ┌─► dense:  MiniLM vector (384) ─► 5 nearest by cosine on "dense" ──────────────────────────────┐
question ─► strip                                                                                               ├─► [Hit, …] best first
                └─► hybrid: MiniLM vector ─► 20 nearest on "dense" ─┐                                           │
                            BM25 words    ─► 20 best on "bm25"  ────┴─► merged by rank (RRF) ─► top 5 ──────────┘
```

## Settings

| Setting | Value | Why |
|---|---|---|
| dense model | `sentence-transformers/all-MiniLM-L6-v2` through FastEmbed, `TextEmbedding.embed` | a question must be embedded by the same model as the chunks, or the distances mean nothing |
| keyword model | `Qdrant/bm25` through FastEmbed, `SparseTextEmbedding.query_embed` | the same words and stemming as the chunks; `query_embed` gives each question word weight 1 (see below) |
| how many | `k = 5` by default, a parameter | the roadmap's "top 5"; row 8 may ask for more (a reranker reads 20) |
| mode | `"dense"` by default, or `"hybrid"` | the default is decided by the comparison (choice 3) |
| hybrid candidates | 20 from each vector | enough for a chunk ranked low by one method but high by the other to be found; to confirm |
| merging | Qdrant's reciprocal rank fusion (`Fusion.RRF`) | uses ranks only, so a cosine (0 to 1) and a BM25 score (no fixed range) never have to be put on one scale |
| score threshold | none | deciding a question isn't in the papers is row 10's job |

## How it is built

### Files

| File | Contents |
|---|---|
| `src/neuro_rag/retrieval/__init__.py` (empty), `src/neuro_rag/retrieval/search.py` | `Hit`, `search`, `main` |
| `scripts/compare_search.py` | runs both modes on the eval questions and prints the comparison |
| `tests/test_search.py` | SE-4 and SE-9 are unit tests (no Qdrant); the others run against Qdrant and are marked `integration` |

No new dependency. `COLLECTION`, `EMBED_MODEL`, `SPARSE_MODEL` and
`QDRANT_URL` come from `config.py`.

### `retrieval/search.py`

```python
@dataclass(frozen=True)
class Hit:
    chunk_id: str
    pmcid: str
    page: int
    title: str
    citation: str
    license: str
    text: str
    score: float      # dense: cosine similarity (1.0 = same direction); hybrid: RRF score (rank-based)

def search(question: str, client: QdrantClient, embed, sparse_embed, k: int = 5,
           mode: str = "dense", name: str = COLLECTION) -> list[Hit]
def main()            # python -m neuro_rag.retrieval.search [--hybrid] "<question>"
```

`embed` is `TextEmbedding(EMBED_MODEL).embed` and `sparse_embed` is
`SparseTextEmbedding(SPARSE_MODEL).query_embed`, passed in (as in row 1's
`write_chunks`) so a test can count their calls or use fakes.

**`search` steps:**
1. `mode` not `"dense"` or `"hybrid"` → `ValueError(f"unknown mode: {mode}")`.
2. `question.strip()`. Empty after stripping → `ValueError("empty question")`.
   Both checks happen before `embed`, `sparse_embed` or Qdrant is called.
3. `dense = list(embed([question]))[0].tolist()`: 384 numbers.
4. **Dense:** `client.query_points(name, query=dense, using="dense", limit=k, with_payload=True).points`.
5. **Hybrid:** `s = list(sparse_embed([question]))[0]`, then
   ```python
   client.query_points(name,
       prefetch=[Prefetch(query=dense, using="dense", limit=20),
                 Prefetch(query=SparseVector(indices=s.indices.tolist(), values=s.values.tolist()), using="bm25", limit=20)],
       query=FusionQuery(fusion=Fusion.RRF), limit=k, with_payload=True).points
   ```
6. One `Hit` per point, in the order Qdrant returns them (best first): the
   seven payload fields, plus `score=point.score`.

**Why `embed` for chunks but `query_embed` for questions, for BM25.** BM25
scores a chunk by the question's words it contains, each counted by how often
it appears in the chunk (stored at build time) and how rare it is (IDF,
applied by Qdrant). The question's own word counts don't matter, so
`query_embed` gives each of its words weight 1: "Ythdf1 Mettl3 knockdown" gives
3 entries, all 1. `embed` on the same text gives 3 entries of 1.6787, which
would wrongly count the question as a document. For the dense model,
`embed` and `query_embed` give the same vector (checked on 3 questions,
largest difference 0.0), so `embed` is used for both.

**How RRF merges.** Each chunk gets, from each list it is in, a score that
falls with its rank there (1st counts most); the two are added. A chunk 3rd in
both lists beats one 1st in one list and absent from the other. The hybrid
`score` is this sum: it only orders hits and can't be compared with a cosine.

**`main` steps:**
1. Arguments: an optional `--hybrid`, then the question. No question →
   print `usage: python -m neuro_rag.retrieval.search [--hybrid] "<question>"` and exit
   with code 2.
2. `search(question, QdrantClient(url=QDRANT_URL), TextEmbedding(EMBED_MODEL).embed, SparseTextEmbedding(SPARSE_MODEL).query_embed, mode=...)`.
3. Print one line per hit: `f"{hit.score:.4f}  {hit.chunk_id}  {hit.text[:80]}"`.

**Worked example: question q01, dense** (run 2026-11-03 on row 1's
collection; the dense vectors don't change when `bm25` is added, so the
rebuilt collection gives the same lines):

```
$ python -m neuro_rag.retrieval.search "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
0.7612  PMC6226095-p6-c1  4i; Supplementary Table 1, 6), suggesting that more binding of Ythdf1 to its m 6
0.7292  PMC11319347-p1-c0  Epigenetic factors are well-established players in memory formation. Specificall
0.7284  PMC13144532-p3-c4  These studies suggest that histone H2A.Z modification might regulate both recent
0.7090  PMC11319347-p9-c5  Collectively, these findings indicate distinct regulatory functions. Specificall
0.7054  PMC11319347-p1-c3  Indeed, epigenetic mechanisms such as DNA methylation have emerged as important
```

The first hit is from the expected paper (PMC6226095) but page 6, not the
expected page 2; the next four are about other epigenetic marks. The hybrid
lines for the same question are recorded in validation.md after the rebuild.

The first dense hit as a `Hit`:

```python
Hit(chunk_id="PMC6226095-p6-c1", pmcid="PMC6226095", page=6,
    title="m6A facilitates hippocampus-dependent learning and memory through Ythdf1",
    citation="Nature. Author manuscript; Available in PMC 2019 Apr 30.",
    license="TDM", text="4i; Supplementary Table 1, 6), suggesting that …", score=0.7612…)
```

**An off-topic question** ("What's a good recipe for sourdough bread?") still
returns 5 dense hits, all far: the best is 0.1891 (a table row from
PMC4146209), against 0.76 for q01. Search reports the distance; row 10 decides
what a low score means.

### `scripts/compare_search.py`: dense against hybrid

**Which questions.** From `eval/questions.jsonl`, the 40 with
`expected_sources` (pmcid and page). The 4 non-English ones (`type` starting
`multilingual_`) are reported on their own line and left out of the totals
(roadmap choice 2), so the totals are over **36 questions**. The 14 without
expected sources (off-topic, borderline, out of corpus) have nothing to
match and are skipped.

**Two numbers per mode**, from the top 5 hits:
- **paper@5:** the question counts if any hit's `pmcid` is one of its
  expected pmcids.
- **page@5:** the question counts if any hit's (`pmcid`, `page`) is one of
  its expected (pmcid, page) pairs.

**Steps:**
1. Load the questions; keep the 40 with expected sources.
2. For each question and each mode, `search(question, …, k=5, mode=mode)`.
3. Print, for each mode, paper@5 and page@5 over the 36 English questions,
   then the same for the 4 multilingual ones.
4. Print every question where the two modes differ on page@5: its id,
   and which mode found the page.
5. Write one row per question and mode to
   `eval/results/search_compare_<YYYY-MM-DD>.csv` with columns
   `id, type, mode, paper_hit, page_hit, chunk_ids` (the 5 IDs joined by
   spaces), so any number printed can be checked against the hits behind it.

**Output format** (the counts below are placeholders, not results):
```
36 English questions
mode     paper@5   page@5
dense    NN/36     NN/36
hybrid   NN/36     NN/36
4 multilingual questions
dense    N/4       N/4
hybrid   N/4       N/4
differ on page@5: q07 hybrid, q19 dense, …
wrote eval/results/search_compare_2026-11-03.csv
```

## Choices, accepted 2026-11-07

1. **Dense and hybrid built side by side in row 2, compared before
   deployment** (decided 2026-11-03). v2 found hybrid helped; here it is
   measured again on this corpus and these chunks.
2. **The comparison is retrieval only:** does the top 5 contain the
   expected paper and page. It needs no LLM and runs in about a minute. It
   doesn't measure answer quality; that is row 4.
3. **The default mode is the one with more page@5 hits on the 36 English
   questions; on a tie, dense** (one vector, simpler to explain and run).
   The result and the chosen default are recorded in validation.md.
   **Result 2026-11-04: dense 24/36, hybrid 23/36, so dense is the default.**
4. **20 candidates from each vector for hybrid, merged by Qdrant's RRF with
   its default constant.** Not tuned; tuning is row 8.
5. **No score threshold.** Search always returns `k` hits (fewer only if the
   collection holds fewer points).
6. **The question is used as typed**, after stripping spaces: no spelling
   fixes or rewriting (row 9). (BM25 lower-cases and stems on its own.)
7. **`retrieval/search.py`, next to `ingest/`,** plus one script. Row 8 (a reranker) goes in the same folder.
8. **Errors from Qdrant are not caught here.** Qdrant down, or no `papers`
   collection, raises the client's own exception. The API (row 5) decides
   what the caller sees.

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is checked is in [validation.md](validation.md).

**SE-1: a dense search returns the 5 closest chunks, best first.**
- **Given** the `papers` collection from row 1's build (4,313 points).
- **When** `search` runs in `"dense"` mode on "How does m6A RNA methylation
  support hippocampus-dependent learning and memory?" with the real
  embedders.
- **Then** it returns exactly 5 hits, their scores never increase from one to
  the next, and the first is `PMC6226095-p6-c1` with a score between 0.76 and
  0.77.
- **Why:** the answer step reads the hits in order and cites them; the first
  must be the closest.

**SE-2: each hit carries everything needed to quote and cite it.**
- **Given** the same collection and question as SE-1.
- **When** `search` runs in `"dense"` mode.
- **Then** the first hit has `pmcid` "PMC6226095", `page` 6, `title` "m6A
  facilitates hippocampus-dependent learning and memory through Ythdf1",
  `citation` "Nature. Author manuscript; Available in PMC 2019 Apr 30.",
  `license` "TDM", and a `text` starting "4i; Supplementary Table 1, 6),
  suggesting that more binding of Ythdf1".
- **Why:** the answer cites "paper, page" and quotes the text; going back to
  Qdrant or the catalog for them would be a second lookup that can disagree.

**SE-3: a chunk's own text finds that chunk first.**
- **Given** the text of chunk `PMC6226095-p2-c0`, read from the collection.
- **When** `search` runs in `"dense"` mode with that text as the question.
- **Then** the first hit is `PMC6226095-p2-c0` with a score of at least 0.99.
- **Why:** it shows questions and chunks are embedded by the same model the
  same way; a different model or a changed text would score far below 1.

**SE-4: an empty question is refused before any work is done.**
- **Given** the question "   " (three spaces), an `embed` and a
  `sparse_embed` that count their calls, and a client that counts its calls.
- **When** `search` runs.
- **Then** it raises `ValueError("empty question")`, and none of the three
  was called.
- **Why:** an empty string still gets a vector and 5 "closest" chunks, which
  an answer would then cite for nothing.

**SE-5: `k` sets how many hits come back.**
- **Given** the same collection and question as SE-1.
- **When** `search` runs in `"dense"` mode with `k=20`.
- **Then** it returns 20 hits, and the first 5 are the 5 from SE-1, in the
  same order.
- **Why:** row 8 may rerank a longer list; asking for more must not change
  the order of the first ones.

**SE-6: an off-topic question still returns 5 hits, with low scores.**
- **Given** the same collection.
- **When** `search` runs in `"dense"` mode on "What's a good recipe for
  sourdough bread?".
- **Then** it returns 5 hits, and the first has a score below 0.30.
- **Why:** search measures distance and never decides; that the best score
  here is 0.19 against 0.76 for SE-1 is the evidence row 10 starts from.

**SE-7: a hybrid search returns 5 hits, each found by dense or BM25.**
- **Given** the same collection, and the question "Ythdf1 Mettl3 knockdown".
- **When** `search` runs in `"hybrid"` mode, and separately the dense top 20
  and the BM25 top 20 for the same question are read from Qdrant.
- **Then** it returns 5 distinct hits, their scores never increase, and
  every hit's `chunk_id` is in the dense top 20 or the BM25 top 20.
- **Why:** RRF only reorders the two candidate lists; a hit from neither
  would mean the merge is not doing what the spec says.

**SE-8: hybrid finds an exact rare term that appears in a chunk.**
- **Given** the same collection, and the question "Ythdf1 Mettl3 knockdown".
- **When** `search` runs in `"hybrid"` mode.
- **Then** at least one of the 5 hits has a `text` containing "Mettl3".
- **Why:** finding exact gene and region names is the reason to add BM25;
  if hybrid can't find a three-keyword query's rare term, it adds nothing.

**SE-9: an unknown mode is refused before any work is done.**
- **Given** the mode `"sparse"`, and the same counting fakes as SE-4.
- **When** `search` runs on "Does sleep help memory?".
- **Then** it raises `ValueError("unknown mode: sparse")`, and none of the
  three was called.
- **Why:** a typo in the mode would otherwise fall through to one of the two
  and silently measure the wrong thing.

**SE-10: the command prints one line per hit, in either mode.**
- **Given** the same collection.
- **When** `python -m neuro_rag.retrieval.search "How does m6A RNA methylation support
  hippocampus-dependent learning and memory?"` runs, then the same with
  `--hybrid`.
- **Then** each prints 5 lines and exits with code 0; the dense one's first
  line starts `0.7612  PMC6226095-p6-c1  4i; Supplementary Table 1`. With no
  question it prints the usage line and exits with code 2.
- **Why:** looking at real results by hand is how the comparison's numbers
  get checked.

**SE-11: the comparison reports both modes on the same 36 questions.**
- **Given** the collection and `eval/questions.jsonl`.
- **When** `python scripts/compare_search.py` runs.
- **Then** it prints paper@5 and page@5 for dense and hybrid, each out of 36
  English questions and 4 multilingual ones, lists the questions where the
  modes differ on page@5, and writes the CSV with 80 rows (40 questions × 2
  modes).
- **Why:** the default mode (choice 3) is decided from these numbers, and
  the CSV lets each number be traced back to the hits behind it.

## Out of scope

- A reranker, tuning RRF or the candidate count (row 8).
- A score threshold, "not in the papers" (row 10).
- Rewriting or correcting the question (row 9).
- Filtering by paper, page or license.
- Answer quality; the comparison is retrieval only (row 4).
- Catching Qdrant errors (row 5 decides what the caller sees).
