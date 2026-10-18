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

## Out of scope

- Gates that later rows must pass (each row states its own in its spec).
- Scoring the corrective paths: rewrite, web search, decline (rows 6–8 add
  their measures when they exist).
- Writing new questions; human-written questions are a later candidate.
