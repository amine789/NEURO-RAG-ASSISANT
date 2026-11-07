import pytest
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector

from neuro_rag.config import COLLECTION, EMBED_MODEL, QDRANT_URL, SPARSE_MODEL
from neuro_rag.ingest.index import point_id
from neuro_rag.retrieval.search import search

Q01 = "How does m6A RNA methylation support hippocampus-dependent learning and memory?"
KEYWORDS = "Ythdf1 Mettl3 knockdown"


class Counter:
    """Stands in for embed, sparse_embed or the client, and counts calls."""

    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return []

    def query_points(self, *args, **kwargs):
        self.calls += 1
        return []


@pytest.fixture(scope="module")
def real():
    return (QdrantClient(url=QDRANT_URL), TextEmbedding(EMBED_MODEL).embed, SparseTextEmbedding(SPARSE_MODEL).query_embed)


def scores_never_increase(hits):
    return all(a.score >= b.score for a, b in zip(hits, hits[1:]))


@pytest.mark.integration
def test_SE1_dense_top_5_best_first(real):
    hits = search(Q01, *real, mode="dense")

    assert len(hits) == 5
    assert scores_never_increase(hits)
    assert hits[0].chunk_id == "PMC6226095-p6-c1"
    assert 0.76 <= hits[0].score <= 0.77


@pytest.mark.integration
def test_SE2_hit_carries_citation_fields(real):
    first = search(Q01, *real, mode="dense")[0]

    assert first.pmcid == "PMC6226095"
    assert first.page == 6
    assert first.title == "m6A facilitates hippocampus-dependent learning and memory through Ythdf1"
    assert first.citation == "Nature. Author manuscript; Available in PMC 2019 Apr 30."
    assert first.license == "TDM"
    assert first.text.startswith("4i; Supplementary Table 1, 6), suggesting that more binding of Ythdf1")


@pytest.mark.integration
def test_SE3_chunk_text_finds_itself(real):
    client = real[0]
    [point] = client.retrieve(COLLECTION, [point_id("PMC6226095-p2-c0")], with_payload=True)

    first = search(point.payload["text"], *real, mode="dense")[0]

    assert first.chunk_id == "PMC6226095-p2-c0"
    assert first.score >= 0.99


def test_SE4_empty_question_refused():
    embed, sparse_embed, client = Counter(), Counter(), Counter()

    with pytest.raises(ValueError, match="^empty question$"):
        search("   ", client, embed, sparse_embed)

    assert (embed.calls, sparse_embed.calls, client.calls) == (0, 0, 0)


@pytest.mark.integration
def test_SE5_k_sets_number_of_hits(real):
    five = search(Q01, *real, k=5, mode="dense")
    twenty = search(Q01, *real, k=20, mode="dense")

    assert len(twenty) == 20
    assert [h.chunk_id for h in twenty[:5]] == [h.chunk_id for h in five]


@pytest.mark.integration
def test_SE6_off_topic_still_returns_hits(real):
    hits = search("What's a good recipe for sourdough bread?", *real, mode="dense")

    assert len(hits) == 5
    assert hits[0].score < 0.30


@pytest.mark.integration
def test_SE7_hybrid_hits_come_from_either_list(real):
    client, embed, sparse_embed = real
    dense = list(embed([KEYWORDS]))[0].tolist()
    s = list(sparse_embed([KEYWORDS]))[0]
    sparse = SparseVector(indices=s.indices.tolist(), values=s.values.tolist())
    dense_top = client.query_points(COLLECTION, query=dense, using="dense", limit=20, with_payload=True).points
    bm25_top = client.query_points(COLLECTION, query=sparse, using="bm25", limit=20, with_payload=True).points
    candidates = {p.payload["chunk_id"] for p in dense_top + bm25_top}

    hits = search(KEYWORDS, *real, mode="hybrid")

    assert len(hits) == 5
    assert len({h.chunk_id for h in hits}) == 5
    assert scores_never_increase(hits)
    assert all(h.chunk_id in candidates for h in hits)


@pytest.mark.integration
def test_SE8_hybrid_finds_rare_term(real):
    hits = search(KEYWORDS, *real, mode="hybrid")

    assert any("Mettl3" in h.text for h in hits)


def test_SE9_unknown_mode_refused():
    embed, sparse_embed, client = Counter(), Counter(), Counter()

    with pytest.raises(ValueError, match="^unknown mode: sparse$"):
        search("Does sleep help memory?", client, embed, sparse_embed, mode="sparse")

    assert (embed.calls, sparse_embed.calls, client.calls) == (0, 0, 0)
