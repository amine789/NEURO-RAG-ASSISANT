# Correction: spec

What this module must do. Written when its row in [ROADMAP.md](../../ROADMAP.md)
starts.

## Goal

When the chunks are not good enough, improve the search: rewrite the query, then search the web.

This spec covers the **rewrite** (row 7a). Web search (row 7b) is added here
when its row starts. Calling the rewrite when grading fails, and searching
again, is orchestration's job, in its own spec.

## In and out

- **In:** the user's question, exactly as asked.
- **Out:** one search query: English, in the vocabulary the papers use, with
  every specific term of the question kept.

```
question ──► Claude Haiku 5.5 (thinking off, structured output) ──► {"query": "..."} ──► one-line query
```

Why rewriting: retrieval misses questions asked in everyday words or in
another language. Retrieval RT-7: "How do the fear center and the memory
center keep their rhythms in step…?" never finds its paper, which says
"amygdala" and "phase synchrony". The reranker eval (row 6a): 8 questions with
an expected paper still missed it, 4 of them not in English.

## Settings

| Setting | Value | Why |
|---|---|---|
| model | `claude-haiku-5-5` | one model for every LLM call (ARCHITECTURE) |
| thinking | off: `{"type": "disabled"}` | grading showed default thinking adds about 1 s at p95; CR-5 to CR-8 show whether quality holds without it |
| effort | `low` | the project's setting for every call |
| rewrites per question | 1 | each costs a call and a search; the eval says whether a second would help |
| longest query kept | 60 words | a longer reply is an answer or an essay, not a query |
| latency limit | none here; reported by CR-10 | the rewrite runs alongside grading (orchestration spec), so its limit comes from the rewritten path's budget there |

## How it is built

Everything the code does is written here; anything not written here is not
built. The choices behind it, and why, are listed at the end.

### Files

| File | Holds |
|---|---|
| `src/neuro_rag/correction/__init__.py` | empty |
| `src/neuro_rag/correction/rewrite.py` | `REWRITE_SCHEMA`, `PROMPT`, `MAX_WORDS`, `RewriteError`, `Rewriter` |
| `tests/test_rewrite.py` | unit tests with a fake Claude client: CR-1 to CR-4 |
| `tests/test_rewrite_llm.py` | real Claude, marked `llm`: CR-5 to CR-8 |
| `tests/test_rewrite_corpus.py` | real index, reranker and Claude, marked `llm`: CR-9, CR-10 (CR-10 also rewrites the 20 known-paper questions) |

### The prompt

`PROMPT`, exactly; `{question}` is filled in:

```
You rewrite a user's question into a search query for a collection of scientific papers on the hippocampus and memory.

Rules:
- Write the query in English, whatever language the question is in.
- Replace everyday words with the terms the papers would use (for example "fear center" becomes "amygdala").
- Keep every specific term from the question unchanged: gene and protein names, brain regions, species, methods.
- Keep the question's meaning. Don't answer it, don't add claims, and don't narrow it to one hypothesis.
- Write one line, at most 30 words: a short question or phrase.

Examples:
Question: why do I keep forgetting where I put my keys?
Query: everyday forgetting of object locations; spatial memory retrieval and the hippocampus

Question: Est-ce que le stress abîme la mémoire ?
Query: effects of chronic stress on memory and hippocampal function

Question: {question}
```

The two examples are not eval questions, so the eval doesn't measure the
rewrite on questions it was shown.

### The reply

`REWRITE_SCHEMA`, sent as the structured output format:

```json
{
  "type": "object",
  "properties": {"query": {"type": "string"}},
  "required": ["query"],
  "additionalProperties": false
}
```

### `Rewriter.rewrite()`

```python
class RewriteError(Exception): ...

class Rewriter:
    def __init__(self, client: anthropic.Anthropic | None = None,
                 model: str = LLM_MODEL, effort: str = LLM_EFFORT)
    def rewrite(self, question: str) -> str
```

1. Build the prompt as above.
2. Call `client.messages.create` with `model`, `max_tokens=256`, one user
   message holding the prompt, `thinking={"type": "disabled"}`, and
   `output_config={"effort": effort, "format": {"type": "json_schema", "schema": REWRITE_SCHEMA}}`.
3. If the call raises `anthropic.APIError`, raise
   `RewriteError("rewrite call failed: <the error>")`.
