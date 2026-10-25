# Orchestration: spec

What this module must do. Written when its row in [ROADMAP.md](../../ROADMAP.md)
starts.

## Goal

Run the steps in order and decide the route: answer, correct, or decline.

This spec covers row 7a: grade the chunks, and when they fail, rewrite the
question and search again. Web search (row 7b) and declining (row 8) are added
when their rows start.

## In and out

- **In:** the user's question, and the request's trace (observability).
- **Out:** an `Outcome`: the answer (generation), and the **path** it took:
  - `papers`: the first chunks passed the grade;
  - `papers_rewritten`: they failed, the rewritten query's chunks passed;
  - `none`: both failed, or the rewrite failed; the answer says the papers
    don't cover it.
- **Called by:** the API, through `ask(question, trace)`, as since row 5. The
  API uses `outcome.answer`; the eval also reads `outcome.path`.

### The flow

Steps on the same line run at the same time.

```
1. retrieve(question) ──► rerank                                       → chunks A
2. grade(question, A)   ‖   rewrite(question)   ‖   generate(question, A)
3. grade passed ─────────► wait for generate(A) ───────────────────────► path papers
   grade failed ─────────► wait for rewrite ──► query
4.   retrieve(query) ──► rerank                                        → chunks B
5.   grade(question, B)   ‖   generate(question, B)
6.   grade passed ───────► wait for generate(B) ───────────────────────► path papers_rewritten
     grade failed ───────► "I couldn't find this in the papers." ──────► path none
```

Why at the same time: one Claude call takes about 1.5 s whatever it does
(grading GR-11: p95 1.77 s with no thinking; rewrite CR-10: p95 2.49 s), and
generation takes 2–4 s. Run one after the other, a passing question would
wait about 1.5 s longer than in row 6a, and a failing one about 7 s longer.
Run together, a passing question waits only for generation, which it waited
for anyway; the grade and the rewrite are ready before it.

What it costs: every question pays a grade and a rewrite even when they aren't
used, about $0.0004; every failing question also pays a discarded generation,
about $0.0005.

## Settings

| Setting | Value | Why |
|---|---|---|
| work at the same time | up to 3 Claude calls per question | step 2 runs three |
| question given to grade and generate | always the user's original question | the rewrite is for search; the answer must answer what was asked |
| rewrites | at most 1, from the original question | correction spec, choice 4 |
| answer when nothing passes | "I couldn't find this in the papers." | row 7b replaces this with web search |
| latency target, rewritten path | p95 ≤ 8 s | about 0.5 + 2.5 + 0.5 + 4 s (steps 1, 2, 4, 5), with margin; added to the ROADMAP's targets |

## How it is built

Everything the code does is written here; anything not written here is not
built. The choices behind it, and why, are listed at the end.

### Files

| File | Holds |
|---|---|
| `src/neuro_rag/orchestration/pipeline.py` | `NOT_FOUND_PAPERS`, `Outcome`, `Pipeline` (replaces the row 5 straight line) |
| `src/neuro_rag/api/app.py` | one change: `answer = state.pipeline.ask(...).answer`, and the API no longer sets the trace's output (the pipeline does, step 8). `build_pipeline()` is unchanged: the service gets a grader and a rewriter only after the row 7a eval shows they help |
| `tests/test_orchestration.py` | its own fakes for every step (below) and unit tests OR-1 to OR-8 |
| `tests/pipeline_fakes.py` | unchanged: `fake_pipeline()` has no grader, so the row 5 API and observability tests keep their three steps |

### `Outcome` and `Pipeline`

```python
NOT_FOUND_PAPERS = "I couldn't find this in the papers."

@dataclass(frozen=True)
class Outcome:
    answer: Answer
    path: str            # "papers" | "papers_rewritten" | "none"
    chunks: list = field(default_factory=list)   # the chunks the last grade saw (OR-9)
    query: str | None = None  # the rewritten query, when the second search ran (OR-9)

class Pipeline:
    def __init__(self, retriever, generator, reranker=None, grader=None, rewriter=None)
    def ask(self, question: str, trace: Trace) -> Outcome
    def index_name(self) -> str           # unchanged
```

`grader` and `rewriter` are optional. **Without a grader, `ask` runs exactly
as in row 5** (retrieve → rerank → generate, path `papers`), so the reranker
eval system and existing tests keep working. With a grader but no rewriter,
step 2 starts only grade and generate, and a failed grade returns
`Outcome(Answer(NOT_FOUND_PAPERS), "none")`.

### `ask()` with a grader and a rewriter

The pipeline owns one `ThreadPoolExecutor(max_workers=8)` for its lifetime;
`ask` submits work to it and never waits for work it doesn't use.

