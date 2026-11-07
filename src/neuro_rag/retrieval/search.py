import sys
from dataclasses import dataclass

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Fusion, FusionQuery, Prefetch, SparseVector

from neuro_rag.config import COLLECTION, EMBED_MODEL, QDRANT_URL, SPARSE_MODEL


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    pmcid: str
    page: int
    title: str
    citation: str
    license: str
    text: str
    score: float


def search(question: str, client: QdrantClient, embed, sparse_embed, k: int = 5,
           mode: str = "dense", name: str = COLLECTION) -> list[Hit]:
    if mode not in ("dense", "hybrid"):
        raise ValueError(f"unknown mode: {mode}")
    question = question.strip()
    if not question:
        raise ValueError("empty question")
    dense = list(embed([question]))[0].tolist()
    if mode == "dense":
        points = client.query_points(name, query=dense, using="dense", limit=k, with_payload=True).points
    else:
        s = list(sparse_embed([question]))[0]
        points = client.query_points(
            name,
            prefetch=[
                Prefetch(query=dense, using="dense", limit=20),
                Prefetch(query=SparseVector(indices=s.indices.tolist(), values=s.values.tolist()), using="bm25", limit=20),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=k,
            with_payload=True,
        ).points

    fields = ("chunk_id", "pmcid", "page", "title", "citation", "license", "text")
    return [Hit(**{f: p.payload[f] for f in fields}, score=p.score) for p in points]


def main():
    args = sys.argv[1:]
    mode = "dense"
    if args and args[0] == "--hybrid":
        mode = "hybrid"
        args = args[1:]
    if not args:
        print('usage: python -m neuro_rag.retrieval.search [--hybrid] "<question>"')
        sys.exit(2)

    hits = search(args[0], QdrantClient(url=QDRANT_URL), TextEmbedding(EMBED_MODEL).embed,
                  SparseTextEmbedding(SPARSE_MODEL).query_embed, mode=mode)
    for hit in hits:
        print(f"{hit.score:.4f}  {hit.chunk_id}  {hit.text[:80]}")


if __name__ == "__main__":
    main()
