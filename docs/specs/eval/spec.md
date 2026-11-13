# Eval and baseline score: spec

Roadmap row 4: rows 1–3 have a measured score on the 50 English questions.

## Goal

Run every eval question through the system as it is (search, then cited
answer), measure each answer in code and with an LLM judge, and write one
report. That report is the **baseline**: every later row (API, deployment,
better search, "not in the papers"…) is kept only if it does at least as well.

## In and out

- **In:** `eval/questions.jsonl` (54 questions, v2's, unchanged; the 4
  non-English ones are skipped, so 50 are run), the `papers`
  collection, and the API key in `.env`.
- **Out:** a folder `eval/results/<YYYY-MM-DD_HHMM>_<name>/` with
  - `runs.jsonl`: one line per question per repeat, with everything measured;
  - `report.md`: the scores, overall and by question type, and every answer
    the judge didn't grade "correct", with its reason.
- **Runs:**
  ```
  docker compose up -d                       # Qdrant
  python -m neuro_rag.eval.run --name baseline
  ```

```
questions.jsonl ──► for each question, once (--repeats N):
                       search (top 5) ──► answer (Haiku 4.5) ──► measure in code ──► judge (Haiku 4.5)
                ──► runs.jsonl (a line written after each run) ──► report.md
```

## The question set

54 questions in the file, each with `id`, `type`, `expected_behavior`, `question`,
`reference_answer` (may be empty) and `expected_sources` (pmcid and page, may be
empty). What each kind of question is measured on:

| Questions | How many | Example | Measured |
|---|---|---|---|
| answered from the papers, English (`answer_from_corpus` and `correct_premise`, not multilingual) | 36 | q01 "How does m6A RNA methylation support hippocampus-dependent learning and memory?" | search hits, cites expected paper, **correctness**, faithfulness |
| non-English (`type` starts with `multilingual_`) | 4 | a German, French, Spanish and Arabic question | **not run**: the product answers in English only (roadmap choice 2), and the English embedding model can't search them; a question rewriter (row 9) may bring them back |
| should be declined or answered from the web (`decline`, `web_fallback`) | 8 | q51 "What's a good recipe for sourdough bread?", q19 "How does dopamine loss in the substantia nigra cause the motor symptoms of Parkinson's disease?" | **not covered**: the answer cites nothing |
| borderline (`not_declined`) | 6 | q45 "Does caffeine help you remember what you studied?" | reported only: how often the answer cites the papers |

Known limit, kept from v2: the questions were drafted by Claude from paper
abstracts, so they share wording with the text they retrieve; real users'
questions are harder.

## What is measured

| Measure | For which runs | How |
|---|---|---|
| `paper_hit`, `page_hit` | questions with expected sources | code: any of the 5 hits has an expected pmcid / an expected (pmcid, page), as in row 2's comparison |
| `cites_expected` | questions with expected sources | code: an expected pmcid is in the answer's source list |
| `correctness` | the 36 answered-from-papers questions | judge: `correct` (1), `partial` (0.5) or `wrong` (0) against the reference answer |
| `faithful` | runs whose answer has at least one source | judge: every claim is in the text of the chunks it cites |
| `not_covered` | `decline` and `web_fallback` questions | code: the answer has no sources |
| `cites_papers` | borderline questions | code: the answer has at least one source |
| `search_s`, `answer_s` | all | code: wall-clock seconds for `search` and for `answer` |
| `cost_usd` | all | code: answer and judge tokens at Haiku 4.5's price |

## Settings

| Setting | Value | Why |
|---|---|---|
| repeats | 1 (default; `--repeats 3` when a close comparison needs the spread) | 3 repeats cost $0.75 a run of the eval, too much to run often; 1 repeat costs $0.25 |
| system | `search` dense top 5 (row 2), then `answer` (row 3) | the baseline, nothing else |
| judge model | `claude-haiku-4-5` through `ChatAnthropic` | the project's model for every LangChain call |
| judge output | `llm.with_structured_output(<pydantic model>)` | the verdict always parses into fixed fields |
| order | one run at a time, in question order | simple; 50 runs at about 5 s each is about 4 minutes |
| price | `PRICE_IN = 1.00`, `PRICE_OUT = 5.00` dollars per million tokens, in `config.py` | Haiku 4.5's price |
| cost estimate | $0.005 per run | answer ≈ $0.0032 (2,293 in, 179 out, measured on q01) plus two judge calls ≈ $0.0018 |

## How it is built

### Files

