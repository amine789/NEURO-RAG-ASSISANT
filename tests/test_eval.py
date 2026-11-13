import json
from types import SimpleNamespace

import pytest

from neuro_rag.eval.judge import Correctness, Faithfulness
from neuro_rag.eval.report import COLUMNS, build_report
from neuro_rag.eval.run import load_questions, measure, run_eval, run_one
from neuro_rag.generation.answer import Answer, Citation, Source
from neuro_rag.retrieval.search import Hit

HIT = Hit("PMC1-p3-c0", "PMC1", 3, "Title 1", "Citation 1", "CC BY", "Place cells fire at one location.", 0.9)


def fake_search(question):
    """Stands in for search: the same single hit for every question, no Qdrant."""
    return [HIT]


def fake_answer(question, hits):
    """Stands in for answer: a fixed answer citing the hit, no API call."""
    return Answer(
        text="Place cells fire at one location [1].",
        sources=[Source(1, "PMC1", 3, "Title 1", "Citation 1", "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/")],
        citations=[Citation(1, 0, "Place cells fire at one location.")],
        input_tokens=1000,
        output_tokens=100,
    )


class FakeJudgeLLM:
    """Stands in for ChatAnthropic in the judges: every verdict is correct / faithful.
    tokens: (input, output) per judge model; 200 in and 30 out unless given."""

    def __init__(self, tokens=None):
        self.calls = 0
        self.tokens = tokens or {}

    def with_structured_output(self, model, include_raw=True):
        verdict = Correctness(verdict="correct", reason="Matches the reference.") if model is Correctness \
            else Faithfulness(faithful=True, unsupported_claim="")
        input_tokens, output_tokens = self.tokens.get(model, (200, 30))
        return SimpleNamespace(invoke=lambda messages: self._reply(verdict, input_tokens, output_tokens))

    def _reply(self, verdict, input_tokens, output_tokens):
        self.calls += 1
        raw = SimpleNamespace(usage_metadata={"input_tokens": input_tokens, "output_tokens": output_tokens})
        return {"parsed": verdict, "raw": raw, "parsing_error": None}


def test_EV1_every_question_run_repeats_times(tmp_path):
    questions = [q for q in load_questions() if q["id"] in ("q01", "q19", "q51")]

    run_eval(questions, 2, tmp_path, fake_search, fake_answer, FakeJudgeLLM())

    lines = [json.loads(line) for line in (tmp_path / "runs.jsonl").read_text().splitlines()]
    assert [(r["id"], r["repeat"]) for r in lines] == [
        ("q01", 1), ("q01", 2), ("q19", 1), ("q19", 2), ("q51", 1), ("q51", 2),
    ]


def test_EV2_failing_run_recorded_and_eval_continues(tmp_path):
    questions = [q for q in load_questions() if q["id"] in ("q01", "q19", "q51")]

    def failing_answer(question, hits):
        if "Parkinson" in question:  # q19 only
            raise RuntimeError("Claude unavailable")
        return fake_answer(question, hits)

    run_eval(questions, 1, tmp_path, fake_search, failing_answer, FakeJudgeLLM())

    lines = {r["id"]: r for r in map(json.loads, (tmp_path / "runs.jsonl").read_text().splitlines())}
    assert len(lines) == 3
    assert lines["q19"]["error"] == "Claude unavailable"
    assert lines["q19"]["answer"] is None
    for id_ in ("q01", "q51"):
        assert lines[id_]["error"] is None
        assert lines[id_]["answer"]


def test_EV3_cost_estimate_printed_before_any_call(tmp_path, capsys):
    printed_before_first_call = []

    def watching_search(question):
        if not printed_before_first_call:  # first call: grab everything printed so far
            printed_before_first_call.append(capsys.readouterr().out)
        return fake_search(question)

    run_eval(load_questions(), 1, tmp_path, watching_search, fake_answer, FakeJudgeLLM())

    assert printed_before_first_call == ["50 runs, estimated $0.25\n"]


def hit_from_id(chunk_id):
    """A Hit built from a chunk ID like 'PMC6226095-p6-c1': only pmcid and page matter here."""
    pmcid, page, _ = chunk_id.split("-")
    return Hit(chunk_id, pmcid, int(page[1:]), "Title", "Citation", "CC BY", "text", 0.5)


def question(id_):
    return next(q for q in load_questions() if q["id"] == id_)


# q01's real dense top 5 from row 2 (eval/results/search_compare_2026-11-04.csv)
Q01_HITS = [hit_from_id(c) for c in (
    "PMC6226095-p6-c1", "PMC11319347-p1-c0", "PMC13144532-p3-c4", "PMC11319347-p9-c5", "PMC11319347-p1-c3",
)]


def test_EV4_search_hits_from_expected_sources():
    m = measure(question("q01"), Q01_HITS, fake_answer("", Q01_HITS))

    assert m["paper_hit"] is True
    assert m["page_hit"] is False

def answer_citation(pmcid, page):
       return Answer("text [1].", [Source(1, pmcid, page, "Title", "Citation", "url")], [], 0, 0)

def test_EV5_cites_expected_from_answer_sources():
    m = measure(question("q01"), Q01_HITS, answer_citation("PMC6226095", 2))

    assert m["cites_expected"] is True
    m = measure(question("q01"), Q01_HITS, answer_citation("PMC11319347", 6))
    
    assert m["cites_expected"] is False


