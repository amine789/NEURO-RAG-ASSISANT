# Corrective RAG loop: spec

Roadmap row 9, the project's core (`advanded_rag_project.txt` steps 4, 5 and 7):
retrieval is graded, corrected when weak, and the path taken is visible. The
grade is the loop's one decision, so free off-the-shelf graders (Gemma 3 1B
and Laya) are compared for it, and the best is used (roadmap choice 8). A fourth, fine-tuned
grader (G1) is deferred: built only if none of the three helps (choice 15).

## Goal

Today every question goes search → rerank → answer, whatever the chunks are
worth. The loop adds a **grade** after retrieval. Good chunks are answered as
now. Weak chunks get the question **rewritten** and retrieval **retried**, up to
`MAX_REWRITES` times; still weak, a **web search** on vetted sites, graded the
same way; weak again, the answer is "not covered", with no Claude answer call.
The API says which path was taken, and the trace shows every state.

Built in three phases, each with numbers:

1. **Graders compared** on the 50 eval questions: Gemma 3 1B (a small open
   LLM) and Laya (an open decision model). Both run locally,
   are free and need no training. A fine-tuned grader of our own (G1) is
   built only if none of them helps (choice 15).
2. **The loop**, using phase 1's winner.
3. **The proof:** the eval with the loop against the eval without it (row 8,
   correctness 0.78).

## In and out

- **In:** a question (row 5's API, row 4's eval).
- **Out:** row 3's `Answer`, plus `path` (the states in order) and `used_web`.
  The API response gains the two fields:
  ```json
  {"answer": "...", "sources": [...], "path": ["retrieve", "grade:weak", "rewrite", "retrieve", "grade:good", "generate"], "used_web": false}
  ```

```
            ┌──────── weak, rewrites left ────────┐
            ▼                                      │
question → retrieve → grade ──good──► generate     │
                        └──weak──► rewrite ────────┘
                        └──weak, no rewrites left──► web → grade ──good──► generate (sources marked web)
                                                             └──weak──► not_covered (NOT_FOUND, no Claude call)
```

## Phase 1: the graders

A grader takes the question and the 5 hits and returns a number in [0, 1]
(how likely the hits are good enough to answer from) and a decision
(good if the number is at least the grader's cut).

| Grader | How it decides | Cut | Cost a question | Tuned on our data? |
|---|---|---|---|---|
| **G1 fine-tuned** (deferred, choice 15) | our own cross-encoder: row 8's reranker (`ms-marco-MiniLM-L-6-v2`) fine-tuned on synthetic neuroscience pairs; the best of the 5 chunk probabilities | 0.5 | $0 | trained on synthetic data only |
| **G2a Gemma 270M** (dropped, choice 17) | the yes/no question "Do these passages contain the information needed to answer the question?" to Gemma 3 270M (instruction-tuned, quantized, about 250 MB), served locally by llama.cpp like Laya; the probability of yes is read from the answer token's log-probabilities | 0.5 | $0 (VM memory) | no: zero-shot |
| **G2b Gemma 1B** | the same, with Gemma 3 1B (instruction-tuned, quantized, about 0.8 GB), same server and prompt, a different model file | 0.5 | $0 (VM memory) | no: zero-shot |
| **G3 Laya** | the same yes/no question to Laya, an open decision model (Apache-2.0, about 450 MB), served locally by llama.cpp (as in `rawwerks/rdm`); returns the probability of yes | 0.5 | $0 (VM memory) | no: zero-shot |

### Labels: what "good retrieval" means on the eval

From row 8's eval (`eval/results/2026-11-18_2157_rerank/runs.jsonl`), per
question:

- **good:** an `answer_from_corpus` or `correct_premise` question whose answer
  was judged `correct` or `partial` (the papers could answer it);
- **weak:** one judged `wrong`, and every `decline` (off-domain) and
  `web_fallback` (out-of-corpus) question (the papers shouldn't answer it);
- **left out:** `not_declined` (borderline) questions, which have no verdict.

This is a proxy (a wrong answer can come from the generation, not the
retrieval); the same labels are used for every grader, so the comparison is fair.

### Keeping the test set clean

The 50 eval questions are the **test set**. Nothing is tuned on them:

- **G2b, G3:** zero-shot; the question wording is written now (above) and
  not changed after seeing results; the cut is fixed (0.5, yes/no), not fitted.
- **G1:** trained and checked only on synthetic data (below); the eval
  questions are used once, for the final number.
- A grader's mistakes are counted in two kinds: **weak judged good** (a bad
  answer goes out: costly) and **good judged weak** (an extra rewrite: cheap).

### G1's training data (deferred, choice 15)

Built only if G2b and G3 fail (choice 15). G1 is trained on **papers the system has never seen**, so its test score
measures how well it judges relevance on new papers, not how well it remembers
ours. None of the 52 indexed papers (and none of the 14 excluded candidates) is
used for training.

- **Training papers:** 40 new open-access papers on hippocampus and memory,
  found with NCBI's E-utilities on PubMed Central's open-access subset (query in
  `scripts/fetch_grader_papers.py`), CC BY or CC BY-NC, published 2015 or later,
  with a PDF. Any PMCID already in `data/candidates.csv` is skipped. Saved under
  `data/grader/` (gitignored), with their own catalog `data/grader/catalog.csv`.
- **Same pipeline as row 1:** parsed by GROBID with `parse_pdf`, cut with
  `chunk_page` (200 tokens, 50 overlap), written to a JSONL file; they are not
  indexed into Qdrant, so the live system never sees them. About 3,000 chunks.
- **Answerable pairs:** Haiku writes 3 questions for each of 500 chunks drawn
  across the 40 papers, in the eval's styles (direct, casual, typos and loose
  terms; prompt in `scripts/make_grader_data.py`). Positive: (question, its
  chunk). Hard negatives: (question, the 3 best-reranked chunks from **other**
  training papers), found with in-memory dense search plus row 8's reranker over
  the 3,000 chunks.
