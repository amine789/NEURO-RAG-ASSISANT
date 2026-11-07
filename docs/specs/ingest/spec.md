# Ingest and index: spec

Roadmap row 1: the 52 papers become searchable chunks, each knowing its paper
and page.

## Goal

Turn the kept papers in the catalog into a Qdrant collection of chunks, where
each chunk holds its text, two vectors (a dense one for meaning, a BM25 one for
keywords), and the paper and page it came from, so an answer can cite "paper,
page".

## In and out

- **In:**
  - the catalog `data/candidates.csv`: 66 rows, 52 with `keep=yes`. Columns:
    `keep, pmcid, title, citation, license, pdf_url, pdf_md5`; ingest reads
    `keep, pmcid, title, citation, license`;
  - the PDFs in `data/raw/`, named `<pmcid>.pdf` (52 files, 826 pages);
  - GROBID's output for each PDF, saved in `data/tei/<pmcid>.tei.xml` the
    first time a PDF is parsed and reused after that.
- **Out:** the Qdrant collection `papers`, one point per chunk, and a report
  printed at the end of the build.
- **Runs:** offline, on the laptop, as one command against a local Qdrant
  container:
  ```
  docker compose --profile ingest up -d     # Qdrant and GROBID
  python -m neuro_rag.ingest.build
  ```

```
candidates.csv ─┐
                ├─► select papers ─► for each PDF: GROBID ─► kept parts ─► chunks ─► embed ─► Qdrant "papers"
data/raw/*.pdf ─┘    (keep=yes)        (TEI XML, saved     (abstract,     (≤ 200     (dense: 384
                                         in data/tei/)      body, figure    tokens)    numbers;
                                                            captions)                  bm25: word
                                                                                       weights)
```

## Settings

| Setting | Value | Why |
|---|---|---|
| PDF reader | GROBID `0.9.1-crf` in Docker, `/api/processFulltextDocument` with `teiCoordinates` `p`, `head`, `figure` | a model trained on scientific papers tags each part (heading, paragraph, figure caption, reference, back matter) and gives its page; measured against PMC's own XML (choice 2) |
| embedding model | `sentence-transformers/all-MiniLM-L6-v2` through FastEmbed (ONNX), 384 numbers | small, fast on a CPU, no PyTorch in the deployed image |
| keyword model | `Qdrant/bm25` through FastEmbed (`SparseTextEmbedding`), stored as the sparse vector `bm25` with Qdrant's IDF modifier | lets search (row 2) compare dense against hybrid; exact terms such as "Ythdf1" or "CA1" are what dense vectors blur |
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
| `pyproject.toml` | package `neuro-rag`, Python ≥ 3.11; dependencies `requests`, `tokenizers`, `fastembed`, `qdrant-client`; dev dependency `pytest` |
| `docker-compose.yml` | service `qdrant`, image `qdrant/qdrant:v1.19.1`, port 6333, a named volume; service `grobid`, image `grobid/grobid:0.9.1-crf`, port 8070, profile `ingest` (started only for a build) |
| `src/neuro_rag/config.py` | paths (`DATA_DIR`, `CATALOG_PATH`, `RAW_DIR`, `TEI_DIR`), `QDRANT_URL` and `GROBID_URL` from the environment (defaults `http://localhost:6333`, `http://localhost:8070`), `COLLECTION = "papers"`, `EMBED_MODEL`, `EMBED_SIZE = 384`, `SPARSE_MODEL = "Qdrant/bm25"`, `CHUNK_TOKENS = 200`, `CARRY_TOKENS = 50`, `BATCH = 64` |
| `src/neuro_rag/ingest/catalog.py` | `Paper`, `load_catalog`, `select_papers` |
| `src/neuro_rag/ingest/parse.py` | `Page`, `ParseError`, `grobid_tei`, `kept_elements`, `tei_pages`, `parse_pdf` |
| `src/neuro_rag/ingest/chunk.py` | `Chunk`, `TokenCounter`, `split_sentences`, `chunk_page` |
| `src/neuro_rag/ingest/index.py` | `point_id`, `recreate_collection`, `write_chunks` |
| `src/neuro_rag/ingest/build.py` | `build()` and `main()`: runs everything and prints the report |
| `tests/test_ingest.py` | unit tests, no Qdrant needed |
| `tests/test_ingest_index.py` | tests against the running Qdrant and GROBID, marked `integration` |

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

