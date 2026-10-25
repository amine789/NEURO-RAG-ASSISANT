"""Unit tests for specs/orchestration/spec.md: fakes for every step and the recording tracer; free."""
import time

from neuro_rag.correction.rewrite import RewriteError
from neuro_rag.generation.generate import Answer, Usage
from neuro_rag.grading.grade import Grade, GradingError
from neuro_rag.orchestration.pipeline import NOT_FOUND_PAPERS, Pipeline
from neuro_rag.retrieval.retrieve import Retrieved
from pipeline_fakes import RecordingTracer

FEAR = ("How do the fear center and the memory center keep their rhythms in step "
        "when people form unpleasant memories?")
QUERY = "amygdala hippocampus theta phase synchrony aversive memory"


class QueryRetriever:
    """Returns chunks named after the query it was given; records the queries."""

    def __init__(self):
        self.queries = []

    def retrieve(self, query, k=5):
        self.queries.append(query)
        return [Retrieved(f"c{n}", f"{query} | chunk {n}", "PMC1", "Title", "Citation", "CC BY", 1, 0.0)
                for n in range(k)]


class RecordingReranker:
    """Keeps the order; records the query it scored against."""

    def __init__(self):
        self.queries = []

    def score(self, query, texts):
        self.queries.append(query)
        return [float(len(texts) - i) for i in range(len(texts))]


class FakeGrader:
    """Returns the given grades in order (True passes, False fails, an exception is raised)."""

    def __init__(self, *grades, delay=0.0):
        self.grades, self.delay, self.calls = list(grades), delay, []

    def grade(self, question, chunks):
        self.calls.append((question, [c.text for c in chunks]))
        time.sleep(self.delay)
        g = self.grades.pop(0)
        if isinstance(g, Exception):
            raise g
        return Grade(passed=g, relevant=[0] if g else [])


class FakeRewriter:
    def __init__(self, query=QUERY, error=None, delay=0.0):
        self.query, self.error, self.delay, self.calls = query, error, delay, []

    def rewrite(self, question):
        self.calls.append(question)
        time.sleep(self.delay)
        if self.error:
            raise self.error
        return self.query


class FirstChunkGenerator:
    """Answers with the text of the first chunk it was given."""

    model = "claude-haiku-5-5"

    def __init__(self, delay=0.0):
        self.delay, self.calls = delay, []

    def answer(self, question, chunks):
        self.calls.append((question, [c.text for c in chunks]))
        time.sleep(self.delay)
        return Answer(chunks[0].text, usage=Usage(100, 10))


def build(grader=None, rewriter=None, generator=None, retriever=None, reranker=None):
    return Pipeline(retriever or QueryRetriever(), generator or FirstChunkGenerator(),
                    reranker or RecordingReranker(), grader, rewriter)


def ask(pipeline, question):
    tracer = RecordingTracer()
    with tracer.trace("ask", input=question) as trace:
        outcome = pipeline.ask(question, trace)
    pipeline.pool.shutdown(wait=True)  # step 9: background steps have ended
    return outcome, tracer.traces[0]


def names(trace):
    return [s["name"] for s in trace["steps"]]


def test_OR1_passing_chunks_answered_at_once():
    retriever, rewriter, generator = QueryRetriever(), FakeRewriter(), FirstChunkGenerator()
    outcome, trace = ask(build(FakeGrader(True), rewriter, generator, retriever), "What do place cells encode?")

    assert outcome.path == "papers"
    assert outcome.answer.text == "What do place cells encode? | chunk 0"
    assert retriever.queries == ["What do place cells encode?"]
    assert names(trace)[:2] == ["retrieve", "rerank"]
    assert sorted(names(trace)[2:]) == ["generate", "grade", "rewrite"]


