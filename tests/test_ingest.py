"""Unit tests for specs/ingest/spec.md: no Qdrant, no models. Named after the criteria."""
import pytest

from helpers import BODY, body_pages, catalog_row, make_pdf, paper, word_count, write_catalog
from neuro_rag.ingest.catalog import load_catalog, select_papers
from neuro_rag.ingest.chunk import _fit, chunk_pages
from neuro_rag.ingest.parse import ParseError, parse_paper


@pytest.fixture
def raw(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    return d


def chunks_of(pages, size=40, overlap=10, max_tokens=60):
    return chunk_pages(pages, word_count, max_tokens, size, overlap)


# Input

def test_IN1_pdf_not_in_catalog_or_not_kept_is_skipped(raw, tmp_path):
    good = make_pdf(raw / "PMC1.pdf", body_pages(1))
    unlisted = make_pdf(raw / "PMC2.pdf", body_pages(1))
    not_kept = make_pdf(raw / "PMC3.pdf", body_pages(1))
    catalog = write_catalog(tmp_path / "c.csv", [catalog_row(good), catalog_row(not_kept, keep="no")])

    selected, skipped = select_papers(raw, load_catalog(catalog))

    assert [p.pmcid for _, p in selected] == ["PMC1"]
    assert {s.name for s in skipped} == {unlisted.name, not_kept.name}
    assert all("catalog" in s.reason for s in skipped)


def test_IN2_checksum_mismatch_is_skipped(raw, tmp_path):
    pdf = make_pdf(raw / "PMC1.pdf", body_pages(1))
    catalog = write_catalog(tmp_path / "c.csv", [catalog_row(pdf, pdf_md5="0" * 32)])

    selected, skipped = select_papers(raw, load_catalog(catalog))

    assert selected == []
    assert [(s.name, s.reason) for s in skipped] == [("PMC1.pdf", "checksum doesn't match the catalog")]


def test_IN3_corrupt_pdf_raises_parse_error(raw):
    bad = raw / "PMC1.pdf"
    bad.write_bytes(b"this is not a pdf")
    with pytest.raises(ParseError):
        parse_paper(bad, paper("PMC1"))


def test_IN3_pdf_without_text_gives_no_pages(raw):
    empty = make_pdf(raw / "PMC1.pdf", [[], []])
    assert parse_paper(empty, paper("PMC1")) == []


# Chunks

def test_IN4_each_chunk_comes_from_one_page_and_keeps_its_number(raw):
    pdf = make_pdf(raw / "PMC1.pdf", body_pages(3))
    pages = parse_paper(pdf, paper("PMC1"))

    chunks = chunks_of(pages)

    assert {c.page.page for c in chunks} == {1, 2, 3}
    for c in chunks:
        assert c.text in c.page.text
        assert c.chunk_id.startswith(f"PMC1-p{c.page.page}-")


def test_IN5_metadata_comes_from_the_catalog_not_the_pdf(raw):
    pdf = make_pdf(raw / "PMC1.pdf", body_pages(1), title="Wrong title from PDF metadata")
    pages = parse_paper(pdf, paper("PMC1", title="Catalog title"))
    assert pages[0].paper.title == "Catalog title"


def test_IN6_headers_footers_and_page_numbers_are_removed(raw):
    pages = [[(20, "Journal of Memory Research 2024"),     # top band
              (100, f"Unique body {i}. {BODY}"),
              (805, f"Page {i} of 4")]                       # bottom band
             for i in range(1, 5)]
    pdf = make_pdf(raw / "PMC1.pdf", pages)

    text = " ".join(p.text for p in parse_paper(pdf, paper("PMC1")))

    assert "Journal of Memory Research" not in text
    assert "of 4" not in text
    assert "Unique body 1" in text


def test_IN6_running_title_below_the_margin_is_removed(raw):
    pages = [[(60, "Raven et al. Cofilin and memory"), (200, f"Unique body {i}. {BODY}")] for i in range(1, 5)]
    pdf = make_pdf(raw / "PMC1.pdf", pages)

    text = " ".join(p.text for p in parse_paper(pdf, paper("PMC1")))

    assert "Raven et al." not in text
    assert "Unique body 4" in text


def test_IN6_reference_list_is_removed(raw):
    pages = [[(100, f"Discussion. {BODY}")],
             [(100, "References"), (130, "1. Smith J. Place cells. J Neurosci. 2001;21:1-10.")],
             [(100, "2. Jones K. Grid cells. Nature. 2005;436:801-6.")]]
    pdf = make_pdf(raw / "PMC1.pdf", pages)

    text = " ".join(p.text for p in parse_paper(pdf, paper("PMC1")))

    assert "Discussion" in text
    assert "Smith J." not in text
    assert "Jones K." not in text


def test_IN6_text_after_references_resumes_at_methods(raw):
    pages = [[(100, "References"), (130, "1. Smith J. Place cells. 2001.")],
             [(100, "Methods"), (130, f"Mice were trained in a water maze. {BODY}")]]
    pdf = make_pdf(raw / "PMC1.pdf", pages)

    text = " ".join(p.text for p in parse_paper(pdf, paper("PMC1")))

    assert "Smith J." not in text
    assert "water maze" in text


def test_IN7_no_piece_exceeds_the_token_limit():
    text = " ".join(["word"] * 500) + " " + "x" * 3000  # long text and one unbreakable "word"
    count = len  # characters as tokens: the long word must be cut too
    pieces = _fit(text, count, 100)
    assert pieces
    assert all(count(p) <= 100 for p in pieces)


def test_IN7_chunks_fit_the_limit(raw):
    pdf = make_pdf(raw / "PMC1.pdf", body_pages(2))
    chunks = chunks_of(parse_paper(pdf, paper("PMC1")), size=40, overlap=10, max_tokens=45)
    assert all(word_count(c.text) <= 45 for c in chunks)


def test_IN8_same_input_gives_same_ids_and_text(raw):
    pdf = make_pdf(raw / "PMC1.pdf", body_pages(3))

    first = chunks_of(parse_paper(pdf, paper("PMC1")))
    second = chunks_of(parse_paper(pdf, paper("PMC1")))

    assert [(c.chunk_id, c.text) for c in first] == [(c.chunk_id, c.text) for c in second]
    assert len({c.chunk_id for c in first}) == len(first)
