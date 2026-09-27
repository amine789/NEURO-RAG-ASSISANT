from neuro_rag.ingest.ingestion import load_folder, save_pages
from neuro_rag.indexing.index import ingest_documents, build_bm25, bm25_search, chunk_pages
from neuro_rag.config import RAW_DIR
from neuro_rag.config import QDRANT_PATH, COLLECTION_NAME, VECTOR_SIZE
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
     qdrant_client.close()
        