def grobid_tei(path: Path, tei_dir: Path = TEI_DIR) -> Path                    # the saved TEI file; calls GROBID only if it is missing
def kept_elements(root: ET.Element) -> list[tuple[ET.Element, str | None]]      # (element, coords) in reading order
def tei_pages(tei: Path, pmcid: str) -> list[Page]
def parse_pdf(path: Path, pmcid: str, tei_dir: Path = TEI_DIR) -> list[Page]   # grobid_tei, then tei_pages
```

**`grobid_tei` steps:**
1. If `tei_dir/<pmcid>.tei.xml` exists and isn't empty, return it: GROBID is
   not called again. The 52 saved files are in `data/tei/` (outside git);
   making them takes about 25 minutes, reading them under a second.
2. Otherwise POST the PDF to `GROBID_URL/api/processFulltextDocument` as the
   form field `input`, with `teiCoordinates` = `p`, `head`, `figure`, timeout
   600 s.
3. A status other than 200 → `ParseError(f"can't open {path.name}: GROBID returned {status} {first 100 characters}")`.
   For the bytes "not a pdf" GROBID returns 500 "[BAD_INPUT_DATA] PDF to XML
   conversion failed".
4. Write the response to the file and return it.

**`kept_elements`: which parts are kept, by their TEI tag:**

| Kept | Dropped |
|---|---|
| every `<p>` in `<abstract>` | everything in `<back>`: the reference list (`<listBibl>`), acknowledgements and other back matter |
| every `<head>` and `<p>` in `<body>`, in reading order | inside a `<figure>`: its `<head>`, `<label>`, tables and any text GROBID read off the image (axis ticks, panel letters) |
| every `<figDesc>` (figure caption) in `<body>` | the title page block (`<teiHeader>` other than the abstract) |

Inline tags inside a kept element stay as text: `<ref type="bibr">[1]</ref>`
gives "[1]".

**`tei_pages` steps:**
1. For each kept element in order, its page is the first number of its
   `coords` (`"3,90.0,504.3,55.8,11.1;4,…"` → 3); a `<figDesc>` uses its
   `<figure>`'s coords. An element with no coords takes the page of the
   element before it (page 1 if none). On the 52 papers, 360 of 3,931 kept
   elements have no coords, mostly section headings.
2. Its text is all its text joined (`"".join(element.itertext())`), every run
   of whitespace replaced by one space, stripped.
3. Texts on the same page are joined with one space, in order, into one
   `Page`. Pages with no kept text don't appear; page numbers are never
   renumbered.

`parse_pdf`: no page at all → `ParseError(f"no text in {path.name}")`.

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

**Worked example: a page with ten sentences.** The token counts are those of
PMC6226095 page 2 under the earlier PyMuPDF parse; with GROBID that page
starts differently, so the example is illustrative:

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

**On the whole corpus:** 628 pages with text, **4,313 chunks**, largest 200
tokens.

### `index.py`: into Qdrant

```python
def point_id(chunk_id: str) -> str   # str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
def recreate_collection(client: QdrantClient, name: str = COLLECTION) -> None
def write_chunks(client: QdrantClient, chunks: list[Chunk], papers: dict[str, Paper], embed, sparse_embed, name: str = COLLECTION) -> int
```

- `point_id`: Qdrant only accepts integers or UUIDs as point IDs; a UUID
  derived from the chunk ID is the same on every build.
  `point_id("PMC6226095-p2-c0")` always returns the same UUID.
- `recreate_collection`: deletes `name` if it exists, then creates it with
  two named vectors:
  - `vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)}`;
  - `sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)}`.
- `write_chunks`, in batches of 64 chunks:
  1. `vectors = list(embed(texts))` and `sparse = list(sparse_embed(texts))`,
     with `texts = [c.text for c in batch]`. `embed` is
     `TextEmbedding(EMBED_MODEL).embed` and `sparse_embed` is
     `SparseTextEmbedding(SPARSE_MODEL).embed`, both passed in so tests can
     use fakes.
  2. One `PointStruct` per chunk: `id=point_id(chunk_id)`,
     `vector={"dense": vector.tolist(), "bm25": SparseVector(indices=s.indices.tolist(), values=s.values.tolist())}`,
     and the payload below. `client.upsert(name, points, wait=True)`.
  3. Returns the number of points written.

**What the BM25 vector holds.** One weight per distinct word, after
lower-casing, stemming and dropping stop words. For a chunk (`embed`), a word's
weight grows with how often it appears, with diminishing returns:
"Ythdf1 promotes protein synthesis of Ythdf1 targets." gives 5 entries ("of"
is dropped), "ythdf1" weighing 1.8957 (twice) and the other four 1.6653. How
rare a word is across the 4,313 chunks (IDF) is not stored: Qdrant applies it
at search time (`Modifier.IDF`), so it always matches the current collection.

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
def build(catalog: dict[str, Paper], raw_dir: Path, client: QdrantClient, embed, sparse_embed, name: str = COLLECTION, tei_dir: Path = TEI_DIR) -> tuple[int, int, int]   # (papers, pages, chunks)
def main()   # load_catalog(CATALOG_PATH), build(catalog, RAW_DIR, client, TextEmbedding(EMBED_MODEL).embed, SparseTextEmbedding(SPARSE_MODEL).embed), print the report
```

