# Ingest and index: spec

Roadmap row 1: the 52 papers become searchable chunks, each knowing its paper
and page.

## Goal

Turn the kept papers in the catalog into a Qdrant collection of chunks, where
each chunk holds its text, its vector, and the paper and page it came from, so
an answer can cite "paper, page".

## In and out

- **In:**
  - the catalog `data/candidates.csv`: 66 rows, 52 with `keep=yes`. Columns:
    `keep, pmcid, title, citation, license, pdf_url, pdf_md5`; ingest reads
    `keep, pmcid, title, citation, license`;
  - the PDFs in `data/raw/`, named `<pmcid>.pdf` (52 files, 826 pages).
- **Out:** the Qdrant collection `papers`, one point per chunk, and a report
  printed at the end of the build.
- **Runs:** offline, on the laptop, as one command against a local Qdrant
  container:
  ```
  docker compose up -d
  python -m neuro_rag.ingest.build
  ```

```
candidates.csv ─┐
                ├─► select papers ─► for each PDF: pages ─► clean lines ─► chunks ─► embed ─► Qdrant "papers"
data/raw/*.pdf ─┘    (keep=yes)        (PyMuPDF)     (drop headers,     (≤ 200     (384
                                                      page numbers,      tokens)    numbers)
                                                      references)
```

## Settings

| Setting | Value | Why |
|---|---|---|
| PDF reader | PyMuPDF, `page.get_text()` | plain text per page, in the PDF's own order; fast, one dependency |
| embedding model | `sentence-transformers/all-MiniLM-L6-v2` through FastEmbed (ONNX), 384 numbers | small, fast on a CPU, no PyTorch in the deployed image |
| token counter | the same model's tokenizer (`tokenizers` library), padding and truncation turned off | the limit that matters is the model's: 256 tokens, beyond which it silently ignores the rest |
| chunk size | at most 200 tokens | below the 256 limit, with room for the 2 tokens the model adds |
| overlap | the previous chunk's last sentence, if it has 50 tokens or fewer | a sentence cut at a chunk edge is still whole in one chunk |
| distance | cosine | what the model was trained for |
| collection | `papers`, deleted and recreated by every build | one command gives a clean state; the deployed service gets its data in row 7, not from this collection |
| batch size | 64 chunks per embedding call and per Qdrant write | keeps memory flat; any size gives the same result |

## How it is built

### Files

| File | Contents |
|---|---|
| `pyproject.toml` | package `neuro-rag`, Python ≥ 3.11; dependencies `pymupdf`, `fastembed`, `qdrant-client`, `python-dotenv`; dev dependency `pytest` |
| `docker-compose.yml` | one service `qdrant`, image `qdrant/qdrant:v1.19.1`, port 6333, a named volume for storage |
| `src/neuro_rag/config.py` | paths (`DATA_DIR`, `CATALOG_PATH`, `RAW_DIR`), `QDRANT_URL` from the environment (default `http://localhost:6333`), `COLLECTION = "papers"`, `EMBED_MODEL`, `EMBED_SIZE = 384`, `CHUNK_TOKENS = 200`, `CARRY_TOKENS = 50`, `BATCH = 64` |
| `src/neuro_rag/ingest/catalog.py` | `Paper`, `load_catalog`, `select_papers` |
| `src/neuro_rag/ingest/parse.py` | `Page`, `ParseError`, `body_lines`, `join_lines`, `parse_pdf` |
| `src/neuro_rag/ingest/chunk.py` | `Chunk`, `TokenCounter`, `split_sentences`, `chunk_page` |
| `src/neuro_rag/ingest/index.py` | `point_id`, `recreate_collection`, `write_chunks` |
| `src/neuro_rag/ingest/build.py` | `main()`: runs everything and prints the report |
| `tests/test_ingest.py` | unit tests, no Qdrant needed |
| `tests/test_ingest_index.py` | tests against the running Qdrant, marked `integration` |

### `catalog.py`: which PDFs are built

```python
@dataclass(frozen=True)
class Paper:
    pmcid: str
    title: str
    citation: str
    license: str

def load_catalog(path: Path) -> dict[str, Paper]          # pmcid -> Paper, rows with keep == "yes" only
def select_papers(raw_dir: Path, catalog: dict[str, Paper]) -> list[tuple[Path, Paper]]
```

