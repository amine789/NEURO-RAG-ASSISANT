from neuro_rag.ingest.ingestion import load_folder, save_pages
from neuro_rag.indexing.index import get_text_embeddings, ingest_documents, build_bm25, bm25_search, chunk_pages
from neuro_rag.config import RAW_DIR
from neuro_rag.config import QDRANT_PATH, COLLECTION_NAME, VECTOR_SIZE
from neuro_rag.retrieval.fusion import rrf_fuse
from qdrant_client import QdrantClient


if __name__ == "__main__":  # also required by ProcessPoolExecutor on macOS
     pages = load_folder(RAW_DIR)
     save_pages(pages)
     chunks = chunk_pages(pages)
     qdrant_client = QdrantClient(path=str(QDRANT_PATH))
     ingest_documents(qdrant_client,
                      COLLECTION_NAME,
                      chunks,
                      VECTOR_SIZE)
     query = "Does resistance exercise improve hippocampus-dependent memory?"
     query_embedding = get_text_embeddings(query)

     # Dense: closest chunks by meaning, from the vectors stored in Qdrant
     dense_hits = qdrant_client.query_points(
          COLLECTION_NAME, query=query_embedding.tolist(), limit=5
     ).points
     print("\nDense (Qdrant):")
     for hit in dense_hits:
          meta = hit.payload["metadata"]
          print(f"  {hit.score:.3f}  {meta['chunk_id']}  {meta['title'][:60]}")

     # BM25: chunks sharing the query's exact words
     bm25 = build_bm25(chunks)
     print("\nBM25:")
     bm25_hits = bm25_search(query, bm25, chunks, k=5)
     for chunk, score in bm25_hits:
          print(f"  {score:6.2f}  {chunk.metadata['chunk_id']}  {chunk.metadata['title'][:60]}")

     # Hybrid: merge both rankings by chunk_id
     fused = rrf_fuse(
          [hit.payload["metadata"]["chunk_id"] for hit in dense_hits],
          [chunk.metadata["chunk_id"] for chunk, _ in bm25_hits],
     )
     print("\nHybrid (RRF):")
     for chunk_id, score in fused[:5]:
          print(f"  {score:.4f}  {chunk_id}")

     qdrant_client.close()
     
