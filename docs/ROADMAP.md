# Neuro-RAG Assistant: Roadmap

What the product is, and every functionality in the order it is built. Each
module's spec and validation are in [specs/](specs/), written when its row
starts.

## Product

**Purpose.** Answer questions about hippocampus and memory neuroscience with
grounded, cited answers. Answers come from 52 open-access papers and, only when
the papers can't answer, from vetted web sources, marked as such. Wrong answers
in a science domain are costly, so the system says when it doesn't know.

**Users.** Students and researchers, served by one answer style: plain
sentences, with technical terms kept and briefly explained the first time they
appear. Questions come in their own words: precise terminology, casual phrasing
or typos.

Answers are in English. Example:
- Question: "front bit vs back bit of the hippocampus, which one does what when
  you remember pairs of things?"
- Answer: "The front (rostral) hippocampus is more active while pairs are being
  learned (encoding), the back (caudal) part while they are recalled
  (retrieval) [1]."

**Scope.**

| Question kind | Example | Behaviour |
|---|---|---|
| Covered by the papers | "How does m6A RNA methylation support hippocampus-dependent learning?" | answer from the papers, every claim cited to paper and page |
| Neuroscience, not in the papers | "How does dopamine loss in the substantia nigra cause Parkinson's motor symptoms?" | say the papers don't cover it, then answer from vetted web sources, marked as web |
| Outside neuroscience | "What's a good recipe for sourdough bread?" | decline in one sentence |
| Borderline (psychology of memory, sleep, brain health) | "Does sleep help memory?" | in scope; when in doubt, never decline |
| False premise | "Why does the hippocampus store memories permanently?" | correct the premise from the sources |

**Non-goals.** A UI, multi-turn chat memory, user accounts, papers that aren't
open access, medical advice for individuals.

**Delivered as.** A public HTTP API (`POST /ask`), deployed, with its eval
numbers and a trace of every request.

**System-wide targets.**

| Area | Target |
|---|---|
| Latency (p95) | from the papers ≤ 6 s; with web search ≤ 30 s |
| Reliability | a failing optional part (web search, a grader call) degrades the answer, never crashes the request |
| Citations | every `[n]` in an answer maps to a listed source |
| Cost | measured per request from traces; a target set after the first measured run |
| Security | API keys only in environment variables; never in images, logs or traces |

## Functionalities

Built in this order. Status: planned → spec written → built → validated.