def test_EV6_not_covered_for_decline_questions():
    no_sources = Answer("The provided papers don't cover this.", [], [], 0, 0)

    m = measure(question("q51"), [HIT], no_sources)

    assert m["not_covered"] is True
    for key in ("paper_hit", "page_hit", "cites_expected", "cites_papers"):
        assert m[key] is None

    m = measure(question("q51"), [HIT], answer_citation("PMC1", 3))

    assert m["not_covered"] is False


def test_EV7_only_answered_questions_judged_for_correctness():
    records= {}
    for id_ in ("q01", "q19", "q45"):
        records[id_] = run_one(question(id_), 1, fake_search, fake_answer, FakeJudgeLLM())

    assert records["q01"]["correctness"] == {"verdict": "correct", "reason": "Matches the reference."}
    assert records["q19"]["correctness"] is None
    assert records["q45"]["correctness"] is None


    assert records["q01"]["faithfulness"] == {"faithful": True, "unsupported_claim": ""}
    assert records["q19"]["faithfulness"] == {"faithful": True, "unsupported_claim": ""}
    assert records["q45"]["faithfulness"] == {"faithful": True, "unsupported_claim": ""}


def test_EV8_cost_from_tokens():
    def answer_with_tokens(question, hits):
        return Answer("Place cells fire at one location [1].",
                      [Source(1, "PMC1", 3, "Title 1", "Citation 1", "url")],
                      [Citation(1, 0, "Place cells fire at one location.")], 2293, 179)

    llm = FakeJudgeLLM(tokens={Correctness: (600, 40), Faithfulness: (800, 30)})

    record = run_one(question("q01"), 1, fake_search, answer_with_tokens, llm)

    assert record["cost_usd"] == 0.004938  # 0.003188 answer + 0.0008 correctness + 0.00095 faithfulness
    


class CrashingJudgeLLM:
    """A judge whose call raises, like a timeout."""

    def with_structured_output(self, model, include_raw=True):
        def invoke(messages):
            raise RuntimeError("timeout")
        return SimpleNamespace(invoke=invoke)


class UnparsableJudgeLLM:
    """A judge whose reply fails the schema check: parsed is None."""

    def with_structured_output(self, model, include_raw=True):
        raw = SimpleNamespace(usage_metadata={"input_tokens": 200, "output_tokens": 30})
        return SimpleNamespace(invoke=lambda messages: {"parsed": None, "raw": raw, "parsing_error": "bad JSON"})


@pytest.mark.parametrize("judge_llm, message", [
    (CrashingJudgeLLM(), "timeout"),
    (UnparsableJudgeLLM(), "judge reply didn't parse: bad JSON"),
])
def test_EV9_judge_failure_recorded_run_kept(judge_llm, message):
    record = run_one(question("q01"), 1, fake_search, fake_answer, judge_llm)

    assert record["correctness"] == {"error": message}
    assert record["answer"] == "Place cells fire at one location [1]."
    assert record["chunk_ids"] == ["PMC1-p3-c0"]
    assert record["paper_hit"] is not None
    assert record["error"] is None


def record(id_, type_, repeat, correctness, search_s, answer_s, **measures):
    """A runs.jsonl record with only what the report reads; measures default to None."""
    keys = ("paper_hit", "page_hit", "cites_expected", "not_covered", "cites_papers")
    return {
        "id": id_, "type": type_, "repeat": repeat, "error": None,
        "correctness": correctness,
        "faithfulness": {"faithful": True, "unsupported_claim": ""} if correctness else None,
        "search_s": search_s, "answer_s": answer_s, "cost_usd": 0.005,
        **{k: measures.get(k) for k in keys},
    }


# the spec's worked example: two runs of q01, one of q51
WORKED = [
    record("q01", "direct", 1, {"verdict": "partial", "reason": "Misses the rescue and knockdown results."},
           1.0, 2.0, paper_hit=True, page_hit=False, cites_expected=True),
    record("q01", "direct", 2, {"verdict": "correct", "reason": "Matches the reference."},
           1.0, 3.0, paper_hit=True, page_hit=False, cites_expected=True),
    record("q51", "off_domain", 1, None, 0.5, 0.5, not_covered=True),
]


def table_row(report, group):
    """The report's table row for one group, as {column: cell}."""
    line = next(line for line in report.splitlines() if line.startswith(f"| {group} |"))
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    return dict(zip(COLUMNS, cells))


def test_EV12_report_overall_and_by_type():
    report = build_report(WORKED, "test")

    all_ = table_row(report, "all")
    assert all_["runs"] == "3"
    assert all_["correctness"] == "0.75"
    assert all_["p95 s"] == "4.0"

    direct = table_row(report, "direct")
    assert direct["runs"] == "2"
    assert direct["correctness"] == "0.75"

    off_domain = table_row(report, "off_domain")
    assert off_domain["not covered"] == "1.00"
    assert off_domain["correctness"] == "–"


def test_EV13_report_lists_not_correct_with_reasons():
    report = build_report(WORKED, "test")

    not_correct = report.split("## Not correct")[1].split("## Unfaithful")[0]
    lines = [line for line in not_correct.splitlines() if line.startswith("- ")]

    assert lines == ["- q01 r1 partial: Misses the rescue and knockdown results."]