`build` takes the catalog, folder, client, both embedders and collection name
as arguments so the integration tests can run it on a temporary folder, fake
embedders and a test collection. `python -m neuro_rag.ingest.build` runs `main`,
and `build` does, in order:
1. `select_papers(raw_dir, catalog)`.
2. For each selected paper: `parse_pdf`, then `chunk_page` on each page.
   A `ParseError` prints its message and the build goes on with the next paper.
3. Nothing to write (no chunks) → print "nothing to build" and exit with code 1,
   without touching Qdrant.
4. `recreate_collection(client, name)`, `write_chunks(client, chunks, catalog, embed, sparse_embed, name)`.
5. Check: `client.count(name, exact=True).count` equals the number of
   chunks; if not, print both numbers and exit with code 1.
6. Return (papers built, pages, chunks); `main` prints the report and exits with code 0.

**The report** for the 52 papers:
```
built 52 papers, 628 pages, 4313 chunks into "papers" in 41.2 s
```
(41.2 s is only an illustration of the format; the time isn't checked.)

## Choices (to confirm)

1. **Two vectors per chunk: dense and BM25** (changed 2026-11-03; was dense
   only). Search (row 2) compares dense against hybrid on the eval questions
   before deployment, so both must be in the collection. Both are named
   (`dense`, `bm25`) so a search says which one it uses.
2. **GROBID, not hand-written PDF rules.** The first version read plain
   PyMuPDF text and dropped headers, page numbers and references with
   regexes; a scan of the 52 papers (2026-11-02) showed those rules guess at
   layout and lost figure legends in about 10 papers and kept back matter in
   42. GROBID tags each part instead. Measured against PMC's own XML for the
   same papers (`data/grobid_check/compare_all.py`, word counts of abstract,
   body and captions): **median recall 97.8%, median precision 95.9%**; 37 of
   52 papers are at or above 85% on both. All 52 are kept (accepted
   2026-11-03); the eval (row 4) decides whether the weakest need more work.
   Known faults: PMC5053807 recall 47%; PMC5406700 precision 66%; in
   PMC6226095 "m6A" comes out as "m 6 A" (the "6" read as a citation) and its
   abstract is the PMC licence notice. The `crf` image (0.5 GB, CPU) is used
   instead of `full` (14.8 GB, wants a GPU).
3. **Parts are kept or dropped by tag** (the table in `parse.py`), with no
   rules about ordering: references and back matter are wherever GROBID
   finds them.
4. **A paragraph's page is the page it starts on.** A paragraph running over
   two pages is cited to the first.
5. **GROBID's output is saved and reused.** It is the slow step (about 30 s a
   paper); saving it makes every later build a few seconds of parsing.
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
- **Given** a file `PMC0000002.pdf` holding the bytes "not a pdf", no saved
  TEI for it, GROBID running, and a readable paper next to it.
- **When** `parse_pdf` runs on the first, and the build runs on both.
- **Then** `parse_pdf` raises `ParseError` with a message starting "can't open
  PMC0000002.pdf", and the build prints that message and still builds the
  other.
- **Why:** one bad file out of 52 shouldn't stop the other 51.

### Clean pages

