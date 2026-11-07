import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, Modifier, PointStruct, SparseVector, SparseVectorParams, VectorParams

from neuro_rag.config import BATCH, COLLECTION, EMBED_SIZE
from neuro_rag.ingest.catalog import Paper
from neuro_rag.ingest.chunk import Chunk


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def recreate_collection(client: QdrantClient, name: str = COLLECTION) -> None:
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(
        name,
        vectors_config={"dense": VectorParams(size=EMBED_SIZE, distance=Distance.COSINE)},
        sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
    )


def write_chunks(client: QdrantClient, chunks: list[Chunk], papers: dict[str, Paper], embed, sparse_embed,
                 name: str = COLLECTION) -> int:
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        texts = [c.text for c in batch]
        vectors = list(embed(texts))
        sparse = list(sparse_embed(texts))
        points = []
        for chunk, vector, s in zip(batch, vectors, sparse):
            paper = papers[chunk.pmcid]
            payload = {
                "chunk_id": chunk.chunk_id,
                "pmcid": chunk.pmcid,
                "page": chunk.page,
                "title": paper.title,
                "citation": paper.citation,
                "license": paper.license,
                "text": chunk.text,
            }
            vector = {
                "dense": list(vector),
                "bm25": SparseVector(indices=s.indices.tolist(), values=s.values.tolist()),
            }
            points.append(PointStruct(id=point_id(chunk.chunk_id), vector=vector, payload=payload))
        client.upsert(name, points, wait=True)
    return len(chunks)