`select_papers` goes through the `.pdf` files in `raw_dir`, sorted by name:
1. File name without `.pdf` in the catalog → selected, paired with its `Paper`.
2. Otherwise → left out, with no message.

A kept paper with no PDF is not reported here; the build report's paper count
(52) shows it.

`keep` is compared after trimming spaces and lower-casing: "yes", "Yes" and
" yes" all count.

### `parse.py`: from a PDF to clean pages

```python
@dataclass(frozen=True)
class Page:
    pmcid: str
    page: int      # 1-based: page 1 is the PDF's first page
    text: str

class ParseError(Exception): ...

def body_lines(pages: list[list[str]]) -> list[list[str]]   # drops non-body lines; same shape in, same shape out
def join_lines(lines: list[str]) -> str                     # one page's kept lines -> one clean string
def parse_pdf(path: Path, pmcid: str) -> list[Page]
```

**`parse_pdf` steps:**
1. Open with `pymupdf.open(path)`. Any exception → `ParseError(f"can't open {path.name}: {e}")`.
2. For each page: `page.get_text()`, split on line breaks, strip each line,
   drop empty lines. Result: one list of lines per page.
3. `body_lines(...)` on all pages at once (the rules need the whole paper).
4. For each page, `join_lines(lines)`. A page whose text is empty is dropped.
   Page numbers are kept as they were in step 2: dropping page 1 doesn't
   renumber page 2.
5. No page left at all → `ParseError(f"no text in {path.name}")`.

**`body_lines` rules,** applied in this order to each line, page by page,
first page to last:
1. **Repeated line:** a line that appears on more than half of the paper's
   pages (counted once per page) is dropped everywhere. Only for papers with
   3 pages or more.
   Example, PMC6226095 (37 pages): "Nature. Author manuscript; available in PMC
   2019 April 30." is on 37 pages and "Shi et al." on 36; both are dropped.
2. **Page number:** a line matching `^(page\s+)?\d{1,4}(\s+of\s+\d{1,4})?$`,
   ignoring case, is dropped: "7", "Page 7", "Page 7 of 37".
3. **Reference list start:** a line matching
   `^(\d+\.?\s*)?(references|bibliography|literature cited)$`, ignoring case,
   is dropped and switches to "in references": "References", "REFERENCES",
   "5. References".
4. **Reference list end:** while in references, a line matching
   `^(\d+\.?\s*)?(methods|online methods)$`, ignoring case, switches back and is kept.
   Every other line in references is dropped. "In references" carries over
   from one page to the next.

   Why rule 4: four Nature-style papers (PMC11848949, PMC12229897, PMC13156042,
   PMC13533836) print their Methods after the reference list. In PMC12229897
   the references start on page 8 of 28 and "Methods" is on page 10; without
   rule 4 the Methods would be lost. A second reference list after the Methods
   is dropped again by rule 3.

On the 52 papers these rules drop 6,028 repeated lines, 4,614 page-number lines,
55 reference headings and 15,135 reference lines.

**`join_lines` steps:**
1. Join the lines in order. Between two lines put one space, except when the
   first ends with "-" right after a letter or digit: then join with nothing, so
   the hyphen stays and no space is added.
   Example: "…through m6A-" + "specific binding proteins" →
   "…through m6A-specific binding proteins"; "long-" + "term potentiation" →
   "long-term potentiation". (A word broken only by hyphenation, "hippo-" +
   "campus", becomes "hippo-campus"; that is accepted, see choice 5.)
2. Replace the ligature characters: "ﬁ" → "fi", "ﬂ" → "fl", "ﬀ" → "ff",
   "ﬃ" → "ffi", "ﬄ" → "ffl".
3. Replace every run of whitespace with one space; strip both ends.

### `chunk.py`: from a page to chunks

