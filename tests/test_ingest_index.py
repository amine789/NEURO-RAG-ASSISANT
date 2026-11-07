from types import SimpleNamespace

import numpy as np
import pytest
from qdrant_client import QdrantClient

from neuro_rag.config import CATALOG_PATH, QDRANT_URL, RAW_DIR
from neuro_rag.ingest.build import build
from neuro_rag.ingest.catalog import Paper, load_catalog
from neuro_rag.ingest.chunk import Chunk
from neuro_rag.ingest.index import point_id, recreate_collection, write_chunks

pytestmark = pytest.mark.integration

TEST_COLLECTION = "test_papers"


def fake_embed(texts):
    return [[0.1] * 384 for _ in texts]


def fake_sparse_embed(texts):
    return [SimpleNamespace(indices=np.array([7, 42]), values=np.array([1.5, 0.5])) for _ in texts]


def test_IN12_point_holds_text_vectors_paper_and_page():
    client = QdrantClient(url=QDRANT_URL)
    paper = Paper(
        pmcid="PMC6226095",
        title="m6A facilitates hippocampus-dependent learning and memory through Ythdf1",
        citation="Nature. Author manuscript; Available in PMC 2019 Apr 30.",
        license="TDM",
    )
    chunk = Chunk("PMC6226095-p2-c0", "PMC6226095", 2, "m6A is abundant in the nervous system.")
    recreate_collection(client, TEST_COLLECTION)

    written = write_chunks(client, [chunk], {"PMC6226095": paper}, fake_embed, fake_sparse_embed, TEST_COLLECTION)

    [point] = client.retrieve(TEST_COLLECTION, [point_id("PMC6226095-p2-c0")], with_vectors=True)
    assert written == 1
    assert len(point.vector["dense"]) == 384
    assert point.vector["bm25"].indices == [7, 42]
    assert point.vector["bm25"].values == [1.5, 0.5]
    assert point.payload == {
        "chunk_id": "PMC6226095-p2-c0",
        "pmcid": "PMC6226095",
        "page": 2,
        "title": "m6A facilitates hippocampus-dependent learning and memory through Ythdf1",
        "citation": "Nature. Author manuscript; Available in PMC 2019 Apr 30.",
        "license": "TDM",
        "text": "m6A is abundant in the nervous system.",
    }
    client.delete_collection(TEST_COLLECTION)


def test_IN2_build_continues_after_parse_error(tmp_path, capsys):
    client = QdrantClient(url=QDRANT_URL)
    (tmp_path / "PMC0000002.pdf").write_bytes(b"not a pdf")
    (tmp_path / "PMC0000003.pdf").write_bytes(b"%PDF placeholder, already parsed")
    (tmp_path / "PMC0000003.tei.xml").write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div>'
        '<p coords="1,0,0,0,0">Mice were trained for 5 days.</p></div></body></text></TEI>'
    )
    catalog = {pmcid: Paper(pmcid, "Title", "Citation", "CC BY") for pmcid in ["PMC0000002", "PMC0000003"]}

    papers, pages, chunks = build(catalog, tmp_path, client, fake_embed, fake_sparse_embed, TEST_COLLECTION, tei_dir=tmp_path)

    assert capsys.readouterr().out.startswith("can't open PMC0000002.pdf")
    assert (papers, pages, chunks) == (1, 1, 1)
    client.delete_collection(TEST_COLLECTION)


def test_IN13_build_replaces_the_collection():
    client = QdrantClient(url=QDRANT_URL)
    recreate_collection(client, TEST_COLLECTION)
    old = [Chunk(f"OLD-p1-c{n}", "PMC6226095", 1, f"old text {n}") for n in range(10)]
    write_chunks(client, old, {"PMC6226095": Paper("PMC6226095", "T", "C", "L")}, fake_embed, fake_sparse_embed, TEST_COLLECTION)

    papers, pages, chunks = build(load_catalog(CATALOG_PATH), RAW_DIR, client, fake_embed, fake_sparse_embed, TEST_COLLECTION)

    assert (papers, pages, chunks) == (52, 628, 4313)
    assert client.count(TEST_COLLECTION, exact=True).count == 4313
    assert client.retrieve(TEST_COLLECTION, [point_id(c.chunk_id) for c in old]) == []
    client.delete_collection(TEST_COLLECTION)
