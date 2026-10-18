"""The index build job: catalog + PDFs -> new Qdrant collection + snapshot.

Run (with Qdrant up: docker compose up -d):

    python -m neuro_rag.ingest.build
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from qdrant_client import QdrantClient

from neuro_rag import config
from neuro_rag.encoders import Encoders
from neuro_rag.ingest.catalog import Skipped, file_sha256, load_catalog, select_papers
from neuro_rag.ingest.chunk import chunk_pages
from neuro_rag.ingest.index import (
    check_count,
    create_collection,
    move_alias,
    next_collection_name,
    save_snapshot,
    write_chunks,
)
from neuro_rag.ingest.parse import ParseError, parse_paper


@dataclass
class BuildReport:
    collection: str = ""
    papers: int = 0
    pages: int = 0
    chunks: int = 0
    skipped: list[Skipped] = field(default_factory=list)
    snapshot: Path | None = None


def build_index(
    client: QdrantClient,
    encoders: Encoders,
    raw_dir: Path = config.RAW_DIR,
    catalog_path: Path = config.CATALOG_PATH,
    alias: str = config.COLLECTION_ALIAS,
    snapshot_dir: Path | None = config.SNAPSHOT_DIR,
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> BuildReport:
    """Build a new collection and move the alias to it only once it is complete (IN-10, IN-11).

    snapshot_dir=None skips the snapshot (tests).
    """
    report = BuildReport()
    selected, report.skipped = select_papers(raw_dir, load_catalog(catalog_path))

    pages = []
    for path, paper in selected:
        try:
            paper_pages = parse_paper(path, paper)
        except ParseError as e:
            report.skipped.append(Skipped(path.name, str(e)))
            continue
        if not paper_pages:
            report.skipped.append(Skipped(path.name, "no extractable text (scanned PDF?)"))
            continue
        pages += paper_pages
        report.papers += 1
    report.pages = len(pages)

    chunks = chunk_pages(pages, encoders.count_tokens, encoders.max_tokens, chunk_size, chunk_overlap)
    report.chunks = len(chunks)
    if not chunks:
        raise RuntimeError("no chunks to index; nothing was built")

    build_info = {
        "catalog_sha256": file_sha256(catalog_path),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        **encoders.describe(),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    report.collection = next_collection_name(client, alias)
    create_collection(client, report.collection, config.DENSE_SIZE, build_info)
    try:
        write_chunks(client, report.collection, chunks, encoders)
        check_count(client, report.collection, len(chunks))
    except Exception:
        client.delete_collection(report.collection)  # the alias was never moved (IN-11)
        raise
    move_alias(client, alias, report.collection)

    if snapshot_dir is not None:
        report.snapshot = save_snapshot(client, report.collection, config.QDRANT_URL,
                                        config.QDRANT_API_KEY, snapshot_dir)
    return report


def main() -> None:
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    try:
        report = build_index(client, Encoders())
    finally:
        client.close()
    for s in report.skipped:
        print(f"skipped {s.name}: {s.reason}")
    print(f"built {report.collection}: {report.papers} papers, {report.pages} pages, {report.chunks} chunks")
    print(f"alias {config.COLLECTION_ALIAS!r} -> {report.collection}")
    print(f"snapshot: {report.snapshot}")


if __name__ == "__main__":
    main()
