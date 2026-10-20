"""Question -> top chunks, from dense and keyword search fused in one Qdrant query.

Spec: docs/specs/retrieval/spec.md (RT-1 to RT-17).
"""
from dataclasses import dataclass

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from qdrant_client.models import Fusion, FusionQuery, Prefetch

from neuro_rag.config import COLLECTION_ALIAS
from neuro_rag.encoders import DENSE, SPARSE, Encoders
from neuro_rag.retrieval.rerank import Reranker, rerank

TOP_K = 5
CANDIDATES = 20  # per search, before fusion
RERANK_CANDIDATES = 20  # fused chunks the reranker reorders (decision 005)


class RetrievalError(Exception):
    """Qdrant can't be reached or the index isn't there; the API answers 503 (row 5)."""


@dataclass(frozen=True)
class Retrieved:
    chunk_id: str
    text: str
    pmcid: str
    title: str
    citation: str
    license: str
    page: int
    score: float


class Retriever:
    """Created once per process; the encoders inside it load their models once (RT-10).

    Every query names the alias, never a versioned collection, so a rebuild is
    picked up without restarting (RT-9). With a reranker, fusion returns more
    chunks and the reranker's scores pick the final k (RT-14).
    """

    def __init__(self, client: QdrantClient, encoders: Encoders, alias: str = COLLECTION_ALIAS,
                 candidates: int = CANDIDATES, reranker: Reranker | None = None,
                 rerank_candidates: int = RERANK_CANDIDATES):
        self.client = client
        self.encoders = encoders  # shared with ingest (RT-8)
        self.alias = alias
        self.candidates = candidates
        self.reranker = reranker
        self.rerank_candidates = rerank_candidates

    def retrieve(self, question: str, k: int = TOP_K) -> list[Retrieved]:
        """The k best chunks, best first: by reciprocal rank fusion, then by the reranker if there is one."""
        prefetch = self._prefetch(question)
        limit = max(k, self.rerank_candidates) if self.reranker else k
        points = self._query(prefetch=prefetch, query=FusionQuery(fusion=Fusion.RRF), limit=limit)
        chunks = [_to_retrieved(p) for p in points]
        return rerank(self.reranker, question, chunks, k) if self.reranker else chunks

    def index_name(self) -> str:
        """The collection the alias points at now; raises RetrievalError if Qdrant or the alias is missing."""
        try:
            aliases = self.client.get_aliases().aliases
        except (ResponseHandlingException, httpx.HTTPError, ConnectionError, UnexpectedResponse) as e:
            raise RetrievalError("Qdrant is unreachable") from e
        for a in aliases:
            if a.alias_name == self.alias:
                return a.collection_name
        raise RetrievalError(f"alias '{self.alias}' not found")

    def candidate_pmcids(self, question: str) -> set[str]:
        """Papers among all candidates, before fusion keeps the top k (reported by RT-7)."""
        pmcids = set()
        for search in self._prefetch(question):
            points = self._query(query=search.query, using=search.using, limit=search.limit)
            pmcids |= {p.payload["pmcid"] for p in points}
        return pmcids

    def _prefetch(self, question: str) -> list[Prefetch]:
        if not question or not question.strip():
            raise ValueError("question is empty")  # before any Qdrant call (RT-11)
        dense = self.encoders.dense([question])[0]
        sparse = self.encoders.sparse([question])[0]
        searches = [Prefetch(query=dense, using=DENSE, limit=self.candidates)]
        if sparse.indices:  # a question of only stopwords has no keywords to search
            searches.append(Prefetch(query=sparse, using=SPARSE, limit=self.candidates))
        return searches

    def _query(self, **kwargs) -> list:
        try:
            return self.client.query_points(collection_name=self.alias, with_payload=True, **kwargs).points
        except UnexpectedResponse as e:
            if e.status_code == 404:
                raise RetrievalError(f"alias '{self.alias}' not found") from e
            raise RetrievalError(f"Qdrant error {e.status_code}") from e
        except (ResponseHandlingException, httpx.HTTPError, ConnectionError) as e:
            raise RetrievalError("Qdrant is unreachable") from e


def _to_retrieved(point) -> Retrieved:
    p = point.payload
    return Retrieved(p["chunk_id"], p["text"], p["pmcid"], p["title"], p["citation"], p["license"], p["page"],
                     point.score)
