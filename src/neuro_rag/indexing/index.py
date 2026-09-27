import re
from collections import defaultdict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from neuro_rag.config import BM25_TOP_K, CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, VECTOR_SIZE


model = SentenceTransformer(EMBEDDING_MODEL)


def ingest_documents(
    qdrant: QdrantClient,
    collection_name: str,
    chunks: list[Document],
    vector_size: int = VECTOR_SIZE,
) -> None:
    """Rebuild the collection from scratch: embed chunks and store them with their metadata.

    `chunks` come from chunk_pages(), so each has page_content and metadata with a
    chunk_id (the point's id) plus pmcid, title, citation and page for citing hits later.
    """
    # Full rebuild: chunk IDs change when chunk settings change, so old points would linger.
    if qdrant.collection_exists(collection_name):
        qdrant.delete_collection(collection_name)
    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    vectorized_chunks = get_text_embeddings([c.page_content for c in chunks])
    points = [
        PointStruct(
            id=str(uuid5(NAMESPACE_URL, chunk.metadata["chunk_id"])),  # same chunk -> same point id every run
            vector= vector.tolist(),
            payload={
                "content": chunk.page_content,               
                "metadata": chunk.metadata
            },
        )
         for chunk, vector in zip(chunks, vectorized_chunks)
    ]
    qdrant.upsert(collection_name=collection_name, points=points)


def chunk_pages(pages, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Split pages into token-sized chunks; each chunk keeps its page's metadata
    plus a stable chunk_id like "PMC3854211-p4-c2" (paper, page, chunk number on that page)."""
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(pages)
    counters = defaultdict(int)  # (pmcid, page) -> chunks numbered so far
    for chunk in chunks:
        key = (chunk.metadata["pmcid"], chunk.metadata["page"])
        chunk.metadata["chunk_id"] = f"{key[0]}-p{key[1]}-c{counters[key]}"
        counters[key] += 1
    return chunks


def get_text_embeddings(text):
    
    outputs = model.encode(text,  normalize_embeddings=True)
    return outputs


def tokenize(text):
    """Lowercase words; hyphenated terms stay whole ("IGF-1" -> "igf-1"), punctuation is dropped."""
    return re.findall(r"\w+(?:-\w+)*", text.lower())


def build_bm25(documents):
    """Build the keyword index once; the same tokenize() must be used for queries."""
    return BM25Okapi([tokenize(d.page_content) for d in documents])


def bm25_search(query, bm25_index, documents, k=BM25_TOP_K):
    """Top-k (document, score) pairs; k is large because results are fused with dense search."""
    scores = bm25_index.get_scores(tokenize(query))
    top_indices = scores.argsort()[::-1][:k]
    return [(documents[i], scores[i]) for i in top_indices if scores[i] > 0]  # 0 = no query word matched