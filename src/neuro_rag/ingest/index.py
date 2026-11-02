import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from neuro_rag.config import BATCH, COLLECTION, EMBED_SIZE
from neuro_rag.ingest.catalog import Paper
from neuro_rag.ingest.chunk import Chunk


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def recreate_collection(client: QdrantClient, name: str = COLLECTION) -> None:
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(name, vectors_config=VectorParams(size=EMBED_SIZE, distance=Distance.COSINE))


def write_chunks(client: QdrantClient, chunks: list[Chunk], papers: dict[str, Paper], embed, name: str = COLLECTION) -> int:
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        vectors = list(embed([c.text for c in batch]))
        points = []
        for chunk, vector in zip(batch, vectors):
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
            points.append(PointStruct(id=point_id(chunk.chunk_id), vector=list(vector), payload=payload))
        client.upsert(name, points, wait=True)
    return len(chunks)
