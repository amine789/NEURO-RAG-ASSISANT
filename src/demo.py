"""End-to-end check: retrieve -> grade -> generate for a few real questions."""
from neuro_rag.ingest.ingestion import load_folder, save_pages
from neuro_rag.indexing.index import get_text_embeddings, ingest_documents, build_bm25, bm25_search, chunk_pages
from neuro_rag.config import RAW_DIR
from neuro_rag.config import QDRANT_PATH, COLLECTION_NAME, VECTOR_SIZE
from neuro_rag.retrieval.fusion import rrf_fuse
from qdrant_client import QdrantClient
from neuro_rag.generation.generate_answer import generate_answer
from neuro_rag.retrieval.retrieve import Retriever
from neuro_rag.grading.grade import grade_retrieval_results


if __name__ == "__main__":
    pages = load_folder(RAW_DIR)
    save_pages(pages)
    chunks = chunk_pages(pages)
    qdrant_client = QdrantClient(path=str(QDRANT_PATH))
    ingest_documents(qdrant_client,
                     COLLECTION_NAME,
                     chunks,
                     VECTOR_SIZE)
    retriever = Retriever(chunks, qdrant_client)
    for question in [
    "Does resistance exercise improve hippocampus-dependent memory?",  # from search_demo
    "What is the role of dopamine in the striatum?"]:
        results = retriever.retrieve(question, k=5)            # [(Document, score), ...]
        graded = grade_retrieval_results(question, results)    # keeps the relevant pairs
        print(f"\n{question}\n{len(graded)}/{len(results)} chunks relevant\n")
        print(generate_answer(question, [doc for doc, _ in graded]))

    qdrant_client.close()

