"""HTTP entry point: POST /ask and GET /health.

Spec: docs/specs/api/spec.md (AP-1 to AP-10).

    uvicorn neuro_rag.api.app:app --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from neuro_rag.generation.generate import GenerationError
from neuro_rag.observability.tracing import Tracer, make_tracer
from neuro_rag.orchestration.pipeline import Pipeline
from neuro_rag.retrieval.retrieve import RetrievalError

log = logging.getLogger(__name__)

MAX_QUESTION = 1000  # characters, after trimming spaces (AP-4)

# Messages for the user; never the exception text, which may hold internal details (AP-5 to AP-7).
INDEX_DOWN = "The paper index is unavailable. Please try again shortly."
CLAUDE_DOWN = "The answer service is unavailable. Please try again shortly."
UNEXPECTED = "Something went wrong."


class AskRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def _check(cls, question: str) -> str:
        question = question.strip()
        if not question:
            raise ValueError("The question is empty.")
        if len(question) > MAX_QUESTION:
            raise ValueError(f"The question is longer than {MAX_QUESTION:,} characters.")
        return question


class Source(BaseModel):
    n: int
    pmcid: str
    title: str
    citation: str
    page: int
    url: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    trace_id: str


def build_pipeline(generator=None) -> Pipeline:
    """The real components, with the models loaded now rather than on the first question (AP-8).

    `generator` replaces Claude in tests that measure everything else.
    """
    from qdrant_client import QdrantClient

    from neuro_rag import config
    from neuro_rag.encoders import Encoders
    from neuro_rag.generation.generate import Generator
    from neuro_rag.retrieval.rerank import Reranker
    from neuro_rag.retrieval.retrieve import Retriever

    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    pipeline = Pipeline(Retriever(client, Encoders()), generator or Generator(), Reranker())  # decision 005
    # Load and run each model once; this needs no Qdrant, so a service started before Qdrant still starts.
    pipeline.retriever.encoders.dense(["warm up"])
    pipeline.retriever.encoders.sparse(["warm up"])
    pipeline.reranker.score("warm up", ["warm up"])
    return pipeline


def create_app(pipeline: Pipeline | None = None, tracer: Tracer | None = None) -> FastAPI:
    """Tests pass a pipeline of fakes and a recording tracer; the service builds the real ones."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.pipeline = pipeline or build_pipeline()
        app.state.tracer = tracer or make_tracer()
        yield
        app.state.tracer.flush()

    app = FastAPI(title="Neuro-RAG", lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def bad_question(request: Request, exc: RequestValidationError):
        """One plain sentence instead of FastAPI's list of errors (AP-3, AP-4)."""
        error = exc.errors()[0]
        if error["type"] == "missing" or error["loc"][-1] != "question":
            detail = "The question is missing."
        else:
            detail = error["msg"].removeprefix("Value error, ")
        return JSONResponse(status_code=422, content={"detail": detail})

    @app.post("/ask", response_model=AskResponse)
    def ask(body: AskRequest, request: Request):
        state = request.app.state
        trace = None
        try:
            with state.tracer.trace("ask", input=body.question) as trace:
                answer = state.pipeline.ask(body.question, trace)
                trace.update(output={"answer": answer.text, "pmcids": [s.pmcid for s in answer.sources]})
        except RetrievalError:
            return _error(503, INDEX_DOWN, trace)
        except GenerationError:
            return _error(503, CLAUDE_DOWN, trace)
        except Exception:
            log.exception("unexpected error, trace_id=%s", trace.id if trace else None)  # findable (AP-7)
            return _error(500, UNEXPECTED, trace)
        return AskResponse(answer=answer.text, sources=[Source(**vars(s)) for s in answer.sources],
                           trace_id=trace.id)

    @app.get("/health")
    def health(request: Request):
        """Ready when the index answers; never calls Claude (AP-9)."""
        try:
            index = request.app.state.pipeline.index_name()
        except RetrievalError:
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return {"status": "ok", "index": index}

    return app


def _error(status: int, detail: str, trace) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail, "trace_id": trace.id if trace else None})


app = create_app()