- **Unanswerable questions:** Haiku writes 300: 150 off-domain (cooking, tax,
  code, general medicine) and 150 on neuroscience topics outside these papers.
  Each paired with its 3 best-reranked training chunks, all negatives.
- **No leaks:** any synthetic question whose MiniLM embedding has cosine ≥ 0.9
  with an eval question is dropped (a second guard; the papers already differ).
- **Split by paper:** 32 papers train, 8 dev; the dev set picks the number of
  epochs, nothing else.
- **Training:** `sentence-transformers` `CrossEncoder`, binary labels, on the
  laptop's CPU (a dev dependency, not in the image). Exported to ONNX and run
  in the API with `onnxruntime` and `tokenizers`, which are already in the lock.
- Cost: about 1,800 Haiku-written questions, about $0.50, once; GROBID locally
  (`docker compose --profile ingest up -d`), about 3 minutes for 40 papers.

### Choosing the grader

All are free, so the most accurate one is used, unless another is within
0.05 of it with fewer "weak judged good" mistakes; a remaining tie goes to the
one using less VM memory.

## Phase 2: the loop

### Settings

| Setting | Value | Why |
|---|---|---|
| retrieve | row 8's search: dense top 20, reranked, top 5 | the validated default |
| grade | phase 1's chosen grader | |
| rewrite | one Haiku call through `make_llm()`: rewrite the question as a clear English search query (fix typos, casual wording, translate), reply with the query only; each rewrite sees the previous query too | runs only after a weak grade |
| `MAX_REWRITES` | 2 | a real loop, but bounded: latency and cost stay predictable |
| retrieval after a rewrite | the **rewritten** query searches; the **original** question is answered | the user's wording is what the answer must address |
| web | choice 2; at most 5 pages from the allow-list, cut into chunks as in row 1, reranked, graded | the same grade applies to web text |
| allow-list | `pubmed.ncbi.nlm.nih.gov`, `pmc.ncbi.nlm.nih.gov`, `www.ncbi.nlm.nih.gov`, `www.nature.com`, `www.science.org`, `www.cell.com`, `elifesciences.org`, `www.jneurosci.org`, `en.wikipedia.org` | "vetted web sources" (roadmap product) |
| web hits | `Hit` with `pmcid="web"`, `page=0`, `title` = page title, `citation` = domain, and a new field `url` (default `""`) | `answer()` cites them like papers; the source's `url` is the page |
| not_covered | row 3's `NOT_FOUND`, no sources, no Claude answer call | |
| failures | a failing rewrite, grader or web call is logged and treated as weak; the loop moves on | roadmap reliability target |
| tracing | each state is an `@observe` step | the path is visible in Langfuse (plan step 7) |
| latency target | ≤ 6 s from the papers, ≤ 30 s with the web (roadmap) | |

