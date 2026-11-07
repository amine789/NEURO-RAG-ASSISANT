import sys
import time
from pathlib import Path

from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client import QdrantClient

from neuro_rag.config import CATALOG_PATH, COLLECTION, EMBED_MODEL, QDRANT_URL, RAW_DIR, TEI_DIR, SPARSE_MODEL
from neuro_rag.ingest.catalog import Paper, load_catalog, select_papers
from neuro_rag.ingest.chunk import TokenCounter, chunk_page
from neuro_rag.ingest.index import recreate_collection, write_chunks
from neuro_rag.ingest.parse import ParseError, parse_pdf


def build(
    catalog: dict[str, Paper], raw_dir: Path, client: QdrantClient, embed, sparse_embed, name: str = COLLECTION, tei_dir: Path = TEI_DIR
) -> tuple[int, int, int]:
    papers = select_papers(raw_dir, catalog)

    pages = []
    for path, paper in papers:
        try:
            pages += parse_pdf(path, paper.pmcid, tei_dir)
        except ParseError as e:
            print(e)

    count = TokenCounter()
    chunks = []
    for page in pages:
        chunks += chunk_page(page, count)

    if not chunks:
        print("nothing to build")
        sys.exit(1)

    recreate_collection(client, name)
    write_chunks(client, chunks, catalog, embed, sparse_embed, name)

    points = client.count(name, exact=True).count
    if points != len(chunks):
        print(f"wrote {len(chunks)} chunks but the collection holds {points} points")
        sys.exit(1)

    return len({page.pmcid for page in pages}), len(pages), len(chunks)


def main():
    start = time.time()
    client = QdrantClient(url=QDRANT_URL)
    papers, pages, chunks = build(load_catalog(CATALOG_PATH), RAW_DIR, client, TextEmbedding(EMBED_MODEL).embed, SparseTextEmbedding(SPARSE_MODEL).embed)
    print(f'built {papers} papers, {pages} pages, {chunks} chunks into "{COLLECTION}" in {time.time() - start:.1f} s')


if __name__ == "__main__":
    main()
