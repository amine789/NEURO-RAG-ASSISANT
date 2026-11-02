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
| 1 | Ingest and index | the 52 papers are searchable chunks, each knowing its paper and page | validated |
| 2 | Search | a question returns its top 5 chunks | planned |
| 3 | Cited answer | a question gets an answer citing paper and page | planned |
| 4 | Eval and baseline score | rows 1–3 have a measured score on the 54 questions | planned |
| 5 | API | `POST /ask` answers over HTTP | planned |
| 6 | Tracing | every request is traced: its steps, timings, tokens and cost | planned |
| 7 | Deployment | the API has a public URL, and the eval runs against it | planned |
| 8 | Better search | kept only if the eval improves on the baseline | planned |
| 9 | "Not in the papers" | questions the papers can't answer are recognised, measured | planned |
| 10 | Web search | those questions are answered from vetted web sources, marked as web | planned |
| 11 | Declining | off-topic questions are declined, with no false declines on borderline ones | planned |

1–7 is the walking skeleton: the simplest version that works end to end, and is
live. Each row after it is an improvement, kept only if the eval shows it helps.

## Choices, accepted 2026-10-25

1. **One answer style for everyone**, shown by the example above.
2. **English answers only.** The 4 non-English questions in the set (German,
   French, Spanish, Arabic) are reported but left out of the overall score.
3. **Deployment is in the skeleton (row 7), not at the end.** v2 left it last
   and never reached it; deploying early means every later row is measured on
   the live system.
4. **Rows 8–11 are named by the problem, not the technique.** "Better search"
   may become hybrid search, a reranker or both; "Not in the papers" may become
   a reranker score or an LLM grader. Each is chosen in its spec from what the
   eval shows. v2's results (hybrid search, a reranker at 0.68 → 0.75
   correctness, an LLM grader) are evidence for those specs.
5. **Tracing is its own row (6),** right after the API, so every request on the
   live system is traced from the start.
6. **The question set is v2's, unchanged:** 54 questions with reference
   answers and expected papers.

Candidates for later, each measured before it is kept: query rewriting,
streaming answers.