| File | Contents |
|---|---|
| `src/neuro_rag/config.py` | adds `PRICE_IN = 1.00`, `PRICE_OUT = 5.00`, `QUESTIONS_PATH = ROOT / "eval" / "questions.jsonl"`, `RESULTS_DIR = ROOT / "eval" / "results"` |
| `src/neuro_rag/eval/__init__.py` | empty |
| `src/neuro_rag/eval/judge.py` | `Correctness`, `Faithfulness`, `CORRECTNESS_PROMPT`, `FAITHFULNESS_PROMPT`, `judge_correctness`, `judge_faithfulness` |
| `src/neuro_rag/eval/run.py` | `load_questions`, `measure`, `cost`, `run_one`, `run_eval`, `main` |
| `src/neuro_rag/eval/report.py` | `build_report` |
| `tests/test_eval.py` | unit tests with fake search, answer and judge: no API call, no Qdrant |
| `tests/test_eval_llm.py` | the two judges against the real API, marked `llm` |

### `eval/judge.py`

```python
class Correctness(BaseModel):
    verdict: Literal["correct", "partial", "wrong"]
    reason: str                     # one sentence

class Faithfulness(BaseModel):
    faithful: bool
    unsupported_claim: str          # "" when faithful, else the first unsupported claim, quoted

def judge_correctness(question: str, reference: str, answer_text: str, llm) -> tuple[Correctness, int, int]
def judge_faithfulness(result: Answer, hits: list[Hit], llm) -> tuple[Faithfulness, int, int]
                                    # each returns the verdict, input tokens, output tokens
```

`llm` is `make_llm()` from row 3. Each judge calls
`llm.with_structured_output(<model>, include_raw=True).invoke([SystemMessage(prompt), HumanMessage(text)])`;
the verdict is `out["parsed"]` and the tokens are
`out["raw"].usage_metadata["input_tokens"]` and `["output_tokens"]`.
If `out["parsed"]` is `None` (the reply failed the schema check), the judge
raises `ValueError(f"judge reply didn't parse: {out['parsing_error']}")`, so
`run_one` records it as that judge's error (EV-9) instead of a silent `None`.

**`CORRECTNESS_PROMPT`, word for word:**
```
You grade an answer to a neuroscience question against a reference answer written by an expert.

- correct: the answer states the reference's main findings and contradicts none of them. Different wording and extra true detail are fine.
- partial: the answer states some of the reference's main findings and contradicts none, but misses at least one.
- wrong: the answer contradicts the reference, answers a different question, or says the papers don't cover it.

Judge the content only, not the style or the citations. Give the verdict and one sentence saying why.
```
The human message: `f"Question: {question}\n\nReference answer: {reference}\n\nAnswer to grade: {answer_text}"`.

**`FAITHFULNESS_PROMPT`, word for word:**
```
You check whether an answer is supported by the sources it cites. The sources are numbered as in the answer.

- faithful: every claim in the answer is stated in, or follows directly from, the text of a source it cites.
- unfaithful: at least one claim is not in the sources it cites. Quote the first such claim.

Use only the source texts given, not your own knowledge.
```
The human message: `f"Answer: {result.text}\n\nSources:\n{sources}"`, where
`sources` has one line per source number `n`:
`f"[{n}] {texts}"`, and `texts` is the text of every hit cited under that
number (from `result.citations`, by `hit_index`, each hit once, in hit order),
joined with `" … "`.

### `eval/run.py`

```python
def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]     # every line except types starting with "multilingual_"
def measure(question: dict, hits: list[Hit], result: Answer) -> dict      # the code measures
def cost(input_tokens: int, output_tokens: int) -> float                   # dollars
def run_one(question: dict, repeat: int, search_fn, answer_fn, llm) -> dict
def run_eval(questions: list[dict], repeats: int, out_dir: Path, search_fn, answer_fn, llm) -> list[dict]
def main()      # python -m neuro_rag.eval.run --name <name> [--repeats N]
```

`search_fn(question) -> list[Hit]` and `answer_fn(question, hits) -> Answer`
are passed in so the unit tests can use fakes; `main` builds the real ones
from row 2's `search` and row 3's `answer`.

**`measure` rules** (each key is present only for the runs it applies to,
otherwise `None`):
- `paper_hit`, `page_hit`, `cites_expected`: only when `expected_sources` isn't
  empty.
- `not_covered = len(result.sources) == 0`: only when `expected_behavior` is
  `decline` or `web_fallback`.
- `cites_papers = len(result.sources) > 0`: only when `expected_behavior` is
  `not_declined`.

**`cost`:** `(input_tokens * PRICE_IN + output_tokens * PRICE_OUT) / 1_000_000`.
For q01's answer, `cost(2293, 179)` = 0.003188.

