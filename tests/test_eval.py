"""Unit tests for specs/eval/spec.md: fake retriever, generator and judge; no API calls."""
import json

from neuro_rag.eval.judge import Correctness, Faithfulness, JudgeError
from neuro_rag.eval.report import build_comparison, build_report
from neuro_rag import config
from neuro_rag.eval.run import Question, run_eval, run_one, system_meta
from neuro_rag.generation.generate import Answer, Citation, Source, Usage
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