def test_OR2_failed_grade_rewritten_and_answered_from_papers():
    retriever, reranker = QueryRetriever(), RecordingReranker()
    grader, generator = FakeGrader(False, True), FirstChunkGenerator()

    outcome, trace = ask(build(grader, FakeRewriter(QUERY), generator, retriever, reranker), FEAR)

    assert outcome.path == "papers_rewritten"
    assert retriever.queries == [FEAR, QUERY]
    assert reranker.queries == [FEAR, QUERY]
    second_grade_question, second_chunks = grader.calls[1]
    assert second_grade_question == FEAR
    assert second_chunks[0] == f"{QUERY} | chunk 0"
    assert (FEAR, second_chunks) in generator.calls  # the second generate: original question, chunks B
    assert outcome.answer.text == f"{QUERY} | chunk 0"
    assert trace["output"]["path"] == "papers_rewritten"
    rewrite_step = next(s for s in trace["steps"] if s["name"] == "rewrite")
    assert rewrite_step["output"] == QUERY


def test_OR3_two_failed_grades_end_with_couldnt_find():
    slow_generator = FirstChunkGenerator(delay=1.0)
    pipeline = build(FakeGrader(False, False), FakeRewriter(), slow_generator)

    start = time.perf_counter()
    tracer = RecordingTracer()
    with tracer.trace("ask", input=FEAR) as trace:
        outcome = pipeline.ask(FEAR, trace)
    elapsed = time.perf_counter() - start
    pipeline.pool.shutdown(wait=True)

    assert outcome.path == "none"
    assert outcome.answer.text == NOT_FOUND_PAPERS
    assert outcome.answer.sources == []
    assert elapsed < 0.5  # the 1 s generations were not waited for


def test_OR4_grade_rewrite_and_generate_run_together():
    pipeline = build(FakeGrader(True, delay=0.3), FakeRewriter(delay=0.3), FirstChunkGenerator(delay=0.3))

    start = time.perf_counter()
    outcome, trace = ask(pipeline, "What do place cells encode?")
    elapsed = time.perf_counter() - start

    assert outcome.path == "papers"
    assert elapsed < 0.5  # not 0.9 s
    starts = [s["start"] for s in trace["steps"] if s["name"] in ("grade", "rewrite", "generate")]
    assert len(starts) == 3 and max(starts) - min(starts) < 0.1


def test_OR5_passing_question_doesnt_wait_for_rewrite():
    pipeline = build(FakeGrader(True, delay=0.1), FakeRewriter(delay=2.0), FirstChunkGenerator(delay=0.2))

    start = time.perf_counter()
    tracer = RecordingTracer()
    with tracer.trace("ask", input="What do place cells encode?") as trace:
        outcome = pipeline.ask("What do place cells encode?", trace)
    elapsed = time.perf_counter() - start
    pipeline.pool.shutdown(wait=True)

    assert outcome.path == "papers"
    assert elapsed < 0.5


def test_OR6_grading_error_counts_as_passed():
    outcome, trace = ask(build(FakeGrader(GradingError("grading call failed")), FakeRewriter()),
                         "What do place cells encode?")

    assert outcome.path == "papers"
    assert outcome.answer.text == "What do place cells encode? | chunk 0"
    grade_step = next(s for s in trace["steps"] if s["name"] == "grade")
    assert "grading call failed" in grade_step["error"]


def test_OR7_rewrite_error_ends_with_couldnt_find():
    retriever = QueryRetriever()
    pipeline = build(FakeGrader(False), FakeRewriter(error=RewriteError("rewrite call failed")), retriever=retriever)

    outcome, trace = ask(pipeline, FEAR)

    assert outcome.path == "none"
    assert outcome.answer.text == NOT_FOUND_PAPERS
    assert retriever.queries == [FEAR]
    rewrite_step = next(s for s in trace["steps"] if s["name"] == "rewrite")
    assert "rewrite call failed" in rewrite_step["error"]


def test_OR8_without_grader_flow_is_row_5s():
    outcome, trace = ask(build(), "What do place cells encode?")

    assert outcome.path == "papers"
    assert names(trace) == ["retrieve", "rerank", "generate"]


def test_OR9_outcome_carries_chunks_and_query():
    rewritten, _ = ask(build(FakeGrader(False, True), FakeRewriter(QUERY)), FEAR)
    first, _ = ask(build(FakeGrader(True), FakeRewriter(QUERY)), "What do place cells encode?")

    assert rewritten.query == QUERY
    assert rewritten.chunks[0].text == f"{QUERY} | chunk 0"
    assert first.query is None
    assert first.chunks[0].text == "What do place cells encode? | chunk 0"
