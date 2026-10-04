from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from neuro_rag.retrieval.retrieve import Retriever
from neuro_rag.grading.grade import grade_retrieval_results
from neuro_rag.correction.rewriter import rewrite_query
from neuro_rag.config import llm, MIN_RELEVANT, MAX_RETRIES
from neuro_rag.correction.web_search import search_web
from neuro_rag.generation.generate_answer import generate_answer
TOP_K = 5  # chunks retrieved per query


class RAGState(TypedDict):
    question: str
    query: str
    documents: list[Document]
    retries: int
    used_web: bool
    answer: str


def make_retrieve(retriever: Retriever):
    """Build the retrieve node. The Retriever is slow to create, so it is made
    once outside the graph and passed in here."""

    def retrieve(state: RAGState) -> dict:
        results = retriever.retrieve(state["query"], k=TOP_K)
        return {"documents": [doc for doc, _score in results]}

    return retrieve


def grade(state: RAGState) -> dict:
    pairs = [(doc, 0.0) for doc in state["documents"]]  # grader wants (Document, score)
    relevant = grade_retrieval_results(state["question"], pairs)
    return {"documents": [doc for doc, _ in relevant]}


def rewrite(state: RAGState) -> dict:
    # Rewrite from the original question, not the last query, so a bad rewrite
    # isn't built on; the next retrieve uses the new query.
    return {
        "query": rewrite_query(llm, state["question"]),
        "retries": state["retries"] + 1,
    }


def web_search(state: RAGState)->dict:
    documents = search_web(state['query'])
    return {"documents": documents, "used_web":True}


def generate(state: RAGState)->dict:
    answer = generate_answer(state['question'], state['documents'])
    return {"answer": answer}


def decide(state: RAGState) -> str:
    """Route after grading: answer if enough chunks are relevant, otherwise
    rewrite and retry while the retry budget lasts, then fall back to the web."""
    if len(state["documents"]) >= MIN_RELEVANT:
        return "generate"
    if state["retries"] < MAX_RETRIES:
        return "rewrite"
    return "web_search"


def build_graph(retriever: Retriever):
    """Wire the nodes into the corrective loop and compile it:
    retrieve -> grade -> generate, or -> rewrite -> retrieve, or -> web_search -> generate."""
    graph = StateGraph(RAGState)

    graph.add_node("retrieve", make_retrieve(retriever))
    graph.add_node("grade", grade)
    graph.add_node("rewrite", rewrite)
    graph.add_node("web_search", web_search)
    graph.add_node("generate", generate)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", decide, ["generate", "rewrite", "web_search"])
    graph.add_edge("rewrite", "retrieve")  # the retry loop
    graph.add_edge("web_search", "generate")  # web results are graded inside search_web
    graph.add_edge("generate", END)

    return graph.compile()


def initial_state(question: str) -> RAGState:
    """Starting state for a question: search with the question itself, no retries yet."""
    return {
        "question": question,
        "query": question,
        "documents": [],
        "retries": 0,
        "used_web": False,
        "answer": "",
    }


def run(app, question: str) -> RAGState:
    """Run one question through a compiled graph and return the final state."""
    return app.invoke(initial_state(question))




    




