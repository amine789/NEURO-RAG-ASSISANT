"""IN-7 on the real corpus with the real tokenizer. Skipped if data/raw is missing.

Slow (parses all 52 papers): pytest tests/test_ingest_corpus.py
"""
import pytest

from neuro_rag import config
from neuro_rag.encoders import Encoders
from neuro_rag.ingest.catalog import load_catalog, select_papers
from neuro_rag.ingest.chunk import chunk_pages
from neuro_rag.ingest.parse import parse_paper

pytestmark = pytest.mark.skipif(not config.RAW_DIR.is_dir(), reason="no corpus in data/raw")


def test_IN7_every_real_chunk_fits_the_embedding_model():
    encoders = Encoders()
    selected, _ = select_papers(config.RAW_DIR, load_catalog(config.CATALOG_PATH))
    pages = [p for path, paper in selected for p in parse_paper(path, paper)]

    chunks = chunk_pages(pages, encoders.count_tokens, encoders.max_tokens, config.CHUNK_SIZE, config.CHUNK_OVERLAP)

    too_long = [c.chunk_id for c in chunks if encoders.count_tokens(c.text) > encoders.max_tokens]
    assert chunks
    assert too_long == []
