"""End-to-end check: run a few real questions through the corrective RAG graph
and print the path each one takes."""
from neuro_rag.ingest.ingestion import load_folder, save_pages
from neuro_rag.indexing.index import ingest_documents, chunk_pages
from neuro_rag.config import RAW_DIR
from neuro_rag.config import QDRANT_PATH, COLLECTION_NAME, VECTOR_SIZE
from qdrant_client import QdrantClient
from neuro_rag.retrieval.retrieve import Retriever
from neuro_rag.orchestration.agent import build_graph, initial_state


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
    app = build_graph(retriever)

    for question in [
        "Does resistance exercise improve hippocampus-dependent memory?",  # well covered by the corpus
        "how does the brain remember places?",  # casual wording: may need a rewrite
        "How do opioids affect the spinal cord?",  # off-topic: should end in web search
    ]:
        print(f"\n{'=' * 80}\n{question}\n")
        # stream() yields one {node: state update} per step, so we can print the path
        for step in app.stream(initial_state(question)):
            node, update = next(iter(step.items()))
            if node == "retrieve":
                print(f"  retrieve    {len(update['documents'])} chunks")
            elif node == "grade":
                print(f"  grade       {len(update['documents'])} relevant")
            elif node == "rewrite":
                print(f"  rewrite     -> {update['query']!r}")
            elif node == "web_search":
                print(f"  web_search  {len(update['documents'])} pages")
            elif node == "generate":
                print(f"\n{update['answer']}")

    qdrant_client.close()