```python
@dataclass(frozen=True)
class Chunk:
    chunk_id: str  # "<pmcid>-p<page>-c<n>", n counts from 0 on each page
    pmcid: str
    page: int
    text: str

class TokenCounter:
    def __init__(self, model: str = EMBED_MODEL)   # Tokenizer.from_pretrained(model); then no_padding() and no_truncation()
    def __call__(self, text: str) -> int           # len(encode(text, add_special_tokens=False).ids)

def split_sentences(text: str) -> list[str]        # re.split(r"(?<=[.!?])\s+", text), empty pieces dropped
def make_units(text: str, count: TokenCounter, size: int) -> list[tuple[str, int]]   # step 1: (text, tokens) per unit
def pack_units(units: list[tuple[str, int]], size: int, carry: int) -> list[str]     # steps 2-4: one text per chunk
def chunk_page(page: Page, count: TokenCounter, size: int = 200, carry: int = 50) -> list[Chunk]   # make_units, pack_units, then step 5 (IDs)
```

Why `no_padding()` and `no_truncation()`: this model's tokenizer file comes
with padding and truncation to 128 tokens switched on. Left on, every text
counts as exactly 128 tokens, short or long, and every check on size passes
without measuring anything.

**`chunk_page` steps:**
1. **Units.** `split_sentences(page.text)`. A sentence over `size` tokens is
   cut into pieces between words: add words one at a time, and when the next
   word would take the piece over `size`, close it and start a new one. Each
   piece is a unit; every other sentence is a unit as it is.
2. **Packing.** Go through the units in order, adding each to the current
   chunk while the chunk's tokens plus the unit's stay at or under `size`.
   A chunk's tokens are the sum of its units' tokens: this tokenizer splits
   on spaces first, so joining units with a space adds no token.
3. **Closing a chunk.** When the next unit doesn't fit, the current chunk is
   closed: its text is its units joined with one space. The new chunk starts
   with the closed chunk's last unit if that unit has `carry` tokens or fewer
   (the overlap), otherwise empty. If the carried unit plus the next unit
   still exceed `size`, the new chunk starts empty instead.
4. At the end, the last chunk is closed if it has any unit.
5. IDs: `f"{page.pmcid}-p{page.page}-c{n}"`, `n` = 0, 1, 2… in order.

**Worked example: PMC6226095, page 2.** After cleaning, its first sentences
have these token counts:

| Unit | Starts with | Tokens |
|---|---|---|
| s0 | "10Department of Psychiatry, Perelman School of Medicine…" (affiliations) | 112 |
| s1 | "Summary N6-methyladenosine (m6A), the most prevalent…" | 50 |
| s2 | "m6A is abundant in the nervous system…" | 19 |
| s3 | "While m6A marks groups of mRNAs…" | 35 |
| s4 | "Here we show that, through its binding protein Ythdf1…" | 46 |
| s5 | "Mice with genetic deletion of Ythdf1 (Ythdf1-KO)…" | 43 |
| s6 | "Ythdf1 re-expression in the hippocampus…" | 75 |
| s7 | "Transcriptome-wide mapping of Ythdf1 binding sites…" | 31 |
| s8 | "Nascent protein labeling and tether reporter assays…" | 37 |
| s9 | "Collectively, our results uncover…" | 32 |

- `PMC6226095-p2-c0`: s0 + s1 + s2 = 112 + 50 + 19 = 181. Adding s3 would make
  216 > 200, so c0 closes at **181 tokens**. Its last unit, s2 (19 ≤ 50), is carried.
- `PMC6226095-p2-c1`: s2 + s3 + s4 + s5 = 19 + 35 + 46 + 43 = 143. Adding s6
  would make 218, so c1 closes at **143**. s5 (43 ≤ 50) is carried.
- `PMC6226095-p2-c2`: s5 + s6 + s7 + s8 = 43 + 75 + 31 + 37 = 186. Adding s9
  would make 218, so c2 closes at **186**; s8 (37) is carried, and so on.

c1 starts with "m6A is abundant in the nervous system…", the sentence c0 ends
with, so a question matching that sentence finds it whole in either chunk.

**On the whole corpus:** 642 pages with text, **4,431 chunks**, largest 200
tokens, median 179; 10% of chunks have 119 tokens or fewer (page ends).

### `index.py`: into Qdrant