### The loop

```python
def run_loop(question, search_fn, grade_fn, answer_fn, rewrite_fn, web_fn) -> CragResult:
    path, query = [], question
    for attempt in range(MAX_REWRITES + 1):
        path.append("retrieve")
        hits = search_fn(query)
        if grade(grade_fn, question, hits, path):        # appends "grade:good" or "grade:weak"
            return CragResult(answer_fn(question, hits), path + ["generate"], False)
        if attempt < MAX_REWRITES:
            path.append("rewrite")
            query = rewrite_fn(question, query) or query  # None if the call failed
    path.append("web")
    hits = web_fn(query)                                  # [] if the call failed
    if grade(grade_fn, question, hits, path):
        return CragResult(answer_fn(question, hits), path + ["generate"], True)
    return CragResult(Answer(NOT_FOUND, [], [], 0, 0), path + ["not_covered"], False)
```

Every function is passed in, so the tests drive every branch with fakes.

### Files

| File | Change |
|---|---|
| `src/neuro_rag/crag/__init__.py` | empty |
| `src/neuro_rag/crag/graders.py` | `finetuned_grader` (only if G1 is built), `gemma_grader` (Gemma 3 1B, via the server's URL), `laya_grader`: each `(question, hits) -> float` |
| `src/neuro_rag/crag/loop.py` | `CragResult(answer, path, used_web)`, `run_loop`, `rewrite`, `web_hits` |
| `src/neuro_rag/config.py` | `GRADE_CUT`, `MAX_REWRITES`, `WEB_DOMAINS`, `GRADER` |
| `src/neuro_rag/retrieval/search.py` | `Hit` gains `url: str = ""` (default keeps every caller and test unchanged) |
| `src/neuro_rag/generation/answer.py` | a source's `url` is `hit.url` when set, else the PMC link |
| `src/neuro_rag/api/app.py` | `ask` calls `run_loop`; `AskResponse` gains `path` and `used_web` |
| `src/neuro_rag/eval/run.py` | `--crag`; the run record gains `path` and `used_web` |
| `src/neuro_rag/eval/report.py` | a `web used` column for `web_fallback` questions; rewrites per question |
| `scripts/compare_graders.py` | phase 1: the graders (G2b, G3, plus G1 if built) on the eval questions, the table |
| `scripts/fetch_grader_papers.py` | G1's 40 training papers: search, download, catalog (written, run only if G1 is built) |
| `scripts/make_grader_data.py` | G1's synthetic data: parse, chunk, questions, pairs, split |
| `scripts/train_grader.py` | G1's training, dev check and ONNX export |
| `tests/test_crag.py` | the loop's criteria, with fakes |
| `docker-compose.yml`, `deploy/k8s/llm-local.yaml` | G2 and G3: llama.cpp servers for Gemma and Laya, locally and, only for the chosen one, on the VM |

## Choices, accepted 2026-11-19

1. **Free graders compared, the best one used.** G2b Gemma 1B, G3 Laya (and G1 fine-tuned only if built, choice 15), as above, with the rule in "Choosing the grader".
   A threshold on row 8's raw reranker score was dropped (2026-11-19): its cut
   would have to be fitted, and a cut fitted on one set of questions doesn't
   transfer to questions written differently.
2. **Nothing fitted on the eval:** G2b and G3 zero-shot with fixed wording
   and a fixed cut; G1 trained on synthetic data only, so the 50 eval questions stay a
   test set.
3. **G1 is row 8's reranker fine-tuned,** not a new model: the same size (about
   80 MB) on the VM, trained on CPU, run with `onnxruntime` (already in the
   lock). `sentence-transformers` and its PyTorch are dev-only.
4. **Jev dropped** (2026-11-20): it is a paid API, and every other grader is
   free. It was a hosted decision model, reachable through TypeSafe, AIMLAPI,
   Vercel's AI Gateway (`/v1/decisions`, $0.042 per million input tokens) or
   OpenRouter; Laya stays as the decision model in the comparison.
5. **A bounded loop, `MAX_REWRITES = 2`,** then the web. One rewrite was the
   first draft; two let a casual question be corrected twice while keeping
   latency predictable.
6. **Orchestration: a plain function** (`run_loop` above). LangGraph, which
   the plan suggests, would add a dependency for the same states; it stays a
   candidate if the loop gains branches.