1. **Retrieve A:** step `retrieve`: `retriever.retrieve(question, k=20)`;
   then step `rerank`: keep 5 (as row 5).
2. **Start three at once,** in this order: step `grade` (`grader.grade(question, A)`),
   step `rewrite` (`rewriter.rewrite(question)`), step `generate`
   (`generator.answer(question, A)`). Each runs in the executor, inside its
   own trace step.
3. **Wait for the grade.**
   - If it passed: wait for generate(A) and return `Outcome(answer, "papers")`.
     The rewrite is not waited for.
   - If grading raised `GradingError`: treat it as passed (same as above). The
     grade step is marked as an error in the trace.
   - If it failed: wait for the rewrite.
4. **Rewrite result.**
   - If the rewrite raised `RewriteError`: return
     `Outcome(Answer(NOT_FOUND_PAPERS), "none")`. The rewrite step is marked as
     an error in the trace.
   - Otherwise `query` is the rewritten query. Step `retrieve`:
     `retriever.retrieve(query, k=20)`; step `rerank` with **the query** (the
     words that were searched); keep 5 → chunks B.
5. **Start two at once:** step `grade` (`grader.grade(question, B)`, the
   **original** question) and step `generate` (`generator.answer(question, B)`).
6. **Wait for the second grade.**
   - Passed, or `GradingError`: wait for generate(B); return
     `Outcome(answer, "papers_rewritten")`.
   - Failed: return `Outcome(Answer(NOT_FOUND_PAPERS), "none")` without
     waiting for generate(B).
7. **Errors from steps that are waited for** are raised as before:
   `RetrievalError` from either retrieve, `GenerationError` from the generate
   whose answer is returned. Errors from work that is not waited for (a
   discarded generate or rewrite) are recorded in its trace step and never
   raised.
