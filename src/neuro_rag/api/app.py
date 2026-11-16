import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastembed import SparseTextEmbedding, TextEmbedding
from langfuse import observe
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel, StringConstraints
from qdrant_client import QdrantClient

from neuro_rag.config import EMBED_MODEL, QDRANT_URL, SPARSE_MODEL
from neuro_rag.generation.answer import answer, make_llm
from neuro_rag.retrieval.search import search

logger = logging.getLogger(__name__)

SEARCH_DOWN = "Search is unavailable. Try again later."
ANSWER_DOWN = "Answering is unavailable. Try again later."




# the question: spaces stripped, then 1 to 1000 characters; anything else is a 422
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class AskRequest(BaseModel):
    question: Question


class SourceOut(BaseModel):
    n: int
    pmcid: str
    page: int
    title: str
    citation: str
    url: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]


def build_pipeline():
    """Builds the client, embedders and LLM once; returns search_fn and answer_fn that reuse them."""
    client = QdrantClient(url=QDRANT_URL)
    embed = TextEmbedding(EMBED_MODEL).embed
    sparse_embed = SparseTextEmbedding(SPARSE_MODEL).query_embed
    llm = make_llm().with_config(callbacks=[CallbackHandler()])  # every Claude call → a Langfuse generation

    def search_fn(question):
        return search(question, client, embed, sparse_embed)  # dense, top 5 (defaults)

    def answer_fn(question, hits):
        return answer(question, hits, llm)

    return search_fn, answer_fn


def create_app(search_fn=None, answer_fn=None) -> FastAPI:
    """The app. Tests pass fake search_fn/answer_fn; uvicorn calls it with none (--factory)."""
    if search_fn is None or answer_fn is None:
        search_fn, answer_fn = build_pipeline()

    # each step becomes a Langfuse observation inside the request's trace; a plain def,
    # because the tests pass objects (FakeSearch()), not functions
    @observe(name="search")
    def traced_search(question):
        return search_fn(question)

    @observe(name="answer")
    def traced_answer(question, hits):
        return answer_fn(question, hits)

    app = FastAPI(title="Neuro-RAG")

    @app.post("/ask")
    @observe(name="ask")
    def ask(request: AskRequest) -> AskResponse:
        # 1. search; any failure is a 503, the real error goes to the log only
        try:
            hits = traced_search(request.question)
        except Exception:
            logger.exception("search failed")
            raise HTTPException(status_code=503, detail=SEARCH_DOWN)

        # 2. answer; same rule
        try:
            result = traced_answer(request.question, hits)
        except Exception:
            logger.exception("answer failed")
            raise HTTPException(status_code=503, detail=ANSWER_DOWN)

        # 3. the response: the answer text and its sources, nothing else
        sources = [SourceOut(n=s.n, pmcid=s.pmcid, page=s.page, title=s.title, citation=s.citation, url=s.url)
                   for s in result.sources]
        return AskResponse(answer=result.text, sources=sources)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