```python
def point_id(chunk_id: str) -> str   # str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
def recreate_collection(client: QdrantClient, name: str = COLLECTION) -> None
def write_chunks(client: QdrantClient, chunks: list[Chunk], papers: dict[str, Paper], embed, name: str = COLLECTION) -> int
```

- `point_id`: Qdrant only accepts integers or UUIDs as point IDs; a UUID
  derived from the chunk ID is the same on every build.
  `point_id("PMC6226095-p2-c0")` always returns the same UUID.
- `recreate_collection`: deletes `name` if it exists, then creates it with one
  unnamed dense vector of size 384, distance cosine.
- `write_chunks`, in batches of 64 chunks:
  1. `vectors = list(embed([c.text for c in batch]))`, where `embed` is
     `TextEmbedding(EMBED_MODEL).embed`, passed in so tests can use a fake.
  2. One `PointStruct` per chunk: `id=point_id(chunk_id)`, `vector`, and the
     payload below. `client.upsert(name, points, wait=True)`.
  3. Returns the number of points written.

**Payload of one point,** with `title`, `citation` and `license` from the
catalog (never from the PDF's metadata):

```json
{
  "chunk_id": "PMC6226095-p2-c0",
  "pmcid": "PMC6226095",
  "page": 2,
  "title": "m6A facilitates hippocampus-dependent learning and memory through Ythdf1",
  "citation": "Nature. Author manuscript; Available in PMC 2019 Apr 30.",
  "license": "TDM",
  "text": "10Department of Psychiatry, Perelman School of Medicine, … m6A is abundant in the nervous system and modulates various neural functions6–11."
}
```

### `build.py`: the command

```python
def build(catalog: dict[str, Paper], raw_dir: Path, client: QdrantClient, embed, name: str = COLLECTION) -> tuple[int, int, int]   # (papers, pages, chunks)
def main()   # load_catalog(CATALOG_PATH), build(catalog, RAW_DIR, client, TextEmbedding(EMBED_MODEL).embed), print the report
```

`build` takes the catalog, folder, client, embedder and collection name as
arguments so the integration tests can run it on a temporary folder, a fake
embedder and a test collection. `python -m neuro_rag.ingest.build` runs `main`,
and `build` does, in order:
1. `select_papers(raw_dir, catalog)`.
2. For each selected paper: `parse_pdf`, then `chunk_page` on each page.
   A `ParseError` prints its message and the build goes on with the next paper.
3. Nothing to write (no chunks) → print "nothing to build" and exit with code 1,
   without touching Qdrant.
4. `recreate_collection(client, name)`, `write_chunks(client, chunks, catalog, embed, name)`.
5. Check: `client.count(name, exact=True).count` equals the number of
   chunks; if not, print both numbers and exit with code 1.
6. Return (papers built, pages, chunks); `main` prints the report and exits with code 0.

**The report** for the 52 papers:
```
built 52 papers, 642 pages, 4431 chunks into "papers" in 41.2 s
```
(41.2 s is only an illustration of the format; the time isn't checked.)

## Choices (to confirm)

1. **Dense vectors only.** Keyword (BM25) search was in v2's first version;
   here it is a candidate for row 8 "Better search", added only if the eval
   shows it helps. The collection is recreated by every build, so adding a
   second vector later costs nothing.
2. **Plain PyMuPDF text, no layout handling.** No column detection, no table
   or figure removal, no font-based headings (v2 had all of these, in 150
   lines). Known noise that stays: affiliations (s0 above), figure captions,
   table cells. The eval measures what that noise costs before anything is
   added.
3. **Repeated lines and page numbers are dropped,** two short rules that
   remove about 10,600 lines of headers, footers and page numbers.
4. **References dropped up to "Methods",** so the four Nature-style papers
   keep their Methods.
5. **A hyphen at a line end is kept** ("long-term", "m6A-specific"). Removing
   it would also merge real compound words ("longterm"); the cost is the
   occasional "hippo-campus".
6. **Chunks of at most 200 tokens, packed from sentences, with a one-sentence
   overlap of at most 50 tokens.** v2 used a library splitter
   (`RecursiveCharacterTextSplitter`, 200 / 64); the rule here is written
   out so it can be coded and explained without a library.
7. **The collection is deleted and recreated by every build, with no alias
   and no snapshot.** v2 built versioned collections behind an alias and
   wrote snapshots; that matters once a deployed service reads the data,
   which is row 7's job.
8. **The catalog is the only source of a paper's title, citation and
   license.** The PDFs' checksums (`pdf_md5`) are not checked: the 52 files
   don't change, and a changed file would show up as different chunk counts
   in the build report (IN-14).

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is checked is in [validation.md](validation.md).

### Which papers are built

**IN-1: a PDF that isn't kept in the catalog isn't selected.**
- **Given** `data/raw/` holding the 52 kept PDFs plus `PMC6925997.pdf`, whose
  catalog row has `keep=no`.
- **When** `select_papers` runs.
- **Then** exactly the 52 kept papers are selected, each paired with its
  `Paper`, and `PMC6925997.pdf` is not among them.
- **Why:** a paper outside the catalog has no checked title, citation or
  license, so an answer couldn't cite it properly.

**IN-2: a PDF that can't be read is reported, and the build continues.**
- **Given** a file `PMC0000002.pdf` holding the bytes "not a pdf", and a
  readable PDF next to it.
- **When** `parse_pdf` runs on the first, and the build runs on both.
- **Then** `parse_pdf` raises `ParseError` with a message starting "can't open
  PMC0000002.pdf", and the build prints that message and still builds the
  other.
- **Why:** one bad file out of 52 shouldn't stop the other 51.

### Clean pages

**IN-3: lines on more than half of a paper's pages are dropped.**
- **Given** a 4-page paper where "Shi et al." is on pages 1, 2 and 3, and
  "Hippocampal neurogenesis" on pages 1 and 2 only.
- **When** `body_lines` runs.
- **Then** "Shi et al." is gone from every page (3 of 4 is more than half),
  and "Hippocampal neurogenesis" stays (2 of 4 is not).
- **Why:** running headers ("Nature. Author manuscript…", the authors' names)
  repeated in hundreds of chunks would make many chunks look alike and match
  questions on journal names instead of content.

**IN-4: page-number lines are dropped, numbers inside text are not.**
- **Given** a page with the lines "7", "Page 7 of 37", and "In 7 of 9 mice
  the effect was absent."
- **When** `body_lines` runs.
- **Then** the first two are dropped and the third is kept.
- **Why:** a page number is noise in a chunk; a number in a sentence is content.

**IN-5: the reference list is dropped, and a Methods section after it is kept.**
- **Given** a paper whose page 2 has "…memory was impaired.", "References",
  "1. Smith J. Neuron 2019;12:1–9.", and whose page 3 has "2. Lee K. Cell
  2020;3:4–8.", "Methods", "Mice were trained for 5 days."
- **When** `body_lines` runs.
- **Then** page 2 keeps only "…memory was impaired." and page 3 keeps
  "Methods" and "Mice were trained for 5 days."
- **Why:** a reference list is 15,000 lines of titles of other papers; its
  chunks would match many questions while saying nothing this paper found.
  Four papers put their Methods after the references, and those are content.

**IN-6: lines are joined into clean text, keeping hyphens.**
- **Given** the lines "regulates fates through m6A-", "specific binding
  proteins and ﬁne", "control of   long-", "term potentiation."
- **When** `join_lines` runs.
- **Then** the result is "regulates fates through m6A-specific binding proteins
  and fine control of long-term potentiation."
- **Why:** a word split at a line end must come back as one word ("m6A-specific",
  not "m6A- specific"), or neither search nor the answer would see it.

**IN-7: each page keeps its own number, even when earlier pages are dropped.**
- **Given** a 3-page PDF whose page 1 has no text left after `body_lines`.
- **When** `parse_pdf` runs.
- **Then** it returns 2 pages, numbered 2 and 3.
- **Why:** the page is what the answer cites; renumbering would send the
  reader to the wrong page.

### Chunks

**IN-8: the tokenizer counts real tokens, not a padded length.**
- **Given** the `TokenCounter` for `all-MiniLM-L6-v2`.
- **When** it counts "m6A is abundant in the nervous system and modulates
  various neural functions6–11." and the 31-word sentence "Here we show that,
  through its binding protein Ythdf1, m6A promotes protein synthesis of target
  transcripts in response to neuronal stimuli in the adult mouse hippocampus,
  thereby facilitating learning and memory."
- **Then** it returns 19 and 46.
- **Why:** with the tokenizer's built-in padding left on, both would count as
  128, and the size limit in IN-10 would pass without measuring anything.

**IN-9: chunks are packed from sentences, with a one-sentence overlap.**
- **Given** a page whose sentences have 112, 50, 19, 35, 46, 43, 75, 31, 37
  and 32 tokens (PMC6226095 page 2, the worked example), and a counter that
  returns those numbers.
- **When** `chunk_page` runs with `size=200, carry=50`.
- **Then** the first three chunks hold sentences 0–2 (181 tokens), 2–5 (143)
  and 5–8 (186), with IDs `PMC6226095-p2-c0`, `-c1`, `-c2`.
- **Why:** a cut between sentences keeps each statement whole, and the carried
  sentence means a fact at a chunk's edge is found whole in one of the two.

**IN-10: a sentence longer than the chunk size is cut between words.**
- **Given** the 46-token sentence "Here we show that, through its binding
  protein Ythdf1, m6A promotes protein synthesis of target transcripts in
  response to neuronal stimuli in the adult mouse hippocampus, thereby
  facilitating learning and memory.", the real `TokenCounter`, and `size=20`
  (small, so a real sentence is over the limit).
- **When** `chunk_page` runs.
- **Then** it returns 3 chunks of 20, 20 and 6 tokens: "Here we show that,
  through its binding protein Ythdf1, m6A promotes protein synthesis", "of
  target transcripts in response to neuronal stimuli in the adult mouse
  hippocampus," and "thereby facilitating learning and memory."
- **Why:** the model ignores everything after its 256th token; an oversized
  chunk would be stored with text its vector doesn't represent. With
  `size=200`, the same rule cuts the 53 real "sentences" over 200 tokens in the
  papers (tables and figure text, the longest 1,062 tokens).

**IN-11: the same PDF gives the same chunks and IDs every time.**
- **Given** PMC6226095.pdf.
- **When** it is parsed and chunked twice.
- **Then** both runs give the same list of chunk IDs and texts, and
  `point_id("PMC6226095-p2-c0")` is the same UUID both times.
- **Why:** the eval records which chunks were retrieved by ID; IDs that
  change between builds would make two eval runs impossible to compare.

### The collection

**IN-12: every chunk is one point, with its text, vector, paper and page.**
- **Given** the chunk `PMC6226095-p2-c0` and the catalog row for PMC6226095.
- **When** `write_chunks` runs into a fresh test collection.
- **Then** the point with ID `point_id("PMC6226095-p2-c0")` has a 384-number
  vector and exactly the payload shown in "Payload of one point": `chunk_id`,
  `pmcid`, `page` 2, the catalog's `title`, `citation` and `license`, and the
  chunk's text.
- **Why:** search returns points; everything the answer needs to quote and
  cite must be on the point itself.

**IN-13: a build replaces the collection, it doesn't add to it.**
- **Given** a collection `papers` holding 10 points from an earlier build.
- **When** the build runs on the 52 papers.
- **Then** the collection holds exactly 4,431 points, the number of chunks
  built, and none of the old 10 remain unless rebuilt.
- **Why:** leftover points from an older build would be found by search and
  cited, with text that no longer matches the current rules.

**IN-14: the full build reports what it did.**
- **Given** the 52 PDFs and the catalog.
- **When** `python -m neuro_rag.ingest.build` runs.
- **Then** it prints "built 52 papers, 642 pages, 4431 chunks into "papers"
  in … s" and exits with code 0.
- **Why:** the counts are the first sign something changed: a different number
  of chunks after a code change, or after a PDF was replaced, means something
  is new and worth a look.

## Out of scope

- Downloading the PDFs (done once; they are in `data/raw/`, outside git).
- Checking the PDFs' checksums (choice 8).
- OCR of scanned PDFs; tables, figures and equations as structured data.
- Keyword (BM25) vectors (row 8, if the eval shows they help).
- Versioned collections, an alias and snapshots (row 7, deployment).
- Adding one paper to an existing collection; every build is full.
