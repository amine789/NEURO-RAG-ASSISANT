import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from langfuse import observe
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel, StringConstraints
from qdrant_client import QdrantClient

from neuro_rag.config import EMBED_MODEL, GRADER, QDRANT_URL, SPARSE_MODEL, RERANK_MODEL
from neuro_rag.crag.graders import gemma_grader, jev_grader, laya_grader
from neuro_rag.crag.loop import rewrite, run_loop, web_hits
from neuro_rag.generation.answer import answer, make_llm
from neuro_rag.ingest.chunk import TokenCounter
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
    path: list[str]      # row 9: the states taken, e.g. ["retrieve", "grade:good", "generate"] (CR-10)
    used_web: bool       # row 9: True if the answer was written from web pages


# row 9: the loop's grader by name (config.GRADER); Haiku is left out: it was compared, not chosen
GRADERS = {"jev": jev_grader, "gemma": gemma_grader, "laya": laya_grader}


class SearchDown(Exception):
    """search_fn failed inside the loop: the API answers 503 SEARCH_DOWN, as before row 9."""


class AnswerDown(Exception):
    """answer_fn failed inside the loop: the API answers 503 ANSWER_DOWN, as before row 9."""


def build_pipeline():
    """Builds the client, embedders, reranker and LLM once; returns the five steps that reuse them.

    Returns (search_fn, answer_fn, grade_fn, rewrite_fn, web_fn):
      search_fn(query): row 8's search, dense top 20 reranked, top 5;
      answer_fn(question, hits): row 3's cited answer (Haiku 4.5);
      grade_fn(question, hits): the grader named by config.GRADER ("jev": Jev via
        OpenRouter, needs OPENROUTER_API_KEY; without it every grade fails and counts
        as weak, so every question ends "not covered");
      rewrite_fn(question, last_query): loop.rewrite with the same LLM (traced too);
      web_fn(query): loop.web_hits with the same reranker (needs FIRECRAWL_API_KEY).
    The token counter for web chunks is built on the first web call only: it loads a
    tokenizer, which most requests never need.
    """
    client = QdrantClient(url=QDRANT_URL)
    embed = TextEmbedding(EMBED_MODEL).embed
    sparse_embed = SparseTextEmbedding(SPARSE_MODEL).query_embed
    rerank = TextCrossEncoder(RERANK_MODEL).rerank
    llm = make_llm().with_config(callbacks=[CallbackHandler()])  # every Claude call → a Langfuse generation
    counter = []                                                 # TokenCounter, built on the first web call

    def search_fn(question):
        return search(question, client, embed, sparse_embed, rerank=rerank)  # dense, top 5 (defaults)

    def answer_fn(question, hits):
        return answer(question, hits, llm)

    def rewrite_fn(question, last_query):
        return rewrite(question, last_query, llm)

    def web_fn(query):
        if not counter:
            counter.append(TokenCounter())
        return web_hits(query, rerank, counter[0])

    return search_fn, answer_fn, GRADERS[GRADER], rewrite_fn, web_fn


def create_app(search_fn=None, answer_fn=None, grade_fn=None, rewrite_fn=None, web_fn=None) -> FastAPI:
    """The app. uvicorn calls it with nothing (--factory): the real pipeline, with the loop.

    Tests pass fakes. With only search_fn and answer_fn (row 5's tests), there is no
    grade_fn, so the loop is off: search, then answer, path ["retrieve", "generate"],
    used_web false: row 8's behaviour, which is also CR-12's baseline. With grade_fn
    (and rewrite_fn and web_fn) the question goes through run_loop (row 9).
    """
    if search_fn is None or answer_fn is None:
        search_fn, answer_fn, grade_fn, rewrite_fn, web_fn = build_pipeline()

    # each step becomes a Langfuse observation inside the request's trace; a plain def,
    # because the tests pass objects (FakeSearch()), not functions. Named after the
    # loop's states (row 9, CR-11); grade, rewrite and web are traced in crag/loop.py.
    # A failure is re-raised as SearchDown / AnswerDown so the 503 still says which
    # step failed, even from inside run_loop.
    @observe(name="retrieve")
    def traced_search(question):
        try:
            return search_fn(question)
        except Exception as e:
            raise SearchDown() from e

    @observe(name="generate")
    def traced_answer(question, hits):
        try:
            return answer_fn(question, hits)
        except Exception as e:
            raise AnswerDown() from e

    app = FastAPI(title="Neuro-RAG")

    @app.post("/ask")
    @observe(name="ask")
    def ask(request: AskRequest) -> AskResponse:
        # 1. the loop (row 9) when there is a grader, else search then answer (row 8);
        #    a search or answer failure is a 503, the real error goes to the log only
        try:
            if grade_fn is None:
                result = traced_answer(request.question, traced_search(request.question))
                path, used_web = ["retrieve", "generate"], False
            else:
                crag = run_loop(request.question, traced_search, grade_fn, traced_answer, rewrite_fn, web_fn)
                result, path, used_web = crag.answer, crag.path, crag.used_web
        except SearchDown:
            logger.exception("search failed")
            raise HTTPException(status_code=503, detail=SEARCH_DOWN)
        except AnswerDown:
            logger.exception("answer failed")
            raise HTTPException(status_code=503, detail=ANSWER_DOWN)

        # 2. the response: the answer text, its sources, and the path taken (CR-10)
        sources = [SourceOut(n=s.n, pmcid=s.pmcid, page=s.page, title=s.title, citation=s.citation, url=s.url)
                   for s in result.sources]
        return AskResponse(answer=result.text, sources=sources, path=path, used_web=used_web)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
