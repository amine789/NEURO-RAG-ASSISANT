"""Integration tests for specs/ingest/spec.md against a real Qdrant (docker compose up -d).

Encoders are fakes, so no models are downloaded; each test uses its own alias
and deletes its collections afterwards.
"""
import hashlib
import uuid

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import DeleteAlias, DeleteAliasOperation, SparseVector

from helpers import body_pages, catalog_row, make_pdf, write_catalog
from neuro_rag import config
from neuro_rag.ingest.build import build_index
from neuro_rag.ingest.index import alias_target

pytestmark = pytest.mark.integration


class FakeEncoders:
    """Deterministic stand-ins: dense from a hash, sparse from word counts."""

    max_tokens = 60
    fail = False

    def count_tokens(self, text):
        return len(text.split())

    def dense(self, texts):
        if self.fail:
            raise RuntimeError("encoder failed")
        return [[b / 255 for b in hashlib.sha512(t.encode()).digest()] * 6 for t in texts]  # 64*6 = 384

    def sparse(self, texts):
        out = []
        for t in texts:
            counts = {}
            for w in t.lower().split():
                i = int(hashlib.md5(w.encode()).hexdigest()[:7], 16)
                counts[i] = counts.get(i, 0) + 1.0
            out.append(SparseVector(indices=list(counts), values=list(counts.values())))
        return out

    def describe(self):
        return {"dense_model": "fake-dense", "dense_library": "test", "sparse_model": "fake-sparse",
                "sparse_library": "test"}


@pytest.fixture
def client():
    c = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    try:
        c.get_collections()
    except Exception:
        pytest.skip("Qdrant is not running (docker compose up -d)")
    yield c
    c.close()


@pytest.fixture
def alias(client):
    name = f"test-{uuid.uuid4().hex[:8]}"
    yield name
    if alias_target(client, name) is not None:
        client.update_collection_aliases(
            change_aliases_operations=[DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=name))]
        )
    for c in client.get_collections().collections:
        if c.name.startswith(f"{name}-v"):
            client.delete_collection(c.name)


@pytest.fixture
def corpus(tmp_path):
    """Two good papers, one corrupt file and one empty PDF, all catalogued."""
    raw = tmp_path / "raw"
    raw.mkdir()
    good = [make_pdf(raw / "PMC1.pdf", body_pages(2, "First")), make_pdf(raw / "PMC2.pdf", body_pages(3, "Second"))]
    corrupt = raw / "PMC3.pdf"
    corrupt.write_bytes(b"not a pdf")
    empty = make_pdf(raw / "PMC4.pdf", [[]])
    catalog = write_catalog(tmp_path / "candidates.csv", [catalog_row(p) for p in [*good, corrupt, empty]])
    return raw, catalog


def build(client, alias, corpus, encoders=None, snapshot_dir=None):
    raw, catalog = corpus
    return build_index(client, encoders or FakeEncoders(), raw_dir=raw, catalog_path=catalog, alias=alias,
                       snapshot_dir=snapshot_dir, chunk_size=40, chunk_overlap=10)


def test_IN3_unreadable_and_empty_pdfs_are_reported_and_the_build_continues(client, alias, corpus):
    report = build(client, alias, corpus)

    assert report.papers == 2
    assert {s.name for s in report.skipped} == {"PMC3.pdf", "PMC4.pdf"}
    assert client.count(alias, exact=True).count == report.chunks


def test_IN9_each_point_holds_text_vectors_and_citation_fields(client, alias, corpus):
    build(client, alias, corpus)

    point = client.scroll(alias, limit=1, with_payload=True, with_vectors=True)[0][0]

    for key in ["text", "chunk_id", "pmcid", "title", "citation", "license", "page"]:
        assert point.payload[key] not in (None, "")
    assert len(point.vector["dense"]) == config.DENSE_SIZE
    assert point.vector["sparse"].indices


def test_IN10_each_build_is_a_new_collection_and_the_alias_moves(client, alias, corpus):
    first = build(client, alias, corpus)
    second = build(client, alias, corpus)

    names = {c.name for c in client.get_collections().collections}
    assert first.collection == f"{alias}-v1" and second.collection == f"{alias}-v2"
    assert {first.collection, second.collection} <= names
    assert alias_target(client, alias) == second.collection


def test_IN11_failed_build_leaves_the_alias_on_the_previous_collection(client, alias, corpus):
    first = build(client, alias, corpus)
    broken = FakeEncoders()
    broken.fail = True

    with pytest.raises(RuntimeError):
        build(client, alias, corpus, encoders=broken)

    assert alias_target(client, alias) == first.collection
    assert f"{alias}-v2" not in {c.name for c in client.get_collections().collections}


def test_IN12_collection_records_what_built_it(client, alias, corpus):
    report = build(client, alias, corpus)

    info = client.get_collection(report.collection).config.metadata

    for key in ["catalog_sha256", "chunk_size", "chunk_overlap", "dense_model", "dense_library",
                "sparse_model", "sparse_library"]:
        assert key in info
    assert info["chunk_size"] == 40


def test_IN13_successful_build_writes_a_snapshot_and_reports_counts(client, alias, corpus, tmp_path):
    report = build(client, alias, corpus, snapshot_dir=tmp_path / "snapshots")

    assert report.snapshot.is_file() and report.snapshot.stat().st_size > 0
    assert (report.papers, report.pages) == (2, 5)
    assert report.chunks >= report.pages
    client.delete_snapshot(report.collection, report.snapshot.name)
