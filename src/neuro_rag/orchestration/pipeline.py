"""The steps that answer one question, in a straight line: retrieve -> rerank -> generate.

Spec: docs/specs/api/spec.md (In and out). Row 7 replaces this line with the
corrective graph; the API keeps calling `ask` and doesn't change.
"""
from neuro_rag.config import PRICE_IN, PRICE_OUT
from neuro_rag.generation.generate import Answer, Generator
from neuro_rag.observability.tracing import Trace
from neuro_rag.retrieval.rerank import Reranker, rerank
from neuro_rag.retrieval.retrieve import RERANK_CANDIDATES, TOP_K, Retriever


class Pipeline:
    def __init__(self, retriever: Retriever, generator: Generator, reranker: Reranker | None = None):
        self.retriever = retriever  # built without a reranker: reranking is its own traced step
        self.generator = generator
        self.reranker = reranker

    def ask(self, question: str, trace: Trace) -> Answer:
        """Each step is a step of `trace`, so its time, inputs and outputs are recorded (OB-1)."""
        with trace.step("retrieve", input=question) as step:
            chunks = self.retriever.retrieve(question, k=RERANK_CANDIDATES if self.reranker else TOP_K)
            step.update(output=_listed(chunks))  # ids and scores only; texts go in "generate" (OB-2)

        if self.reranker:
            with trace.step("rerank") as step:
                chunks = rerank(self.reranker, question, chunks, TOP_K)
                step.update(output=_listed(chunks))

        with trace.step("generate", kind="generation", model=self.generator.model,
                        input={"question": question, "documents": [c.text for c in chunks]}) as step:
            answer = self.generator.answer(question, chunks)
            step.update(output=answer.text,
                        usage={"input": answer.usage.input_tokens, "output": answer.usage.output_tokens},
                        cost=answer.usage.input_tokens * PRICE_IN + answer.usage.output_tokens * PRICE_OUT)
        return answer

    def index_name(self) -> str:
        return self.retriever.index_name()


def _listed(chunks) -> list[dict]:
    return [{"chunk_id": c.chunk_id, "pmcid": c.pmcid, "page": c.page, "score": c.score} for c in chunks]
