# Eval: spec

What this module must do. Written when its row in [ROADMAP.md](../../ROADMAP.md)
starts.

## Goal

Score the system on a fixed question set, so every change can be compared with the last.

Row 4 runs it on the **baseline**: retrieval (row 2) then generation (row 3),
nothing else. The baseline report is the score every later row has to beat.

## In and out

- **In:** the question set, `eval/questions.jsonl`, and the system to score.
- **Out:** a folder `eval/results/<date>_<name>/` with:
  - `runs.jsonl`: one line per question per repeat, everything measured;
  - `report.md`: the scores, overall and by question type.

```
questions.jsonl ──► for each question, 3 times:
                       retrieve ──► generate ──► measure in code ──► judge with an LLM
                ──► runs.jsonl ──► report.md
```

## The question set

The 54 questions from v1, copied unchanged. Each has an `id`, a `type` (direct,
casual, typos, keywords, multi_paper, false_premise, out_of_corpus, off_domain,
borderline, multilingual…), the behaviour expected, a reference answer where one
exists, and the papers and pages where the answer is found. Two examples:

- `q01`, direct: "How does m6A RNA methylation support hippocampus-dependent
  learning and memory?" Reference: "The m6A reader Ythdf1 enhances translation of
  m6A-modified transcripts… Ythdf1-knockout mice show learning and memory
  defects…". Expected source: PMC6226095, page 2.
- `q51`, off_domain: "What's a good recipe for sourdough bread?" No reference,
  no expected source.

Known limits, kept from v1: the questions were drafted by Claude from paper
abstracts, so they share wording with the text they retrieve, and real users'
questions are harder.

## What is measured

| Measure | For which questions | How |
|---|---|---|
| retrieval hit | those with expected sources | code: an expected paper is among the 5 retrieved chunks |
| cites expected paper | those with expected sources | code: an expected paper is in the answer's source list |
| correctness | those with a reference answer, answered from the corpus | judge: correct (1), partial (0.5) or wrong (0) against the reference |
| faithfulness | every answer that cites something | judge: every claim is supported by the text of the chunks it cites |
| says "not covered" | off_domain and out_of_corpus | code: the answer cites nothing |
| latency | all | code: retrieval and generation time, in seconds |
| cost | all | code: tokens, converted to dollars at Haiku's price |

## Settings