8. **The trace's output** gets `"path": <path>` next to the answer and the
   pmcids (row 5's output). The rewrite step's output is the query. The
   returned `Outcome` also carries `chunks`, the chunks the last grade saw
   (A, or B once the second search ran; A without a grader), and `query`, the
   rewritten query once the second search ran, else `None` (added for the
   eval, EV-16; OR-9).

9. The executor is the attribute `pool`; tests call `pipeline.pool.shutdown(wait=True)`
   before reading the trace, so steps still running in the background have
   ended.

Example: the first grade fails, the rewrite returns "amygdala hippocampus
theta phase synchrony aversive memory", the second grade passes → steps in the
trace: retrieve, rerank, then grade, rewrite and generate (started together),
then retrieve, rerank, then grade and generate (started together); path
`papers_rewritten`; the returned answer is the second generate's.

### Choices, and why

Accepted 2026-10-21.

1. **Grade, rewrite and generate run at the same time.** Reason: a Claude call
   takes about 1.5 s whatever it does; run in a row, every question would wait
   for the grade first. Cost: about $0.0004 per question for a grade and a
   rewrite that a passing question doesn't use, and about $0.0005 for a
   discarded generation on a failing one.
2. **A grading error counts as passed.** Reason: grading is an optional check;
   the ROADMAP's reliability target says a failing optional part degrades the
   answer, never the request. The answer is the same as row 6a's would have
   been.
3. **A rewrite error, or two failed grades, end with "I couldn't find this in
   the papers."** and no answer from the chunks. Reason: both grades said the
   chunks don't answer the question, so an answer from them would be the
   unsupported answer the whole system exists to avoid. Until row 7b, that
   includes out-of-corpus questions.
4. **The second rerank uses the rewritten query; both grades and both
   generations use the original question.** Reason: the reranker should
   score against the words that were searched; the grade and the answer must
   be about what the user asked.
5. **Without a grader, `ask` is row 5's straight line.** Reason: the reranker
   system stays runnable in the eval for comparison.
6. **The pipeline is plain Python with a thread pool, not a LangGraph graph.**
   Reason: the flow is fixed: two branches, no loops, no tools; every step is
   already a traced step. v1 used LangGraph for the same flow; a framework
   would add a state object and a second way to trace. Reopen if the flow
   needs loops or tools the model decides on.
7. **Rewritten path target: p95 ≤ 8 s,** added to the ROADMAP; the corpus
   path keeps ≤ 6 s. Checked end to end by the eval (row 7a), not here.

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
All use fakes for every step and the recording tracer, so they are free and
the path is certain. The fakes: a retriever that returns chunks named after
the query it was given; a reranker; a grader that returns the grades it is
told to, in order; a rewriter that returns a given query; a generator that
answers with the text of the first chunk it was given. How each one is run is
in [validation.md](validation.md).

**OR-1: chunks that pass are answered at once, from the papers.**
- **Given** a grader that passes the first chunks, and a rewriter and
  generator that record their calls.
- **When** `ask("What do place cells encode?", trace)` runs.
- **Then** the outcome's path is `papers`; the answer came from the first
  chunks; retrieve was called once; the trace has retrieve, rerank, then
  grade, rewrite and generate, and no second retrieve.
- **Why:** most questions are answered from the first search. They must not
  wait for a second one.

**OR-2: a failed grade is rewritten, searched again and answered from the papers.**
- **Given** a grader that fails the first chunks and passes the second, and a
  rewriter that turns "How do the fear center and the memory center keep
  their rhythms in step…?" into "amygdala hippocampus theta phase synchrony
  aversive memory".
- **When** `ask` runs on that question.
- **Then** the path is `papers_rewritten`; the second retrieve searched the
  rewritten query; the second rerank scored against the rewritten query; the
  second grade and the second generate were given the **original** question
  and the second chunks; the answer is the second generate's.
- **Why:** searching with the papers' words finds the paper; answering the
  rewritten query instead of the question would answer something the user
  didn't ask.

**OR-3: two failed grades end with "couldn't find", not an unsupported answer.**
- **Given** a grader that fails both times.
- **When** `ask` runs.
- **Then** the path is `none`; the answer is "I couldn't find this in the
  papers." with no sources; it is returned without waiting for the second
  generate.
- **Why:** both grades said the chunks don't answer the question; answering
  from them would be exactly the unsupported answer the system must avoid.

**OR-4: grade, rewrite and generate run at the same time.**
- **Given** a grader, a rewriter and a generator that each take 0.3 s, and a
  grader that passes.
- **When** `ask` runs.
- **Then** it returns in less than 0.5 s (not 0.9 s), and the three steps'
  start times in the trace are within 0.1 s of each other.
- **Why:** this is what keeps a passing question as fast as in row 6a. If they
  ran one after the other, nothing else would show it except slower answers.

**OR-5: a passing question doesn't wait for the rewrite.**
- **Given** a grader that passes after 0.1 s, a generator that answers after
  0.2 s, and a rewriter that takes 2 s.
- **When** `ask` runs.
- **Then** it returns in less than 0.5 s, with path `papers`.
- **Why:** the rewrite is only needed when the grade fails; waiting for it
  would add its time to every answer.

**OR-6: a grading error counts as passed.**
- **Given** a grader that raises `GradingError("grading call failed")`.
- **When** `ask` runs.
- **Then** the path is `papers`, the answer is the first generate's, and the
  grade step in the trace is marked as an error with that message.
- **Why:** grading is an optional check; when it fails, the answer should be
  what it would have been without it, not an error.

**OR-7: a rewrite error ends with "couldn't find".**
- **Given** a grader that fails the first chunks, and a rewriter that raises
  `RewriteError("rewrite call failed")`.
- **When** `ask` runs.
- **Then** the path is `none`, the answer is "I couldn't find this in the
  papers.", retrieve was called only once, and the rewrite step is marked as
  an error with that message.
- **Why:** with no query to search again, and chunks the grade rejected, there
  is nothing supported to answer from.

**OR-8: without a grader, the flow is row 5's.**
- **Given** a pipeline built with a retriever, reranker and generator, and no
  grader or rewriter.
- **When** `ask("What do place cells encode?", trace)` runs.
- **Then** the path is `papers`, and the trace has exactly retrieve, rerank,
  generate.
- **Why:** the reranker system (row 6a) must stay runnable for comparison in
  the eval, and the row 5 API tests must keep passing unchanged.

**OR-9: the outcome carries the chunks it was decided on, and the rewritten query.**
- **Given** the pipeline with a grader that fails the first chunks and passes
  the second, and a rewriter returning "amygdala hippocampus theta phase
  synchrony aversive memory".
- **When** `ask(FEAR, trace)` runs (the fear-center question).
- **Then** `outcome.query` is that query and `outcome.chunks` are the second
  search's chunks (the first one's text is "amygdala hippocampus theta phase
  synchrony aversive memory | chunk 0" with the test's retriever). With a
  grader that passes the first chunks, `outcome.query` is `None` and
  `outcome.chunks` are the first search's.
- **Why:** the eval judges faithfulness against the chunks' texts and counts
  a retrieval hit from them; the trace holds only chunk ids (OB-2), so the
  outcome has to carry them.

## Out of scope

- Web search when both grades fail (row 7b).
- Declining off-topic questions (row 8). Until then an off-topic question
  fails both grades and gets "I couldn't find this in the papers." after a
  rewrite and a second search.
- Running the corrective system in the eval: eval spec, "The corrective
  system (row 7a)", EV-15 to EV-20.
