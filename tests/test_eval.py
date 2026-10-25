"""Unit tests for specs/eval/spec.md: fake retriever, generator and judge; no API calls."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from types import SimpleNamespace

from neuro_rag.eval.judge import Correctness, Faithfulness, JudgeError
from neuro_rag.eval.report import build_comparison, build_report, scores
from neuro_rag import config
from neuro_rag.eval.run import Question, run_eval, run_one, run_one_corrective, system_meta
from neuro_rag.generation.generate import Answer, Citation, Source, Usage
from neuro_rag.orchestration.pipeline import NOT_FOUND_PAPERS, Outcome
from neuro_rag.retrieval.retrieve import Retrieved

Q01 = Question("q01", "direct", "answer_from_corpus", "How does m6A support memory?", "Ythdf1 enhances translation.",
               frozenset({"PMC6226095"}))
Q51 = Question("q51", "off_domain", "decline", "What's a good recipe for sourdough bread?", None, frozenset())


def chunk(pmcid, text="Ythdf1 knockout mice show learning defects."):
    return Retrieved(f"{pmcid}-p2-c0", text, pmcid, "Title", "Citation", "CC BY", 2, 0.5)


class FakeRetriever:
    def __init__(self, pmcids=("PMC6226095",)):
        self.pmcids = pmcids

    def retrieve(self, question):
        return [chunk(p) for p in self.pmcids]


class FakeGenerator:
    """Cites the first chunk unless `cite` is False; raises for questions in `fail`."""

    def __init__(self, cite=True, fail=()):
        self.cite, self.fail, self.calls = cite, set(fail), 0

    def answer(self, question, chunks):
        self.calls += 1
        if question in self.fail:
            raise RuntimeError("Claude is unavailable")
        if not self.cite:
            return Answer("The provided papers don't cover this.", usage=Usage(1000, 20))
        c = chunks[0]
        return Answer("Ythdf1 knockout mice show learning defects. [1]",
                      [Source(1, c.pmcid, c.title, c.citation, c.page, "url")],
                      [Citation(1, 0, c.text)], Usage(1000, 50))


class FakeJudge:
    def __init__(self, fail=False):
        self.fail = fail

    def correctness(self, question, reference, answer):
        if self.fail:
            raise JudgeError("judge call failed")
        return Correctness("partial", "misses the knockout result")

    def faithfulness(self, answer, cited):
        return Faithfulness(True, "")


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def evaluate(tmp_path, questions, generator=None, judge=None, repeats=3, log=lambda *_: None):
    return run_eval(questions, FakeRetriever(), generator or FakeGenerator(), judge or FakeJudge(),
                    tmp_path / "run", repeats=repeats, workers=2, log=log)


# Running

def test_EV1_every_question_runs_the_requested_number_of_times(tmp_path):
    runs = read(evaluate(tmp_path, [Q01, Q51], repeats=3))

    assert len(runs) == 6
    assert sorted((r["id"], r["repeat"]) for r in runs) == [("q01", 1), ("q01", 2), ("q01", 3),
                                                            ("q51", 1), ("q51", 2), ("q51", 3)]


def test_EV2_failing_run_is_recorded_and_the_eval_continues(tmp_path):
    generator = FakeGenerator(fail={Q01.question})

    runs = read(evaluate(tmp_path, [Q01, Q51], generator, repeats=1))

    failed = next(r for r in runs if r["id"] == "q01")
    assert "Claude is unavailable" in failed["error"]
    assert "answer" not in failed
    assert next(r for r in runs if r["id"] == "q51")["error"] is None


def test_EV3_interrupted_eval_resumes(tmp_path):
    first = read(evaluate(tmp_path, [Q01], repeats=1))
    generator = FakeGenerator()

    runs = read(evaluate(tmp_path, [Q01, Q51], generator, repeats=1))

    assert runs[0] == first[0]  # the finished run is kept unchanged
    assert generator.calls == 1  # only q51 was run
    assert len(runs) == 2


def test_EV4_cost_is_shown_before_any_call(tmp_path):
    generator = FakeGenerator()
    lines = []

    def log(line):
        lines.append((line, generator.calls))

    evaluate(tmp_path, [Q01, Q51], generator, repeats=3, log=log)

    first, calls_before = lines[0]
    assert "6 runs" in first and "$" in first
    assert calls_before == 0


# Measuring in code

def test_EV5_retrieval_hit_from_expected_sources():
    hit = run_one(Q01, 1, FakeRetriever(("PMC6226095",)), FakeGenerator(), FakeJudge())
    miss = run_one(Q01, 1, FakeRetriever(("PMC1",)), FakeGenerator(), FakeJudge())
    none = run_one(Q51, 1, FakeRetriever(), FakeGenerator(cite=False), FakeJudge())

    assert (hit["retrieval_hit"], miss["retrieval_hit"], none["retrieval_hit"]) == (True, False, None)


def test_EV6_cites_expected_from_source_list():
    cites = run_one(Q01, 1, FakeRetriever(("PMC6226095", "PMC1")), FakeGenerator(), FakeJudge())
    other = run_one(Q01, 1, FakeRetriever(("PMC1", "PMC6226095")), FakeGenerator(), FakeJudge())

    assert cites["cites_expected"] is True  # cites the first chunk: PMC6226095
    assert other["cites_expected"] is False  # cites the first chunk: PMC1


def test_EV7_not_covered_when_nothing_is_cited():
    covered = run_one(Q51, 1, FakeRetriever(), FakeGenerator(cite=False), FakeJudge())
    answered = run_one(Q51, 1, FakeRetriever(), FakeGenerator(cite=True), FakeJudge())
    direct = run_one(Q01, 1, FakeRetriever(), FakeGenerator(), FakeJudge())

    assert (covered["not_covered"], answered["not_covered"], direct["not_covered"]) == (True, False, None)


def test_judges_only_where_each_measure_applies():
    """Supports EV-8 and EV-9: correctness only with a reference; faithfulness only when something is cited."""
    q01 = run_one(Q01, 1, FakeRetriever(), FakeGenerator(), FakeJudge())
    q51 = run_one(Q51, 1, FakeRetriever(), FakeGenerator(cite=False), FakeJudge())

    assert (q01["correctness"], q01["faithful"]) == ("partial", True)
    assert (q51["correctness"], q51["faithful"]) == (None, None)


def test_EV10_judge_failure_keeps_the_run():
    run = run_one(Q01, 1, FakeRetriever(), FakeGenerator(), FakeJudge(fail=True))

    assert "judge call failed" in run["judge_error"]
    assert run["answer"].startswith("Ythdf1")
    assert run["retrieval_hit"] is True


# Reporting

def make_run(qid, qtype, correctness=None, faithful=None, hit=None, error=None):
    return {"id": qid, "type": qtype, "repeat": 1, "error": error, "judge_error": None, "correctness": correctness,
            "faithful": faithful, "retrieval_hit": hit, "cites_expected": hit, "not_covered": None,
            "retrieval_s": 0.02, "generation_s": 3.0, "cost_usd": 0.0005}


def test_EV12_report_has_every_score_by_type():
    runs = [make_run("q01", "direct", "correct", True, True), make_run("q02", "direct", "partial", True, False),
            make_run("q30", "typos", "wrong", False, False), make_run("q40", "multilingual_de", "wrong", True, True)]

    report = build_report(runs, {"system": "baseline", "repeats": 1, "workers": 1})

    for column in ["correctness", "faithful", "retrieval hit", "cites expected", "not covered", "p95 s",
                   "$ per answer"]:
        assert column in report
    rows = {line.split("|")[1].strip(): line for line in report.splitlines() if line.startswith("| ")}
    assert set(rows) >= {"all (excl. multilingual)", "direct", "typos", "multilingual_de"}
    assert "| 3 | 0.50 |" in rows["all (excl. multilingual)"]  # 3 runs; (1 + 0.5 + 0) / 3
    assert "| 2 | 0.75 |" in rows["direct"]


def test_EV13_two_reports_compare_side_by_side():
    old = [make_run("q30", "typos", "wrong", True, False)]
    new = [make_run("q30", "typos", "correct", True, True)]

    comparison = build_comparison(new, old, "row6", "baseline")

    line = next(l for l in comparison.splitlines() if l.startswith("| typos | correctness"))
    assert "| 0.00 | 1.00 | +1.00 |" in line


def test_EV14_rerank_run_is_labelled():
    assert system_meta(rerank=True)["system"] == "baseline + rerank"
    assert system_meta(rerank=True)["reranker"] == config.RERANK_MODEL
    assert "reranker" not in system_meta(rerank=False)


# The corrective system (row 7a)

Q33 = Question("q33", "casual_loose_terms", "answer_from_corpus",
               "front bit vs back bit of the hippocampus, which one does what when you remember pairs of things?",
               "Associative memory engages the rostral hippocampus during encoding.", frozenset({"PMC7"}))
REWRITTEN = "rostral versus caudal hippocampus associative memory encoding retrieval"
# the worked example: grade, rewrite, generate (thrown away), grade, generate
Q33_CALLS = [(2900, 60), (450, 25), (3100, 380), (2900, 60), (3100, 380)]
Q01_CALLS = [(2900, 60), (450, 25), (3100, 380)]


class FakeAnthropic:
    """Answers each call with the tokens it is asked to report."""

    def __init__(self):
        self.messages = self

    def create(self, tokens):
        return SimpleNamespace(usage=SimpleNamespace(input_tokens=tokens[0], output_tokens=tokens[1]))


def cited_answer(c):
    return Answer("Ythdf1 knockout mice show learning defects. [1]",
                  [Source(1, c.pmcid, c.title, c.citation, c.page, "url")], [Citation(1, 0, c.text)], Usage(3100, 380))


class FakePipeline:
    """Answers from `plans`: question -> (outcome, Claude calls). The last call runs in the background,
    after ask has returned, like a generation that is thrown away."""

    def __init__(self, client, plans, delay=0.0):
        self.client, self.plans, self.delay = client, plans, delay
        self.pool = ThreadPoolExecutor(max_workers=1)

    def ask(self, question, trace):
        outcome, calls = self.plans[question]
        for tokens in calls[:-1]:
            self.client.messages.create(tokens=tokens)
        self.pool.submit(lambda: (time.sleep(0.1), self.client.messages.create(tokens=calls[-1])))
        time.sleep(self.delay)
        return outcome


def plans():
    q01_chunks, q33_chunks = [chunk("PMC6226095")], [chunk("PMC7")]
    return {Q01.question: (Outcome(cited_answer(q01_chunks[0]), "papers", q01_chunks), Q01_CALLS),
            Q33.question: (Outcome(cited_answer(q33_chunks[0]), "papers_rewritten", q33_chunks, REWRITTEN),
                           Q33_CALLS)}


def corrective(plans, delay=0.0):
    return partial(run_one_corrective, make_pipeline=lambda c: FakePipeline(c, plans, delay), judge=FakeJudge(),
                   client=FakeAnthropic())


def test_EV15_corrective_run_is_labelled():
    meta = system_meta(rerank=False, corrective=True)

    assert meta["system"] == "rerank + grade + rewrite (row 7a)"
    assert meta["reranker"] == config.RERANK_MODEL
    assert meta["grader_model"] == meta["rewriter_model"] == config.LLM_MODEL


def test_EV16_each_run_records_path_and_query(tmp_path):
    path = run_eval([Q01, Q33], None, None, FakeJudge(), tmp_path / "run", repeats=1, workers=2,
                    log=lambda *_: None, run=corrective(plans()))

    runs = {r["id"]: r for r in read(path)}
    assert (runs["q01"]["path"], runs["q01"]["query"]) == ("papers", None)
    assert (runs["q33"]["path"], runs["q33"]["query"]) == ("papers_rewritten", REWRITTEN)


def test_EV17_cost_counts_every_claude_call():
    rewritten = corrective(plans())(Q33, 1)
    first = corrective(plans())(Q01, 1)

    assert (rewritten["claude_calls"], rewritten["input_tokens"], rewritten["output_tokens"]) == (5, 12450, 905)
    assert abs(rewritten["cost_usd"] - 0.0016975) < 1e-12
    assert first["claude_calls"] == 3


def test_EV18_latency_is_the_whole_ask():
    run = corrective(plans(), delay=0.3)(Q01, 1)

    assert 0.3 <= run["total_s"] < 0.4
    assert scores([run])["p95 s"] == run["total_s"]
    assert abs(scores([make_run("q01", "direct")])["p95 s"] - 3.02) < 1e-9  # a baseline run: retrieval + generation


def test_EV19_couldnt_find_is_scored():
    q01_chunks, q51_chunks = [chunk("PMC1")], [chunk("PMC1")]
    refused = {Q01.question: (Outcome(Answer(NOT_FOUND_PAPERS), "none", q01_chunks, REWRITTEN), Q01_CALLS),
               Q51.question: (Outcome(Answer(NOT_FOUND_PAPERS), "none", q51_chunks, "sourdough bread"), Q01_CALLS)}

    q01 = corrective(refused)(Q01, 1)
    q51 = corrective(refused)(Q51, 1)

    assert q01["correctness"] == "partial"  # the fake judge's verdict: the refusal was judged
    assert q01["cites_expected"] is False
    assert q01["faithful"] is None  # cites nothing, so not judged for faithfulness
    assert q51["not_covered"] is True


def corrective_run(qid, path, correctness, total_s, query=None):
    return {"id": qid, "type": "direct", "expected_behavior": "answer_from_corpus", "repeat": 1, "error": None,
            "judge_error": None, "correctness": correctness, "faithful": None, "retrieval_hit": None,
            "cites_expected": None, "not_covered": None, "total_s": total_s, "cost_usd": 0.0017, "path": path,
            "query": query}


def test_EV20_report_by_path():
    runs = [corrective_run("q02", "papers", "correct", 2.0), corrective_run("q03", "papers", "correct", 2.5),
            corrective_run("q04", "papers", "correct", 3.0), corrective_run("q05", "papers", "partial", 3.5),
            corrective_run("q33", "papers_rewritten", "correct", 5.0, REWRITTEN),
            corrective_run("q01", "none", "wrong", 4.0, "m6A methylation memory")]

    report = build_report(runs, {"system": "rerank + grade + rewrite (row 7a)", "repeats": 1, "workers": 1})

    by_path = report.split("## By path")[1].split("## Answerable")[0]
    rows = {line.split("|")[1].strip(): line for line in by_path.splitlines() if line.startswith("| ")}
    assert rows["papers"].startswith("| papers | 4 | 67% | 0.88 | 2.5 | 3.5 |")
    assert rows["papers_rewritten"].startswith("| papers_rewritten | 1 | 17% | 1.00 | 5.0 | 5.0 |")
    assert rows["none"].startswith("| none | 1 | 17% | 0.00 | 4.0 | 4.0 |")
    listed = [line for line in report.split("## Answerable")[1].splitlines() if line.startswith("| q")]
    assert listed == ["| q01 | 1 | none | m6A methylation memory | wrong |",
                      f"| q33 | 1 | papers_rewritten | {REWRITTEN} | correct |"]
    assert "| all (excl. multilingual) | 6 |" in report  # the type table, as for any run
