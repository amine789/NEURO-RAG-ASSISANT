"""Integration tests for specs/retrieval/spec.md: the six test chunks in a real Qdrant.

The collection is written with ingest's own code and the real encoders, so
retrieval is tested against exactly what ingest writes.
"""
import uuid

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import DeleteAlias, DeleteAliasOperation

from helpers import paper
from neuro_rag import config
from neuro_rag.encoders import Encoders
from neuro_rag.ingest.chunk import Chunk
from neuro_rag.ingest.index import alias_target, create_collection, move_alias, write_chunks
from neuro_rag.ingest.parse import Page
from neuro_rag.retrieval.retrieve import RetrievalError, Retriever

pytestmark = pytest.mark.integration

PLACE = "Place cells in the hippocampus fire when the animal is at a specific location."
ZQX = "The protein zqx-17 is required for memory consolidation during sleep."
TEST_CHUNKS = [
    PLACE,
    "Grid cells in the entorhinal cortex fire in a hexagonal pattern across space.",
    ZQX,
    "Sleep spindles coordinate the replay of recent experiences.",
    "Chronic stress shrinks dendrites in the CA3 region.",
    "Exercise increases the birth of new neurons in the dentate gyrus.",
]
DOPAMINE = "Dopamine signals reward prediction errors."


@pytest.fixture(scope="module")
def encoders():
    return Encoders()


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
    """A fresh alias name; its alias and collections are deleted afterwards."""
    name = f"test-{uuid.uuid4().hex[:8]}"
    yield name
    if alias_target(client, name) is not None:
        client.update_collection_aliases(
            change_aliases_operations=[DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=name))]
        )
    for c in client.get_collections().collections:
        if c.name.startswith(f"{name}-v"):
            client.delete_collection(c.name)


def build(client, encoders, alias, texts, version):
    """Write `texts` as chunks (one paper each) into '<alias>-v<version>' and point the alias at it."""
    name = f"{alias}-v{version}"
    chunks = [Chunk(f"PMC{version}{i}-p1-c0", Page(paper(f"PMC{version}{i}"), 1, text), text)
              for i, text in enumerate(texts)]
    create_collection(client, name, config.DENSE_SIZE, {})
    write_chunks(client, name, chunks, encoders)
    move_alias(client, alias, name)


@pytest.fixture
def retriever(client, encoders, alias):
    build(client, encoders, alias, TEST_CHUNKS, version=1)
    return Retriever(client, encoders, alias=alias)


def test_RT1_results_are_sorted_limited_and_complete(retriever):
    results = retriever.retrieve("where are place cells?", k=3)

    assert 0 < len(results) <= 3
    assert [r.score for r in results] == sorted((r.score for r in results), reverse=True)
    for r in results:
        for field in [r.text, r.chunk_id, r.pmcid, r.title, r.citation, r.license, r.page]:
            assert field not in (None, "")


def test_RT2_chunk_found_by_both_searches_appears_once_first(retriever):
    texts = [r.text for r in retriever.retrieve("place cells hippocampus location", k=5)]

    assert texts[0] == PLACE
    assert texts.count(PLACE) == 1


def test_RT3_exact_rare_term_is_found(retriever):
    texts = [r.text for r in retriever.retrieve("what does zqx-17 do?", k=5)]
    assert ZQX in texts


def test_RT5_unknown_words_still_give_results(retriever):
    assert retriever.retrieve("blorf snazzle quimp", k=5)


def test_RT6_same_question_gives_same_results(retriever):
    first = [r.chunk_id for r in retriever.retrieve("where are place cells?", k=5)]
    second = [r.chunk_id for r in retriever.retrieve("where are place cells?", k=5)]
    assert first == second


def test_RT9_new_build_is_picked_up_without_code_change(client, encoders, alias, retriever):
    build(client, encoders, alias, [DOPAMINE], version=2)

    texts = [r.text for r in retriever.retrieve("dopamine reward", k=5)]

    assert texts == [DOPAMINE]


def test_RT12_missing_alias_gives_clear_error(client, encoders):
    retriever = Retriever(client, encoders, alias=f"missing-{uuid.uuid4().hex[:8]}")

    with pytest.raises(RetrievalError, match="not found"):
        retriever.retrieve("where are place cells?")