| Setting | Start | Why |
|---|---|---|
| repeats | 3 | the model doesn't answer the same way every time; 3 runs show how much scores move |
| judge model | `claude-haiku-5-5` | one model everywhere, cheap; checked against a person by EV-11 ([decision 004](../../decisions/004-eval-judge.md)) |
| judge output | structured JSON (the API's structured outputs) | the verdict always parses; v1's free-text judge failed to parse 5 times |

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own:
**Given** the situation, **When** what is run, **Then** what must be true,
**Why** what is broken if it fails. How each one is run is in
[validation.md](validation.md).

### Running

**EV-1: every question is run the requested number of times.**
- **Given** the 54-question set.
- **When** the eval is run with `--repeats 3`.
- **Then** `runs.jsonl` has 162 lines, three for each question id, numbered
  repeat 1, 2 and 3.
- **Why:** a missing run would make one question count less than the others
  without anyone noticing.

**EV-2: a failing run is recorded, and the eval continues.**
- **Given** a run where generation raises an error (for example Claude is
  unavailable for that one call).
- **When** the eval reaches it.
- **Then** that run's line in `runs.jsonl` has the error message and no answer,
  and the eval goes on to the next run.
- **Why:** one failure in 162 runs must not throw away the other 161.

**EV-3: an interrupted eval resumes where it stopped.**
- **Given** a results folder where 40 of the 162 runs are already in `runs.jsonl`.
- **When** the eval is started again on the same folder.
- **Then** only the 122 missing runs are made, and the 40 finished ones are kept
  unchanged.
- **Why:** a full run takes a while and costs money; a crash halfway shouldn't
  mean starting over.

**EV-4: the cost is shown before anything is spent.**
- **Given** the 54 questions and `--repeats 3`.
- **When** the eval starts.
- **Then** it prints the number of runs and an estimate of what they will cost
  (system and judge calls), before making any call.
- **Why:** the person running it should know the price before paying it.

### Measuring in code

**EV-5: a retrieval hit is counted from the expected sources.**
- **Given** `q01`, whose expected source is PMC6226095, page 2.
- **When** the 5 retrieved chunks include a chunk from PMC6226095 (any page).
- **Then** that run has `retrieval_hit: true`; if none of the 5 is from
  PMC6226095, `false`. Questions with no expected source have no value.
- **Why:** this separates "retrieval didn't find it" from "generation didn't use
  it", which need different fixes.

**EV-6: "cites the expected paper" is counted from the source list.**
- **Given** `q01`.
- **When** the answer's source list includes PMC6226095.
- **Then** that run has `cites_expected: true`, otherwise `false`.
- **Why:** an answer can be correct but cite the wrong paper, which a reader
  checking the source would catch.

**EV-7: "not covered" is counted for questions the papers can't answer.**
- **Given** `q51`, off_domain: "What's a good recipe for sourdough bread?", or
  `q19`, out_of_corpus: "How does dopamine loss in the substantia nigra cause
  the motor symptoms of Parkinson's disease?".
- **When** the answer cites nothing.
- **Then** that run has `not_covered: true`; if it cites something, `false`.
- **Why:** until web search (row 7) and declining (row 8) exist, the right
  baseline behaviour for these is to say the papers don't cover them, not to
  answer from general knowledge.

### Judging

**EV-8: correctness is judged against the reference answer.**
- **Given** `q01`'s reference answer, and an answer that says Ythdf1 enhances
  translation of m6A-modified transcripts but doesn't mention the knockout mice.
- **When** the judge compares them.
- **Then** it returns `partial` with one sentence saying what is missing. A
  complete answer gets `correct`; one that contradicts the reference gets `wrong`.
  Questions with no reference answer are not judged for correctness.
- **Why:** correctness is the headline score; "partial" keeps an incomplete but
  true answer from counting as wrong.

**EV-9: faithfulness is judged against the cited chunks, not the reference.**
- **Given** an answer saying "Ythdf1 knockout mice show learning defects [1]",
  where source [1]'s chunk says exactly that.
- **When** the judge checks it.
- **Then** it returns `faithful: true`. If the answer also said "…and the effect
  is reversed by exercise [1]", which no cited chunk says, it returns
  `faithful: false` and quotes that claim. Answers that cite nothing are not
  judged for faithfulness.
- **Why:** a correct-sounding claim that isn't in the cited source is the most
  dangerous failure: it looks checked but isn't.

**EV-10: a judge failure is recorded, and the run is kept.**
- **Given** a judge call that fails (an API error).
- **When** the eval records that run.
- **Then** the run keeps its answer and code measures, and has the judge error
  in place of the verdict; the report counts it as "not judged".
- **Why:** losing a judge verdict must not lose the run.

**EV-11: the judge agrees with a person before its scores are trusted.**
- **Given** 20 runs picked at random from the baseline: their questions,
  reference answers, answers and cited chunks.
- **When** a person grades them by hand (correctness and faithfulness), without
  seeing the judge's verdicts.
- **Then** the judge's verdicts match the person's on at least 16 of the 20
  (80%).
- **Why:** an LLM judge can be lenient or strict in ways nobody notices. v1
  never checked its judge; until this passes, the scores are only a guess.

### Reporting

**EV-12: the report shows each score, overall and by question type.**
- **Given** a finished `runs.jsonl`.
- **When** the report is built.
- **Then** `report.md` has one table with, for all questions and for each
  question type: number of runs, correctness, faithfulness, retrieval hit rate,
  cites-expected rate, not-covered rate, latency p50 and p95, and cost per
  answer. The multilingual questions are reported but left out of the overall
  numbers (the system answers in English only).
- **Why:** an overall number hides where the system fails; v1's report showed
  typo questions failing only because it split scores by type.

**EV-13: two reports can be compared.**
- **Given** the baseline report and a later report (for example after row 6).
- **When** the comparison is built.
- **Then** it shows each score side by side, with the difference.
- **Why:** every later row is kept only if the eval shows it helps; that needs
  a direct comparison, not two reports read by eye.

**EV-14: the eval can run with the reranker, and says so.**
- **Given** the eval runner.
- **When** it is started with `--rerank --name rerank`.
- **Then** every question is retrieved with the reranker (retrieval RT-14),
  and `meta.json` records the system as "baseline + rerank" with the reranker
  model's name, so the report shows which system it measured.
- **Why:** comparing two runs (EV-13) only means something if each run says
  exactly what it ran; a comparison of two unlabeled folders is easy to read
  backwards.

## The corrective system (row 7a)

Row 7a adds grading and rewriting (orchestration spec). The eval runs that
system through the same `Pipeline.ask` the API uses, so the score is the
product's score, and it records which path each answer took.

```
questions.jsonl ──► for each question, 3 times:
                       Pipeline.ask (rerank + grade + rewrite) ──► outcome: answer, path, chunks, query
                       ──► the same code measures and judge as every run ──► + path, total time, every Claude call
                ──► runs.jsonl ──► report.md: the table by type, plus a table by path
```

### How it is built

#### Files

| File | What changes |
|---|---|
| `src/neuro_rag/eval/run.py` | adds `CountingClient`, `run_one_corrective`, `measure`; `run_one`'s measuring and judging move into `measure` unchanged; `system_meta`, `estimate_cost` and `run_eval` get one new keyword each; `main` gets `--corrective` |
| `src/neuro_rag/eval/report.py` | adds `_latency`, `by_path`, `rerouted`; `scores` uses `_latency`; `build_report` adds the path sections when runs have a `path` |
| `src/neuro_rag/orchestration/pipeline.py` | `Outcome` gets two fields, `chunks` and `query` (choice 3; orchestration step 8 and a new OR-9) |
| `tests/test_eval.py` | new tests EV-15 to EV-20 with their own fakes; the existing tests are not changed |
| `tests/test_orchestration.py` | new test OR-9; the existing tests are not changed |

#### `Outcome`, two new fields

```python
@dataclass(frozen=True)
class Outcome:
    answer: Answer
    path: str                 # "papers" | "papers_rewritten" | "none"
    chunks: list = field(default_factory=list)   # the chunks the last grade saw
    query: str | None = None  # the rewritten query, when the second search ran
```

- Path `papers`: `chunks` are the first search's 5 chunks; `query` is `None`
  (the rewrite ran in the background but wasn't used).
- Path `papers_rewritten`: `chunks` are the second search's; `query` is the
  rewritten query.
- Path `none` after two failed grades: the second search's chunks and the
  rewritten query. After a rewrite error or with no rewriter: the first
  search's chunks and `None`.
- Without a grader (row 5's line): the first search's chunks and `None`.

#### `CountingClient`: every Claude call of one run, added up

```python
class CountingClient:
    """Wraps an Anthropic client and adds up every call's tokens (EV-17). One per run."""
    def __init__(self, client):
        self.client, self.lock = client, threading.Lock()
        self.messages = self      # so Generator/Grader/Rewriter can call client.messages.create(...)
        self.calls = self.input_tokens = self.output_tokens = 0

    def create(self, **kwargs):
        response = self.client.messages.create(**kwargs)
        with self.lock:           # grade, rewrite and generate call it from different threads
            self.calls += 1
            self.input_tokens += response.usage.input_tokens
            self.output_tokens += response.usage.output_tokens
        return response
```

A call that raises is not counted (no tokens come back to count).

#### `run_one_corrective(q, repeat, make_pipeline, judge, client) -> dict`

`make_pipeline(client)` returns `Pipeline(retriever, Generator(client), reranker,
Grader(client), Rewriter(client))`, with the retriever and reranker built once
in `main` and shared. Steps:

1. `counter = CountingClient(client)` (`client` is one `anthropic.Anthropic()` made in `main`, shared by all runs); `pipeline = make_pipeline(counter)`.
   A new pipeline per run, so its counter holds only that run's calls.
2. Start the clock. `with Tracer().trace("ask", input=q.question) as trace:`
   `outcome = pipeline.ask(q.question, trace)` (the base `Tracer`: tracing off,
   nothing sent). Stop the clock: `total_s`, rounded to 3 decimals.
3. `pipeline.pool.shutdown(wait=True)`, in a `finally`, so the calls still
   running in the background (a rewrite not needed, a generation thrown away)
   end before the counter is read.
4. If `ask` raised, the record gets `error` as in EV-2 and the run ends here.
5. `measure(record, q, outcome.answer, outcome.chunks, judge)`: exactly the
   measures and judging of a baseline run.
6. Then overwrite the cost fields with the counter's: `claude_calls`,
   `input_tokens`, `output_tokens`, `cost_usd = input × PRICE_IN + output × PRICE_OUT`.
   Add `path`, `query` and `total_s`.

`run_eval(..., run=None)`: when `run` is given, each `(question, repeat)` is
done by `run(question, repeat)` instead of `run_one(question, repeat, retriever,
generator, judge)`, and the estimate is `estimate_cost(questions, repeats,
corrective=True)`. `main` passes `run=partial(run_one_corrective,
make_pipeline=..., judge=judge, client=anthropic.Anthropic())` and `None` for
retriever and generator; it builds the retriever without a reranker (the
pipeline reranks, as in the API) and warms up the encoders and the reranker
first.
Resuming (EV-3), the log line and the file writing are the same.

#### The report

- `_latency(run)`: `total_s` if the run has it, else `retrieval_s + generation_s`.
  `scores` uses it for p50 and p95, so the type table works for both kinds of run.
- `by_path(runs)`: for runs without an error, grouped by path in the order
  `papers`, `papers_rewritten`, `none`: runs, share of all runs, correctness,
  p50, p95, $ per answer. Multilingual runs are left out, as in the overall row.
- `rerouted(runs)`: every run whose `expected_behavior` is judged for
  correctness and whose path is not `papers`, sorted by id then repeat:
  id, repeat, path, the rewritten query, correctness.
- `build_report` adds both, under "## By path" and "## Answerable questions
  not answered on the first search", only when the runs have a `path`.
  A baseline or rerank report gets no new section; the header's latency
  note adds "for the corrective system, the whole question".

#### Worked example: the cost of one rewritten run

`q33`, "front bit vs back bit of the hippocampus, which one does what when you
remember pairs of things?", takes path `papers_rewritten`. Its counter saw 5
calls:

| Call | Input tokens | Output tokens |
|---|---|---|
| grade (first chunks) | 2,900 | 60 |
| rewrite | 450 | 25 |
| generate (first chunks, thrown away) | 3,100 | 380 |
| grade (rewritten query's chunks) | 2,900 | 60 |
| generate (rewritten query's chunks) | 3,100 | 380 |
| **total** | **12,450** | **905** |

`cost_usd` = 12,450 × $0.10/1M + 905 × $0.50/1M = $0.001245 + $0.0004525 =
**$0.0016975**. The baseline counts only the kept generation: 3,100 × $0.10/1M
+ 380 × $0.50/1M = $0.0005. A run on path `papers` counts 3 calls (grade,
rewrite, generate): the rewrite is paid even when it isn't used.

#### Worked example: the estimate (EV-4)

Per corrective run, the estimate assumes the most expensive path (two rounds):
2 generations (3,000 / 400 each), 2 grades (3,000 / 80 each, `EST_GRADE`),
1 rewrite (500 / 40, `EST_REWRITE`) and 2 judge calls (1,500 / 150 each).
Input 15,500 × $0.10/1M = $0.00155; output 1,300 × $0.50/1M = $0.00065;
**$0.0022 per run, $0.36 for 162 runs**. The baseline estimate stays
$0.00095 per run, $0.15 for 162.

### Choices, accepted 2026-10-22

1. **The comparison is with a fresh rerank run, made the same day.** The
   reranker in the service now is the ONNX one with 20 candidates, which was
   never eval'd: 0.75 / 6.4 s was the PyTorch run, and the ONNX run used 10.
   Run `--rerank --name rerank` again, then `--corrective`. The two rerank runs
   (PyTorch and ONNX, the same model) also give a rough measure of how much
   scores move between runs of the same system.
2. **A `--corrective` flag, not a `--system` option.** EV-14's `--rerank` stays
   as it is; `--corrective` always reranks too (decision 005).
3. **`Outcome` carries `chunks` and `query`.** The eval needs the chunks'
   texts for faithfulness and the retrieval hit; the trace's steps hold only
   chunk ids (OB-2), so reading them from a trace isn't enough.
4. **A pipeline and a counter per run, shut down before recording.** The
   point of the parallel design is paying for calls that may be thrown away;
   the cost per question has to include them, or the eval hides the price.
5. **The estimate is the upper bound**, as if every run took two rounds.
6. **4 runs at a time, as in every earlier run.** Each run makes up to 3 Claude
   calls at once, so up to 12 are in flight; latency stays comparable with the
   earlier runs, and is higher than one user alone would see.
7. **The retrieval hit uses `outcome.chunks`,** the chunks the last grade saw,
   so a rewrite that finds the paper counts as a hit.
8. **The row 7a gate** (written in the orchestration validation, not here):
   grading and rewriting go into the service if correctness (excluding
   multilingual) is higher than the same-day rerank run by more than the gap
   between the two rerank runs, the `papers` path's p95 is ≤ 6 s and the
   `papers_rewritten` path's p95 is ≤ 8 s.

### Acceptance criteria

**EV-15: the eval can run the corrective system, and says so.**
- **Given** the eval runner.
- **When** it is started with `--corrective --name corrective`.
- **Then** every question is asked through `Pipeline.ask` with the reranker,
  the grader and the rewriter, and `meta.json` records the system as
  "rerank + grade + rewrite (row 7a)", with the reranker's, grader's and
  rewriter's model names.
- **Why:** a comparison (EV-13) only means something if each folder says
  exactly what it ran.

**EV-16: each run records its path and the rewritten query.**
- **Given** a fake pipeline that answers `q01` on path `papers`, and `q33` on
  path `papers_rewritten` with the query "rostral versus caudal hippocampus
  associative memory encoding retrieval".
- **When** the corrective eval runs them once each.
- **Then** `q01`'s line has `"path": "papers", "query": null`, and `q33`'s
  line has `"path": "papers_rewritten"` and that query.
- **Why:** the path says whether the correction did anything, and the query
  shows what it searched; q30 and q31 were narrowed to one hypothesis in CR-9,
  and only the recorded query shows whether that happened again.

**EV-17: a corrective run's cost counts every Claude call, thrown-away ones included.**
- **Given** `q33` on path `papers_rewritten`, its fake Claude calls reporting
  the tokens in the worked example above (5 calls).
- **When** the corrective eval records it.
- **Then** the line has `claude_calls: 5`, `input_tokens: 12450`,
  `output_tokens: 905` and `cost_usd` 0.0016975; a run on path `papers` has
  `claude_calls: 3`.
- **Why:** running grade, rewrite and generate at once buys speed with calls
  that are sometimes thrown away; a cost counting only the kept answer would
  report the baseline's price for a system that costs three times as much.

**EV-18: a corrective run's latency is the whole question, start to answer.**
- **Given** a fake pipeline whose `ask` takes 0.3 s.
- **When** the corrective eval records it.
- **Then** the line has `total_s` between 0.3 and 0.4, and the report's p50
  and p95 use `total_s`; a baseline run's latency is still `retrieval_s +
  generation_s`.
- **Why:** with steps running at the same time, adding up step times would
  count overlapping time twice; the user waits for the whole `ask`.

**EV-19: "couldn't find" is scored like any other answer.**
- **Given** `q01` (answerable) and `q51` (off_domain), both answered on path
  `none` with "I couldn't find this in the papers." and no sources.
- **When** the corrective eval records them.
- **Then** `q01` is judged for correctness against its reference (a refusal is
  not correct), `cites_expected` is `false`, and it isn't judged for
  faithfulness (it cites nothing); `q51` has `not_covered: true`.
- **Why:** a grader that fails good chunks turns right answers into
  refusals; scoring a refusal as a missing value would hide exactly that cost.

**EV-20: the report shows each path, and the answerable questions that left it.**
- **Given** 6 corrective runs, none multilingual: 4 on `papers` (correctness
  1, 1, 1, 0.5; 2.0, 2.5, 3.0, 3.5 s), 1 on `papers_rewritten` (`q33`, correct,
  5.0 s) and 1 on `none` (`q01`, wrong, 4.0 s).
- **When** the report is built.
- **Then** "By path" has three rows: `papers` 4 runs, 67%, correctness 0.88,
  p95 3.5 s; `papers_rewritten` 1 run, 17%, 1.00, 5.0 s; `none` 1 run, 17%,
  0.00, 4.0 s. "Answerable questions not answered on the first search" lists
  `q01` (`none`) and `q33` (`papers_rewritten`, its query, `correct`).
  The type table is built as for any run.
- **Why:** the row 7a gate is per path (≤ 6 s from the papers, ≤ 8 s after a
  rewrite), and the list is where a wrong refusal or a narrowed rewrite is
  read, run by run.

## Out of scope

- Gates that later rows must pass (each row states its own in its spec).
- Scoring web search and declining (rows 7b and 8 add their measures when
  they exist).
- Writing new questions; human-written questions are a later candidate.