| # | Functionality | Done when | Status |
|---|---|---|---|
| 1 | Ingest and index | the 52 papers are searchable chunks, each knowing its paper and page, with a dense and a BM25 vector | validated (GROBID + BM25, 2026-11-05) |
| 2 | Search | a question returns its top 5 chunks by dense or hybrid search, and the two are compared on the eval questions | validated (dense default, 2026-11-07) |
| 3 | Cited answer | a question gets an answer citing paper and page | validated (2026-11-08) |
| 4 | Eval and baseline score | rows 1–3 have a measured score on the 50 English questions | validated (2026-11-16): correctness 0.67, faithful 0.97, page@5 0.67, $0.0052 a question |
| 5 | API | `POST /ask` answers over HTTP | validated (2026-11-15) |
| 6 | Tracing | every request is traced: its steps, timings, tokens and cost | validated (2026-11-16) |
| 7 | Deployment | the API runs on Kubernetes with a public URL, and the eval runs against it. Decided in its spec (2026-11-16): k3s on one small VM (about $5–10 a month; a managed cluster is about $70+), with the API as a Deployment, Qdrant as a StatefulSet with a persistent volume, the API key as a Secret, and an Ingress for the URL. Also: CI with GitHub Actions running the free tests (`pytest -m "not integration and not llm"`) on every push; CD (build, push the image, update k3s automatically) added once the manual deploy works | validated (2026-11-18), live at http://204.168.182.10 |
| 8 | Better search | a reranker or tuning, kept only if the eval improves on the baseline | validated (2026-11-18), live: dense top 20 reranked by a cross-encoder (Xenova/ms-marco-MiniLM-L-6-v2), top 5; eval correctness 0.67 → 0.78, faithful 0.97 = 0.97, page@5 0.67 → 0.72, p50 1.7 → 2.5 s, $0.0052 → $0.0054 a question (`eval/results/2026-11-18_2157_rerank/`); image 1518ab4; VM 2.0 GB of 3.7 GB still available |
| 9 | **Corrective RAG loop** (the project's core: `advanded_rag_project.txt` steps 4, 5, 7) | each question goes through explicit, inspectable states: **retrieve** (search + rerank) → **grade** (are these chunks good enough to answer from?) → if not, **rewrite** the question once (clear English, typos and casual wording fixed) and **retry** retrieval → if still not, **web fallback** (vetted sources, marked as web) → **generate** the cited answer. The API returns the path taken and whether the web was used (`path`, `used_web`), and every state is a step in the Langfuse trace. Proven with an eval **with vs without the loop**, against row 8 (correctness 0.78). To decide in its spec: the grader (four compared: Jev, a fine-tuned grader of our own, Gemma, Laya), the web search tool, and the orchestration (LangGraph, as the plan suggests, or a plain function with the same states) | spec written (2026-11-19) |
| 10 | Declining | off-topic questions are declined before the loop runs, with no false declines on borderline ones | planned |

1–7 is the walking skeleton: the simplest version that works end to end, and is
live. Each row after it is an improvement, kept only if the eval shows it helps.

## Choices, accepted 2026-10-25

1. **One answer style for everyone**, shown by the example above.
2. **English only.** The 4 non-English questions in the set (German,
   French, Spanish, Arabic) are not run (decided 2026-11-09): the English
   embedding model can't search them, so they would only measure a known 0.
   Row 9's rewriter may translate them and bring them back.
3. **Deployment is in the skeleton (row 7), not at the end.** v2 left it last
   and never reached it; deploying early means every later row is measured on
   the live system.
4. **Rows 8–10 are named by the problem, not the technique.** "Better search"
   may become hybrid search, a reranker or both; the loop's grader may become
   a reranker score or an LLM grader. Each is chosen in its spec from what the
   eval shows. v2's results (hybrid search, a reranker at 0.68 → 0.75
   correctness, an LLM grader) are evidence for those specs.
5. **Tracing is its own row (6),** right after the API, so every request on the
   live system is traced from the start.
6. **The question set is v2's, unchanged:** 54 questions with reference
   answers and expected papers.
7. **Hybrid search is built and compared in row 2, before deployment**
   (decided 2026-11-03), not left for row 8. Row 1 stores a BM25 vector next
   to the dense one; row 2 compares the two modes on the eval questions'
   expected sources and picks the default. Row 8 keeps the reranker and
   tuning.

8. **Every yes/no decision uses the cheapest model that passes the eval**
   (added 2026-11-18). Tried in this order, keeping the first that matches an
   LLM's quality on the eval: (1) a threshold on a score we already have, $0;
   (2) a local open decision model (e.g. Laya, Apache-2.0, small enough for
   CPU), $0 but VM memory; (3) a hosted decision model (e.g. Jev, about
   $0.00002 a call); (4) an LLM call (Haiku, about $0.001). The main saving
   is calls avoided: a cheap "no" stops the pipeline before Claude answers.
   The answer itself and the eval judges stay with Claude. To confirm in
   each row's spec:
   - **row 9, the corrective loop's grade:** "are these chunks good enough
     to answer from?" (row 8's reranker score is the first candidate); it
     decides both the rewrite-and-retry and the web fallback, so the rewrite
     call runs only when retrieval is weak;
   - **row 10:** "on-topic?" runs before search, so an off-domain question
     costs no Claude call (in the baseline it still cost about $0.0024).

9. **Rows 9, 10 and 11 merged into one corrective RAG loop** (2026-11-18).
   They were "question rewriting", "not in the papers" and "web search": the
   three parts of the corrective loop that `advanded_rag_project.txt` names as
   the project's point (grade → rewrite/retry → web fallback, as explicit
   states, proven by an eval with vs without the loop). Split under neutral
   names, the loop itself had dropped out of the plan. Old row 12 (declining)
   is now row 10.

Candidates for later, each measured before it is kept: streaming answers.
