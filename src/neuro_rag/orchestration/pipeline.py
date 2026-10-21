"""The decision layer: retrieve, then grade, and when the chunks fail, rewrite and search again.

Spec: docs/specs/orchestration/spec.md, "How it is built" (OR-1 to OR-8).
Grade, rewrite and generate run at the same time, so a passing question waits
only for its answer. Without a grader, this is row 5's straight line.
"""
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

from neuro_rag.config import PRICE_IN, PRICE_OUT
from neuro_rag.correction.rewrite import Rewriter, RewriteError
from neuro_rag.generation.generate import Answer, Generator
from neuro_rag.grading.grade import Grader, GradingError
from neuro_rag.observability.tracing import Trace
from neuro_rag.retrieval.rerank import Reranker, rerank
from neuro_rag.retrieval.retrieve import RERANK_CANDIDATES, TOP_K, Retriever

NOT_FOUND_PAPERS = "I couldn't find this in the papers."


@dataclass(frozen=True)
class Outcome:
    answer: Answer
    path: str  # "papers" | "papers_rewritten" | "none"


class Pipeline:
    def __init__(self, retriever: Retriever, generator: Generator, reranker: Reranker | None = None,
                 grader: Grader | None = None, rewriter: Rewriter | None = None):
        self.retriever = retriever  # built without a reranker: reranking is its own traced step
        self.generator = generator
        self.reranker = reranker
        self.grader = grader
        self.rewriter = rewriter
        self.pool = ThreadPoolExecutor(max_workers=8)

    def ask(self, question: str, trace: Trace) -> Outcome:
        chunks = self._search(question, trace)  # step 1
        if not self.grader:  # row 5's straight line (OR-8)
            return self._done(trace, self._generate(question, chunks, trace), "papers")

        grade = self._start(trace, "grade", self.grader.grade, question, chunks)  # step 2
        rewrite = self._start(trace, "rewrite", self.rewriter.rewrite, question) if self.rewriter else None
        answer = self.pool.submit(self._generate, question, chunks, trace)
        if self._passed(grade):  # step 3
            return self._done(trace, answer.result(), "papers")
        if rewrite is None:
            return self._done(trace, Answer(NOT_FOUND_PAPERS), "none")

        try:  # step 4
            query = rewrite.result()
        except RewriteError:
            return self._done(trace, Answer(NOT_FOUND_PAPERS), "none")
        chunks = self._search(query, trace)

        grade = self._start(trace, "grade", self.grader.grade, question, chunks)  # step 5: original question
        answer = self.pool.submit(self._generate, question, chunks, trace)
        if self._passed(grade):  # step 6
            return self._done(trace, answer.result(), "papers_rewritten")
        return self._done(trace, Answer(NOT_FOUND_PAPERS), "none")

    def index_name(self) -> str:
        return self.retriever.index_name()

    def _search(self, query: str, trace: Trace) -> list:
        """Retrieve and rerank with `query`, the words searched (choice 4)."""
        with trace.step("retrieve", input=query) as step:
            chunks = self.retriever.retrieve(query, k=RERANK_CANDIDATES if self.reranker else TOP_K)
            step.update(output=_listed(chunks))  # ids and scores only; texts go in "generate" (OB-2)
        if self.reranker:
            with trace.step("rerank", input=query) as step:
                chunks = rerank(self.reranker, query, chunks, TOP_K)
                step.update(output=_listed(chunks))
        return chunks

    def _start(self, trace: Trace, name: str, fn, *args) -> Future:
        """Run fn(*args) in the pool as its own traced step; an error is recorded on the step (step 7)."""
        def run():
            with trace.step(name) as step:
                result = fn(*args)
                step.update(output=result if isinstance(result, str) else vars(result))
                return result
        return self.pool.submit(run)

    def _generate(self, question: str, chunks: list, trace: Trace) -> Answer:
        with trace.step("generate", kind="generation", model=self.generator.model,
                        input={"question": question, "documents": [c.text for c in chunks]}) as step:
            answer = self.generator.answer(question, chunks)
            step.update(output=answer.text,
                        usage={"input": answer.usage.input_tokens, "output": answer.usage.output_tokens},
                        cost=answer.usage.input_tokens * PRICE_IN + answer.usage.output_tokens * PRICE_OUT)
        return answer

    @staticmethod
    def _passed(grade: Future) -> bool:
        """A grading error counts as passed (choice 2)."""
        try:
            return grade.result().passed
        except GradingError:
            return True

    @staticmethod
    def _done(trace: Trace, answer: Answer, path: str) -> Outcome:
        trace.update(output={"answer": answer.text, "pmcids": [s.pmcid for s in answer.sources], "path": path})
        return Outcome(answer, path)  # step 8


def _listed(chunks) -> list[dict]:
    return [{"chunk_id": c.chunk_id, "pmcid": c.pmcid, "page": c.page, "score": c.score} for c in chunks]