7. **Web search: Firecrawl** (one call returns page text; the key is already
   in `.env` and the Secret), or `ddgs` (free) plus fetching pages with
   `requests` and BeautifulSoup. Firecrawl's price to be checked first.
8. **The API response gains `path` and `used_web`;** row 5's AP-1 asserts the
   exact JSON, so **its expected JSON gains the two fields**: a change to a
   validated criterion.
9. **The eval's `web_fallback` questions** (q19, q43) count as handled when the
   answer has web sources; `decline` questions (q20, q44, q51 to q54) still when
   not covered. Known risk: q20 (metformin) and q53 (ibuprofen) are medical, so
   NCBI or Wikipedia pages might grade well and get answered; row 10 declines
   before the loop.
10. **One cut, two actions (good, weak).** The CRAG paper uses two thresholds
    and a third, "ambiguous" action (papers and web together); it is a
    candidate once phase 3's numbers are in.
11. **Laya (G3) as the decision model, free and local.** It runs as one more
    service (a llama.cpp server): in `docker-compose.yml` for phase 1, and on
    the VM only if it is chosen. About 450 MB of model plus the server; the VM
    has about 2 GB available, so DP-style memory checks come first. How
    llama.cpp exposes Laya's yes/no probability is checked against Laya's and
    `rawwerks/rdm`'s docs before wiring it.
12. **Gemma (G2) instead of Haiku as the LLM grader** (2026-11-19). All
    graders are free and local, so the comparison is a decision model, a small
    open LLM and our own fine-tuned model, with no paid model in the grade. This is the first exception to "every LLM call via
    ChatAnthropic on Haiku 4.5": Gemma only grades; the rewrite, the answer and
    the eval judges stay on Haiku. Gemma 3 1B because the 4 GB VM can't hold a
    4B model next to the rest; its licence is Google's Gemma terms, not
    Apache-2.0.
13. **Liquid d1 (G4): added, then removed the same day** (2026-11-20; see
    choice 16). As first added: a second open decision model,
    next to Laya: d1-3B for the comparison, on the laptop (about 2 GB
    quantized, a few seconds a grade on CPU). It doesn't fit on the 4 GB VM
    next to the rest; if it wins, its smaller sibling d1-omni-600M (an early
    research release) is measured the same way before anything is deployed,
    and the VM keeps the best grader that fits. How to run it (Liquid's code
    from the model card, or llama.cpp) is checked before wiring. Its licence,
    LFM Open License v1.0, is free for us (it restricts companies above $10M
    revenue).
14. **G1 trains on 40 new papers, not on the indexed 52** (2026-11-20).
    Sampling chunks from the indexed corpus would let G1 see the very chunks
    the eval questions are answered from (they draw on 29 of the 52 papers), and
    its test score would partly measure memory. Training on unseen papers keeps
    the test honest and checks transfer to new papers. The alternative, training
    on the 23 papers no eval question uses, was simpler but stays inside the
    same corpus.
15. **Off-the-shelf graders first, G1 deferred** (2026-11-20). The
    off-the-shelf graders need no data and no training; G1 needs 40 papers, about $0.50 of Haiku
    questions, training and an ONNX export. So phase 1 compares those only,
    the loop is built with the winner, and G1 (with CR-1 and CR-2) is built
    only if CR-12 fails, meaning no off-the-shelf grader improves on row 8.
    G1 then joins the comparison in CR-3. `scripts/fetch_grader_papers.py`
    is written and kept for that case, not run.
16. **Liquid d1 removed; Gemma 3 270M added next to 1B** (2026-11-20). d1-3B
    (about 2 GB) doesn't fit on the VM and needs its own runtime, so it could
    win the comparison and still not ship. Gemma 3 270M (about 250 MB) is the
    cheapest option that fits; it runs on the same llama.cpp server as the 1B
    with only a different model file, so both are measured in one run. Only
    the winner is deployed.
17. **Gemma 3 270M dropped** (2026-11-20) after a two-question smoke test,
    before any eval run: with one passage on hippocampal memory consolidation,
    it gave P(yes) 0.96 for "What does the hippocampus do?" and 0.92 for "How do
    I bake sourdough bread?". It says yes regardless of relevance, so it can't
    grade zero-shot. The prompt was not changed to rescue it. Gemma 3 1B
    (Q4_K_M, about 0.8 GB) takes its place in the same llama.cpp service.

## Acceptance criteria

### Phase 1: graders (scripts)

