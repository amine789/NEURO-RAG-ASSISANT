"""Fakes for the API and observability tests: the real Pipeline wired to fake steps, and a
tracer that records into a list. The chunk is the one the specs use: PMC1, page 3."""
import time
import uuid

from neuro_rag.generation.generate import Answer, Citation, Source, Usage
from neuro_rag.observability.tracing import Tracer
from neuro_rag.orchestration.pipeline import Pipeline
from neuro_rag.retrieval.retrieve import Retrieved

PLACE_CELLS = "Place cells in the hippocampus fire when the animal is at a specific location."
ANSWER = "Place cells fire when the animal is at a specific location. [1]"
PMC1_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/"


def chunk(n: int = 0) -> Retrieved:
    return Retrieved(f"PMC1-p3-c{n}", PLACE_CELLS, "PMC1", "Place cells paper", "Author et al. 2020",
                     "CC BY", 3, 0.03)


class FakeRetriever:
    def __init__(self, error: Exception | None = None, index: str | Exception = "hippocampus-v1"):
        self.error, self.index, self.calls = error, index, 0

    def retrieve(self, question, k=5):
        self.calls += 1
        if self.error:
            raise self.error
        return [chunk(n) for n in range(k)]

    def index_name(self):
        if isinstance(self.index, Exception):
            raise self.index
        return self.index


class FakeReranker:
    def score(self, question, texts):
        return [float(len(texts) - i) for i in range(len(texts))]


class FakeGenerator:
    """Answers ANSWER citing PMC1 page 3, or `text` citing nothing, or raises `error`."""

    model = "claude-haiku-5-5"

    def __init__(self, text: str | None = None, error: Exception | None = None, usage=Usage(3000, 400)):
        self.text, self.error, self.usage = text, error, usage

    def answer(self, question, chunks):
        if self.error:
            raise self.error
        if self.text is not None:
            return Answer(self.text, usage=self.usage)
        return Answer(ANSWER, [Source(1, "PMC1", "Place cells paper", "Author et al. 2020", 3, PMC1_URL)],
                      [Citation(1, 0, PLACE_CELLS)], self.usage)


def fake_pipeline(retriever=None, generator=None) -> Pipeline:
    return Pipeline(retriever or FakeRetriever(), generator or FakeGenerator(), FakeReranker())


class RecordingTracer(Tracer):
    """Keeps each trace as a dict with its steps, instead of sending it anywhere."""

    def __init__(self):
        self.traces = []

    def _start_trace(self, name, **fields):
        trace = {"id": uuid.uuid4().hex, "name": name, "steps": [], "start": time.perf_counter(), "end": None,
                 **fields}
        self.traces.append(trace)
        return trace

    def _start_step(self, parent, name, kind, **fields):
        step = {"name": name, "kind": kind, "start": time.perf_counter(), "end": None, **fields}
        parent["steps"].append(step)
        return step

    def _update(self, handle, **fields):
        handle.update(fields)

    def _end(self, handle):
        handle["end"] = time.perf_counter()

    def _trace_id(self, handle):
        return handle["id"]