4. If `stop_reason` is `"refusal"`, raise `RewriteError("rewriter refused")`.
5. Parse the first text block as JSON and take `query`. If it isn't JSON, or
   has no `query`, raise `RewriteError("rewriter reply isn't JSON: <first 100 characters>")`.
6. Make it one line: replace every run of whitespace (spaces, tabs, line
   breaks) with one space, and strip both ends.
7. If the result is empty, raise `RewriteError("rewrite is empty")`. If it has
   more than `MAX_WORDS` = 60 words (split on spaces), raise
   `RewriteError("rewrite is 74 words, more than 60")` (with the real count).
8. Return it.

Example: reply `{"query": "  amygdala hippocampus\ntheta phase synchrony  "}`
→ `"amygdala hippocampus theta phase synchrony"`.

### The CR-9 retrieval run

1. **Questions:** the eval questions whose expected paper was **missed** by
   retrieval with the reranker: their expected paper was in the top 5 in at
   most half of their 3 repeats in
   `eval/results/2026-10-18_2224_rerank/runs.jsonl` (field `retrieval_hit`).
   Off-domain, out-of-corpus and borderline questions are not included: they
   have no expected paper. On 2026-10-21 that is 8 questions: q30, q31, q33,
   q36, q37, q38, q39, q40.
2. **For each:** rewrite it with a `Rewriter`; retrieve the **rewritten query**
   with a `Retriever` with the reranker, `k=5`; it is **found** if any of the
   5 chunks comes from one of its expected papers. Record the rewrite's time.
3. **Printed:** one line per question: found or not, id, the question, the
   rewritten query, the rewrite's time; then the count found and the rewrite
   p50 and p95. p50 is the sorted time at position n // 2; p95 the one at
   position round(0.95 × n) − 1 (counting from 0). Example: 8 times → p95 is
   position 7, the slowest.
4. The tests are skipped, not failed, if Qdrant or the `hippocampus` index
   isn't available.

### The CR-10 timing run

1. **Questions:** 28: the 8 from the CR-9 run, plus the 20 known-paper
   questions in `tests/data/known_papers.jsonl` (retrieval RT-7).
2. **Times:** the 8 CR-9 rewrite times are reused; each of the 20 known-paper
   questions is rewritten once and timed the same way (the `rewrite()` call
   only, no retrieval).
3. **p95** is the sorted time at position round(0.95 × 28) − 1 = 26 (counting
   from 0), the second slowest, so one slow call doesn't decide it.
4. **Printed:** the p50 and p95 of the 28 times. No limit is checked here.

Why 28 and not 8: with 8 times, p95 is position 7, the slowest single call.
The first run failed on one Arabic question at 2.08 s while the other 7 took
1.2–1.9 s (2026-10-21).

### Choices, and why

Accepted 2026-10-21.

1. **Thinking off.** Reason: the same ~1 s saving as grading; CR-5 to CR-8
   check the rewrites stay good.
2. **The query keeps a question's meaning but uses the papers' words,** in
   English, at most 30 words (the prompt asks); the code only rejects
   replies over 60 words (twice the asked length, so a slightly long but
   valid query still passes).
3. **Two examples in the prompt, neither from the eval.**
4. **The rewrite always runs on the user's original question,** never on a
   previous rewrite.
5. **CR-9 target: at least 4 of the 8 missed questions find their paper
   after rewriting.** Reason: the 4 non-English ones should be found once
   translated; any of the 4 English ones found on top shows the vocabulary
   change works.
6. **CR-10 reports the rewrite's p95 and checks no limit** (accepted
   2026-10-21). Reason: a 2 s limit was first set "the same as grading", not
   derived from anything, and measured p95 2.49 s over 28 calls. The rewrite
   runs alongside the first grade (orchestration spec), so what matters is
   the rewritten path's total time, which orchestration's spec sets and
   checks.

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is run is in [validation.md](validation.md).

### With a fake Claude client

**CR-1: the request sends the question with the rules and examples.**
- **Given** a fake Claude client that records the request.
- **When** `rewrite("How do the fear center and the memory center keep their
  rhythms in step when people form unpleasant memories?")` is called.
- **Then** exactly one request was made, with model `claude-haiku-5-5`,
  thinking `{"type": "disabled"}`, effort `low`, `REWRITE_SCHEMA` as the
  output format, and the prompt is `PROMPT` with the question after the last
  "Question: ".