CR-1 and CR-2 apply only if G1 is built (choice 15).

**CR-1: G1's training data comes from new papers only, and is clean.** (deferred)
- **When** `python scripts/fetch_grader_papers.py` then
  `python scripts/make_grader_data.py` run.
- **Then** the catalog has 40 papers, none of whose PMCIDs is in
  `data/candidates.csv`; the script writes the training and dev files, prints
  their sizes (about 1,500 answerable and 300 unanswerable questions before
  filtering) and how many were dropped as too close to an eval question, and
  shows no paper in both train and dev.

**CR-2: G1 trains and beats its starting point on the dev set.** (deferred)
- **When** `python scripts/train_grader.py` runs.
- **Then** on the synthetic dev set, the fine-tuned model's accuracy is higher
  than the un-tuned reranker's (both at cut 0.5); it writes the ONNX model to
  `models/grader/` (gitignored).

**CR-3: the graders are compared on the eval questions.**
- **When** `python scripts/compare_graders.py` runs (G2b and G3
  locally, free; G1 too if it is built).
- **Then** it prints, for each grader: accuracy, weak judged good, good judged weak, cost and median latency a question; and the
  grader chosen by the rule. The table is recorded in validation.md.

### Phase 2: the loop (unit, fakes, no API call)

Fakes: `search_fn` returns hits marked good or weak and records its queries;
`grade_fn` reads that mark; `answer_fn` records `(question, hits)`;
`rewrite_fn` returns `"clear query 1"`, then `"clear query 2"`, and counts calls;
`web_fn` returns hits marked good or weak.

**CR-4: good retrieval answers directly.**
- **Then** `path == ["retrieve", "grade:good", "generate"]`; `rewrite_fn` and
  `web_fn` never called; `used_web` false.

**CR-5: weak retrieval is rewritten and retried; the original question is answered.**
- **Given** weak for the question, good for `"clear query 1"`.
- **Then** `path == ["retrieve", "grade:weak", "rewrite", "retrieve", "grade:good", "generate"]`;
  `search_fn` got `[question, "clear query 1"]`; `answer_fn` got the
  **original** question.

**CR-6: the loop stops after `MAX_REWRITES`, then the web.**
- **Given** weak for every query, good web hits.
- **Then** `rewrite_fn` was called exactly 2 times; the path has 3
  `"retrieve"` and ends `"web", "grade:good", "generate"`; `used_web` true;
  `web_fn` got `"clear query 2"`.

**CR-7: weak everywhere is "not covered", with no answer call.**
- **Then** the path ends `"not_covered"`, the answer is `NOT_FOUND` with no
  sources, `answer_fn` never called.

**CR-8: failures degrade, never crash.**
- **Given** `rewrite_fn`, `web_fn` and `grade_fn` raising.
- **Then** no exception escapes; a failing grade counts as weak; with
  everything failing the path ends `"not_covered"`.

**CR-9: web hits come only from the allow-list, and link to their page.**
- **Given** web results from `www.nature.com` and `random-blog.example`.
- **Then** only the nature.com one becomes a `Hit` (`pmcid="web"`, its `url`);
  when Claude cites it, its `Source.url` is that page, and paper sources are
  unchanged.

**CR-10: the API returns the path.**
- **Then** `POST /ask` returns `path` and `used_web` next to `answer` and
  `sources` (AP-1 updated, choice 8).

**CR-11: every state is in the trace.** (by hand)
- **Given** the server with tracing on and a casual question that takes the
  rewrite path.
- **Then** its Langfuse trace shows each `retrieve`, `grade`, `rewrite` and
  `generate` step in order.

### Phase 3: the proof (real Claude, about $0.30)

**CR-12: the eval with the loop beats the eval without it.**
- **When** `python -m neuro_rag.eval.run --name crag --rerank --crag` runs.
- **Then**, against row 8's run (`2026-11-18_2157_rerank`): correctness above
  0.78; faithful at least 0.95; `decline` questions not covered (1.00);
  `web_fallback` questions answered from the web; rewrites per question and
  web use reported; p95 within the latency targets. Kept only if correctness
  goes up.
- **Why:** the plan's step 8: before/after numbers are the proof the loop is
  not decoration.

## Out of scope

- Declining off-topic questions before the loop (row 10).
- The "ambiguous" action (choice 10).
- A UI showing the path (the plan's step 9).
- LangGraph (choice 6), unless the loop gains branches.
