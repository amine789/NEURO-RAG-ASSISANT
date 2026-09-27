from neuro_rag.indexing.index import  build_bm25, bm25_search, get_text_embeddings
from neuro_rag.config import COLLECTION_NAME
from neuro_rag.retrieval.fusion import rrf_fuse


class Retriever:
    def __init__(self, chunks, qdrant_client):
        self.chunks=chunks
        self.bm25 = build_bm25(chunks)
        self.qdrant_client = qdrant_client
        self.by_id = {c.metadata["chunk_id"]: c for c in chunks}  # chunk_id -> chunk, to return full chunks

    def retrieve(self, question, k):
         query_embedding = get_text_embeddings(question).tolist()
         bm25_hits = bm25_search(question, self.bm25, self.chunks, k)
         dense_hits = self.qdrant_client.query_points(
                   COLLECTION_NAME, query=query_embedding, limit=k
              ).points
         fused = rrf_fuse(
                  [hit.payload["metadata"]["chunk_id"] for hit in dense_hits],
                  [chunk.metadata["chunk_id"] for chunk, _ in bm25_hits],
             )
         return [(self.by_id[chunk_id], score) for chunk_id, score in fused[:k]]  # union can hold up to 2k