**`run_one` steps:**
1. `t0`; `hits = search_fn(q["question"])`; `t1`; `result = answer_fn(q["question"], hits)`; `t2`.
2. `record` = `id`, `type`, `expected_behavior`, `repeat`, `question`,
   `chunk_ids` (the 5 hits' IDs), `answer` (`result.text`), `sources` (a list
   of `{"n", "pmcid", "page"}`), the `measure` keys, `search_s = t1 - t0`,
   `answer_s = t2 - t1`, rounded to 2 decimals.
3. **Correctness** is judged when `expected_behavior` is `answer_from_corpus`
   or `correct_premise` and `reference_answer` isn't empty:
   `record["correctness"] = {"verdict", "reason"}`; otherwise `None`.
4. **Faithfulness** is judged when the answer has at least one source:
   `record["faithfulness"] = {"faithful", "unsupported_claim"}`; otherwise `None`.
5. A judge call that raises → that judge's value is `{"error": str(e)}`; the
   run keeps everything else.
6. `record["cost_usd"]` = `cost` of the answer's tokens plus every judge's
   tokens, rounded to 6 decimals; `record["error"] = None`.

**`run_eval` steps:**
1. Print `f"{len(questions) * repeats} runs, estimated ${len(questions) * repeats * 0.005:.2f}"`
   before any call. For the 50 questions and 1 repeat: `50 runs, estimated $0.25`.
2. For each question in file order, for `repeat` in 1…`repeats`: `run_one`.
   If `search_fn` or `answer_fn` raises, the record is `id`, `type`,
   `expected_behavior`, `repeat`, `question` and `error = str(e)`, with every
   other key `None`. Each record is appended to `out_dir/runs.jsonl` as one
   JSON line as soon as it is made.
3. Print one progress line per run: `f"{n}/{total} {id} r{repeat}"`, plus
   `" error"` when it failed.
4. Return the records.

**`main` steps:**
1. Arguments: `--name` (required), `--repeats` (default 1).
2. `out_dir = RESULTS_DIR / f"{now:%Y-%m-%d_%H%M}_{name}"`, created; it must
   not exist yet.
3. Build `search_fn` with the real Qdrant client and embedders (dense, top 5),
   `llm = make_llm()`, `answer_fn = lambda q, h: answer(q, h, llm)`.
4. `run_eval(load_questions(), repeats, out_dir, search_fn, answer_fn, llm)`.
5. Write `out_dir/report.md` = `build_report(records, name)`, and print its
   path.

### `eval/report.py`

```python
def build_report(records: list[dict], name: str) -> str
```

1. **Header:** `# Eval report: {name}`, then one line: the number of runs, how
   many failed (`error` not `None`), how many judge calls failed, and the
   total cost.
