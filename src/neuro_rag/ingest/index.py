"""Chunks -> a new versioned Qdrant collection behind an alias, plus a snapshot (IN-9 to IN-13)."""
import re
from pathlib import Path
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import (
    CreateAlias,
    CreateAliasOperation,
    DeleteAlias,
    DeleteAliasOperation,
    Distance,
    Modifier,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from neuro_rag.encoders import DENSE, SPARSE
from neuro_rag.ingest.chunk import Chunk

BATCH = 128


class ChunkEncoder(Protocol):
    def dense(self, texts: list[str]) -> list[list[float]]: ...
    def sparse(self, texts: list[str]) -> list[SparseVector]: ...


def point_id(chunk_id: str) -> str:
    """Same chunk ID -> same point ID on every build."""
    return str(uuid5(NAMESPACE_URL, chunk_id))


def next_collection_name(client: QdrantClient, alias: str) -> str:
    """'<alias>-v<N>', one higher than any existing version."""
    pattern = re.compile(rf"{re.escape(alias)}-v(\d+)")
    versions = [int(m.group(1)) for c in client.get_collections().collections if (m := pattern.fullmatch(c.name))]
    return f"{alias}-v{max(versions, default=0) + 1}"


def alias_target(client: QdrantClient, alias: str) -> str | None:
    """The collection the alias points at, or None."""
    for a in client.get_aliases().aliases:
        if a.alias_name == alias:
            return a.collection_name
    return None


def create_collection(client: QdrantClient, name: str, dense_size: int, build_info: dict) -> None:
    """Dense (cosine) and sparse vectors; sparse uses IDF computed by Qdrant (decision 002)."""
    client.create_collection(
        collection_name=name,
        vectors_config={DENSE: VectorParams(size=dense_size, distance=Distance.COSINE)},
        sparse_vectors_config={SPARSE: SparseVectorParams(modifier=Modifier.IDF)},
        metadata=build_info,
    )


def write_chunks(client: QdrantClient, name: str, chunks: list[Chunk], encoder: ChunkEncoder) -> None:
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        texts = [c.text for c in batch]
        dense, sparse = encoder.dense(texts), encoder.sparse(texts)
        client.upsert(
            collection_name=name,
            points=[
                PointStruct(id=point_id(c.chunk_id), vector={DENSE: d, SPARSE: s}, payload=payload(c))
                for c, d, s in zip(batch, dense, sparse)
            ],
            wait=True,
        )


def payload(chunk: Chunk) -> dict:
    paper = chunk.page.paper
    return {
        "text": chunk.text,
        "chunk_id": chunk.chunk_id,
        "pmcid": paper.pmcid,
        "title": paper.title,
        "citation": paper.citation,
        "license": paper.license,
        "page": chunk.page.page,
    }


def check_count(client: QdrantClient, name: str, expected: int) -> None:
    stored = client.count(collection_name=name, exact=True).count
    if stored != expected:
        raise RuntimeError(f"{name} holds {stored} points, expected {expected}")


def move_alias(client: QdrantClient, alias: str, name: str) -> None:
    """Point the alias at `name` in one atomic call, so readers never see no alias."""
    operations = []
    if alias_target(client, alias) is not None:
        operations.append(DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=alias)))
    operations.append(CreateAliasOperation(create_alias=CreateAlias(collection_name=name, alias_name=alias)))
    client.update_collection_aliases(change_aliases_operations=operations)


def save_snapshot(client: QdrantClient, name: str, url: str, api_key: str | None, out_dir: Path) -> Path:
    """Create a snapshot on the Qdrant server and download it as one local file."""
    snapshot = client.create_snapshot(collection_name=name, wait=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / snapshot.name
    headers = {"api-key": api_key} if api_key else {}
    with requests.get(f"{url}/collections/{name}/snapshots/{snapshot.name}", headers=headers,
                      stream=True, timeout=300) as response:
        response.raise_for_status()
        with open(path, "wb") as f:
            for block in response.iter_content(chunk_size=1 << 20):
                f.write(block)
    return path