**IN-3: the abstract, body and figure captions are kept; references, back matter and figure internals are dropped.**
- **Given** a TEI file with the abstract paragraph "Sleep helps memory." (page
  1), the heading "Results" and paragraph "Mice were trained for 5 days."
  (page 2), a figure (page 3) with head "Figure 1", label "0 20 40" and
  caption "Ythdf1-KO mice learn more slowly.", and in `<back>` the
  acknowledgement "We thank the lab." and one reference.
- **When** `parse_pdf` runs.
- **Then** it returns page 1 "Sleep helps memory.", page 2 "Results Mice were
  trained for 5 days." and page 3 "Ythdf1-KO mice learn more slowly.", and
  nothing else.
- **Why:** references and acknowledgements describe other papers and the
  authors, not this paper's findings; axis ticks are noise. The caption says
  what a figure shows.

**IN-4: each part is on the page it starts on, and pages are never renumbered.**
- **Given** a TEI body with a paragraph "Starts on page 3." whose coords are
  `3,…;4,…`, then a heading "No coordinates." with no coords, then a
  paragraph "On page 5." with coords `5,…`.
- **When** `parse_pdf` runs.
- **Then** it returns page 3 "Starts on page 3. No coordinates." and page 5
  "On page 5.".
- **Why:** the page is what the answer cites; a wrong page sends the reader to
  the wrong place.

**IN-5: whitespace is squeezed, and inline tags stay as text.**
- **Given** the paragraph `Learning   requires⏎ protein <ref type="bibr">[1]</ref> synthesis.`
- **When** `parse_pdf` runs.
- **Then** the page text is "Learning requires protein [1] synthesis."
- **Why:** line breaks and runs of spaces come from the layout, not the text.

**IN-6: a saved GROBID output is reused, without calling GROBID.**
- **Given** a saved `PMC0000006.tei.xml` with the paragraph "Saved." and no
  PDF and no GROBID.
- **When** `parse_pdf` runs.
- **Then** it returns page 1 "Saved.".
- **Why:** GROBID takes about 25 minutes for the 52 papers; a rebuild after a
  chunking change shouldn't repeat that.

**IN-7: a paper with no kept text raises an error.**
- **Given** a saved TEI that holds only a reference list.
- **When** `parse_pdf` runs.
- **Then** it raises `ParseError` with a message starting "no text in
  PMC0000007.pdf".
- **Why:** a paper that gives no chunks should be reported, not silently
  missing from the index.

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

**IN-12: every chunk is one point, with its text, both vectors, paper and page.**
- **Given** the chunk `PMC6226095-p2-c0`, the catalog row for PMC6226095, a
  fake `embed` returning 384 × 0.1, and a fake `sparse_embed` returning
  indices `[7, 42]` and values `[1.5, 0.5]`.
- **When** `write_chunks` runs into a fresh test collection.
- **Then** the point with ID `point_id("PMC6226095-p2-c0")` has a 384-number
  `dense` vector, a `bm25` vector with indices `[7, 42]` and values
  `[1.5, 0.5]`, and exactly the payload shown in "Payload of one point":
  `chunk_id`, `pmcid`, `page` 2, the catalog's `title`, `citation` and
  `license`, and the chunk's text.
- **Why:** search returns points; everything the answer needs to quote and
  cite must be on the point itself.

**IN-13: a build replaces the collection, it doesn't add to it.**
- **Given** a collection `papers` holding 10 points from an earlier build.
- **When** the build runs on the 52 papers.
- **Then** the collection holds exactly 4,313 points, the number of chunks
  built, and none of the old 10 remain unless rebuilt.
- **Why:** leftover points from an older build would be found by search and
  cited, with text that no longer matches the current rules.

**IN-14: the full build reports what it did.**
- **Given** the 52 PDFs and the catalog.
- **When** `python -m neuro_rag.ingest.build` runs.
- **Then** it prints "built 52 papers, 628 pages, 4313 chunks into "papers"
  in … s" and exits with code 0.
- **Why:** the counts are the first sign something changed: a different number
  of chunks after a code change, or after a PDF was replaced, means something
  is new and worth a look.

## Out of scope

- Downloading the PDFs (done once; they are in `data/raw/`, outside git).
- Checking the PDFs' checksums (choice 8).
- OCR of scanned PDFs; tables, figures and equations as structured data.
- Versioned collections, an alias and snapshots (row 7, deployment).
- Adding one paper to an existing collection; every build is full.