- **Why:** a prompt that lost the rules or the examples would still return
  queries, just worse ones, and nothing else would show it.

**CR-2: the query comes back as one clean line.**
- **Given** a fake Claude whose reply is
  `{"query": "  amygdala hippocampus\ntheta phase synchrony  "}`.
- **When** a question is rewritten.
- **Then** the result is `"amygdala hippocampus theta phase synchrony"`.
- **Why:** a line break or leading space would reach the encoders and the
  trace as part of the query.

**CR-3: an empty or overlong rewrite is an error.**
- **Given** three replies in turn: `{"query": "   "}`; a query of 74 words;
  a query of exactly 60 words.
- **When** each is returned.
- **Then** the first raises `RewriteError("rewrite is empty")`; the second
  raises `RewriteError("rewrite is 74 words, more than 60")`; the third is
  returned unchanged.
- **Why:** an empty query would search for nothing; a 74-word reply is an
  answer or an essay. The third checks the limit is not off by one.

**CR-4: a failed, refused or unreadable call is an error.**
- **Given** three situations: a fake Claude that raises an API connection
  error; a reply with `stop_reason` "refusal"; a reply whose text is
  `amygdala hippocampus` (not JSON).
- **When** a question is rewritten in each.
- **Then** each raises `RewriteError`: "rewrite call failed: …", "rewriter
  refused", and "rewriter reply isn't JSON: 'amygdala hippocampus'".
- **Why:** orchestration decides what to do when the rewrite fails (its own
  spec says what); it needs one clear error, not an SDK exception or an empty
  query.

### With the real Claude

**CR-5: everyday words become the papers' terms.**
- **Given** the question "How do the fear center and the memory center keep
  their rhythms in step when people form unpleasant memories?"
- **When** it is rewritten.
- **Then** the query contains "amygdala", and "hippocampus" or
  "hippocampal" (any capitalization).
- **Why:** this is the question retrieval can't answer from these words
  (retrieval RT-7); its paper says "amygdala" and "hippocampal".

**CR-6: a question in another language becomes an English query.**
- **Given** the German question "Welche Rolle spielt der ventrale Hippocampus
  dabei, sich zu merken, wo es Futter gibt?" (eval q37).
- **When** it is rewritten.
- **Then** the query contains "ventral hippocampus" and one of "food",
  "foraging" or "reward", and none of the German words "Rolle", "dabei",
  "merken" or "Futter".
- **Why:** the dense encoder is English-only; the baseline found nothing for
  all four non-English questions.

**CR-7: the rewrite is a query, not an answer.**
- **Given** the question "is there some pill you can take right after studying
  that makes the stuff stick better?" (eval q23).
- **When** it is rewritten.
- **Then** the query has at most 30 words, does not start with "Yes" or
  "No", and contains at least one of "consolidation", "pharmacolog",
  "enhanc" or "post-training" (any capitalization).
- **Why:** an answer searched for instead of the question would steer
  retrieval towards whatever the model already believes.

**CR-8: a precise question keeps its exact terms.**
- **Given** the question "What is the role of Ythdf1 in m6A-dependent
  translation in the hippocampus?"
- **When** it is rewritten.
- **Then** the query contains "Ythdf1" and "m6A" exactly as written.
- **Why:** keyword search finds gene and protein names only if they are
  spelled the same; a rewrite that "improves" them to "YTH domain family
  protein 1" would lose the match.

### On the real index

**CR-9: rewriting finds papers that retrieval missed.**
- **Given** the real index, the reranker, and the 8 eval questions whose
  paper retrieval missed ("The CR-9 retrieval run", above).
- **When** each is rewritten and the rewritten query is retrieved.
- **Then** at least 4 of the 8 find their expected paper in the top 5.
  About 8 calls: well under $0.01.
- **Why:** this is the reason the rewrite exists. If it doesn't find missed
  papers, wiring it into the flow would only add a call.

**CR-10: the rewrite's time is measured.**
- **Given** the 28 rewrite times of the CR-10 timing run (above).
- **When** their p50 and p95 are computed.
- **Then** both are printed, and the test checks only that there are 28.
- **Why:** orchestration runs the rewrite alongside the first grade and sets
  the rewritten path's budget; it needs this number to do so. A limit here,
  before that budget exists, would be a guess.

## Out of scope

- When the rewrite runs, and what happens next (orchestration, row 7a).
- Web search (row 7b).
- Several rewrites, or several queries searched at once.