2. **Table**, one row per group: first `all`, then one row
   per `type`, sorted by name. Columns:

   | questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |

   - each rate is the mean over the runs in the group where that value isn't
     `None` (and isn't a judge error), shown with 2 decimals; `–` when no run
     in the group has the value;
   - `correctness`: correct 1, partial 0.5, wrong 0;
   - `p50 s`, `p95 s`: percentiles of `search_s + answer_s`, nearest-rank
     (`sorted(v)[ceil(p/100 * len(v)) - 1]`), 1 decimal;
   - failed runs count in `runs` and in nothing else.
   - `$ per run`: the mean `cost_usd`, 4 decimals (a run costs well under a cent).
3. **Not correct:** one line per run whose verdict is `partial` or `wrong`,
   in question order: `f"- {id} r{repeat} {verdict}: {reason}"`.
4. **Unfaithful:** one line per run judged unfaithful:
   `f"- {id} r{repeat}: \"{unsupported_claim}\""`.

Sections 3 and 4 are there so the judge can be checked by reading its
reasons; v2 never managed to grade the judge by hand (EV-11 was skipped).

**Worked example of the table** (two runs of q01 and one of q51; numbers
illustrative):

| run | type | correctness | faithful | paper_hit | page_hit | cites_expected | not_covered | seconds |
|---|---|---|---|---|---|---|---|---|
| q01 r1 | direct | partial | true | true | false | true | – | 3.0 |
| q01 r2 | direct | correct | true | true | false | true | – | 4.0 |
| q51 r1 | off_domain | – | – | – | – | – | true | 1.0 |

gives, for `all`: runs 3, correctness 0.75, faithful
1.00, paper@5 1.00, page@5 0.00, cites expected 1.00, not covered 1.00, cites
papers –, p50 3.0, p95 4.0.

## Choices, accepted 2026-11-09

1. **1 repeat per question by default** (accepted 2026-11-09): 3 repeats
   (v2's) cost $0.75 a run. The model doesn't answer the same way each time,
   so when two systems differ by a question or two, rerun both with
   `--repeats 3` before keeping either.
2. **Haiku 4.5 judges its own answers.** Cheap and consistent; the risk is a
   lenient judge. The report lists every non-correct and unfaithful verdict
   with its reason, so the judge can be checked by reading.
3. **No hand-graded agreement check** (v2's EV-11), which was skipped in v2 as
   beyond reach; reading the reasons replaces it for now.
4. **Faithfulness is judged as well as correctness:** a correct-sounding claim
   that isn't in its cited chunk is the most dangerous failure. It doubles the
   judge calls (+ $0.0009 a run).
5. **Questions run one at a time, with no resume.** About 4 minutes and $0.25;
   a crash means rerunning into a new folder.
6. **Only the baseline is run here.** Comparing two reports is added when the
   first improvement (row 8) needs it.
7. **The results folder is committed** with the report, so every number can
   be checked against the runs behind it.

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own.
How each one is checked is in [validation.md](validation.md).

### Running (fakes, no API call)

**EV-1: every question is run the requested number of times.**
- **Given** three questions, q01, q19 and q51, a fake `search_fn`, `answer_fn`
  and judge, and `repeats=2`.
- **When** `run_eval` runs into a temporary folder.
- **Then** `runs.jsonl` has 6 lines, in the order q01 r1, q01 r2, q19 r1,
  q19 r2, q51 r1, q51 r2.
- **Why:** a missing run would make one question count less than the others
  without anyone noticing.

**EV-2: a failing run is recorded, and the eval continues.**
- **Given** the same three questions, `repeats=1`, and an `answer_fn` that
  raises `RuntimeError("Claude unavailable")` for q19 only.
- **When** `run_eval` runs.
- **Then** `runs.jsonl` has 3 lines; q19's has `error` "Claude unavailable"
  and `answer` `None`; q01's and q51's have `error` `None` and an answer.
- **Why:** one failure in 50 runs must not throw away the other 49.

**EV-3: the cost estimate is printed before any call.**
- **Given** the questions from `load_questions()`, `repeats=1`, and fakes that count their calls.
- **When** `run_eval` starts.
- **Then** the first line printed is "50 runs, estimated $0.25", and when it
  was printed no fake had been called.
- **Why:** the person running it should know the price before paying it.

### Measuring in code

**EV-4: search hits are counted from the expected sources.**
- **Given** q01 (expected source PMC6226095 page 2) and hits whose first is
  `PMC6226095-p6-c1` and none from page 2 (the real dense top 5 from row 2).
- **When** `measure` runs.
- **Then** `paper_hit` is true and `page_hit` is false.
- **Why:** this separates "search found the paper but not the page" from
  "search missed the paper", which need different fixes.

**EV-5: "cites expected" is counted from the answer's sources.**
- **Given** q01, and an answer whose only source is PMC6226095 page 6.
- **When** `measure` runs.
- **Then** `cites_expected` is true. With the only source PMC11319347 page 1,
  it is false.
- **Why:** an answer can read well but cite the wrong paper, which a reader
  checking the source would catch.

**EV-6: "not covered" is counted for questions the papers can't answer.**
- **Given** q51 ("What's a good recipe for sourdough bread?", `decline`).
- **When** `measure` runs on an answer with no sources.
- **Then** `not_covered` is true, and `paper_hit`, `page_hit`,
  `cites_expected` and `cites_papers` are `None`. With one source,
  `not_covered` is false.
- **Why:** until declining (row 12) and web search (row 11) exist, the right
  baseline behaviour is to say the papers don't cover it.

**EV-7: only the answered-from-papers questions are judged for correctness.**
- **Given** q01 (`answer_from_corpus`, with a reference), q19
  (`web_fallback`, with a reference) and q45 (`not_declined`, no reference),
  each with an answer that has one source, and a fake judge that counts its
  calls.
- **When** `run_one` runs on each.
- **Then** q01 gets a `correctness` verdict; q19 and q45 get `correctness`
  `None`; all three get a `faithfulness` verdict (each has a source).
- **Why:** q19's "reference" describes the expected path ("Not covered by the
  hippocampus corpus…"), not a fact; grading against it would be meaningless.

**EV-8: the cost of a run is its tokens at Haiku 4.5's price.**
- **Given** an answer with 2,293 input and 179 output tokens, and two judge
  calls with 600 / 40 and 800 / 30 tokens.
- **When** `run_one` records the run.
- **Then** `cost_usd` is 0.004938 (0.003188 + 0.0008 + 0.00095).
- **Why:** cost per request is a roadmap target; it must come from measured
  tokens, not guesses.

**EV-9: a judge failure is recorded, and the run is kept.**
- **Given** q01 and a correctness judge that raises `RuntimeError("timeout")`.
- **When** `run_one` runs.
- **Then** the record has `correctness` `{"error": "timeout"}`, its answer,
  hits and code measures, and `error` `None`.
- **And** with a judge whose reply fails the schema check (`parsed` `None`,
  `parsing_error` "bad JSON"), `correctness` is
  `{"error": "judge reply didn't parse: bad JSON"}` and the run is kept the same way.
- **Why:** losing a judge verdict must not lose the run.

### Judging (real Haiku 4.5, marked `llm`)

The reference answer used below is q01's: "The m6A reader Ythdf1 enhances
translation of m6A-modified transcripts in a neuronal-stimulus-dependent way
in the adult mouse hippocampus. Ythdf1-knockout mice show learning and memory
defects plus impaired hippocampal synaptic transmission and LTP; re-expressing
Ythdf1 in the hippocampus rescues these, and acute hippocampal knockdown of
Ythdf1 or Mettl3 (the m6A methyltransferase) recapitulates the deficits."

**EV-10: the correctness judge tells correct, partial and wrong apart.**
- **Given** q01's question and reference, and three answers:
  - "Ythdf1, which reads m6A marks, boosts translation of m6A-marked mRNAs
    after neuronal stimulation in the adult hippocampus. Mice lacking Ythdf1
    learn and remember worse and have impaired synaptic transmission and LTP;
    putting Ythdf1 back in the hippocampus rescues this, and knocking down
    Ythdf1 or Mettl3 there causes the same deficits.";
  - "Ythdf1 boosts translation of m6A-marked mRNAs after neuronal
    stimulation.";
  - "m6A methylation blocks translation in the hippocampus, and mice without
    Ythdf1 learn faster."
- **When** `judge_correctness` runs on each.
- **Then** the verdicts are `correct`, `partial` and `wrong`, each with a
  non-empty reason.
- **Why:** correctness is the headline score; a judge that can't tell these
  three apart makes it meaningless.

**EV-11: the faithfulness judge catches a claim its source doesn't make.**
- **Given** one hit, PMC6226095 page 6, text "Depletion of Ythdf1 impairs
  basal transmission and LTP of hippocampal synapses.", and two answers citing
  it as [1]:
  - "Depleting Ythdf1 impairs basal transmission and LTP at hippocampal
    synapses [1].";
  - "Depleting Ythdf1 impairs LTP at hippocampal synapses, and exercise
    reverses this [1]."
- **When** `judge_faithfulness` runs on each.
- **Then** the first is faithful with `unsupported_claim` ""; the second is
  unfaithful and its `unsupported_claim` contains "exercise".
- **Why:** a claim that looks cited but isn't in the source is the failure a
  reader is least likely to catch.

### Reporting

**EV-12: the report shows each score overall and by type.**
- **Given** the three records of the worked example.
- **When** `build_report` runs.
- **Then** the `all` row shows runs 3, correctness 0.75 and p95 4.0; the
  `direct` row shows runs 2 and correctness 0.75; the `off_domain` row shows
  not covered 1.00 and `–` for correctness.
- **Why:** an overall number hides where the system fails; v2's report showed
  `casual_loose_terms` at 0.12 only because it split scores by type.

**EV-13: the report lists every answer not graded correct, with the judge's reason.**
- **Given** the records of EV-12, where q01 r1 is `partial` with reason "Misses
  the rescue and knockdown results."
- **When** `build_report` runs.
- **Then** the "Not correct" section contains the line
  "- q01 r1 partial: Misses the rescue and knockdown results." and no line
  for q01 r2 or q51 r1.
- **Why:** reading the reasons is how the judge gets checked, and how the
  next row finds what to fix.

### The baseline

**EV-14: the full baseline runs and is recorded.**
- **Given** the `papers` collection, the 50 English questions and the API key.
- **When** `python -m neuro_rag.eval.run --name baseline` runs.
- **Then** it prints "50 runs, estimated $0.25", writes 50 lines to
  `runs.jsonl` and a `report.md`, and its `all` row is
  copied into validation.md as the baseline.
- **Why:** this number is what every later row has to beat.

## Out of scope

- Comparing two reports (added with row 8's first improvement).
- Resuming an interrupted run; running questions in parallel.
- A hand-graded check of the judge.
- Measuring the API or the deployed service (rows 5 and 7 rerun this eval
  against them).
- Scoring declining, web answers and "not in the papers" (rows 10–12).
