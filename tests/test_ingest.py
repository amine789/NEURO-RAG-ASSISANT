from pathlib import Path

import pymupdf
import pytest

from neuro_rag.ingest.catalog import Paper, select_papers
from neuro_rag.ingest.chunk import TokenCounter, chunk_page
from neuro_rag.ingest.index import point_id
from neuro_rag.ingest.parse import Page, ParseError, body_lines, join_lines, parse_pdf


def test_IN1_paper_not_kept_is_not_selected(tmp_path):
    kept = [f"PMC{n:07d}" for n in range(1, 53)]
    catalog = {pmcid: Paper(pmcid, f"Title {pmcid}", f"Citation {pmcid}", "CC BY") for pmcid in kept}
    for pmcid in kept:
        (tmp_path / f"{pmcid}.pdf").touch()
    (tmp_path / "PMC6925997.pdf").touch()

    selected = select_papers(tmp_path, catalog)

    assert len(selected) == 52
    for (pdf, paper), pmcid in zip(selected, kept):
        assert pdf.name == f"{pmcid}.pdf"
        assert paper == catalog[pmcid]


def test_IN2_unreadable_pdf_raises_parse_error(tmp_path):
    bad = tmp_path / "PMC0000002.pdf"
    bad.write_bytes(b"not a pdf")

    with pytest.raises(ParseError, match=r"^can't open PMC0000002\.pdf"):
        parse_pdf(bad, "PMC0000002")


def test_IN3_lines_on_most_pages_are_dropped():
    pages = [
        ["Shi et al.", "Hippocampal neurogenesis", "Page one text."],
        ["Shi et al.", "Hippocampal neurogenesis", "Page two text."],
        ["Shi et al.", "Page three text."],
        ["Page four text."],
    ]

    kept = body_lines(pages)

    assert kept == [
        ["Hippocampal neurogenesis", "Page one text."],
        ["Hippocampal neurogenesis", "Page two text."],
        ["Page three text."],
        ["Page four text."],
    ]


def test_IN4_page_numbers_dropped_numbers_in_text_kept():
    pages = [["7", "Page 7 of 37", "In 7 of 9 mice the effect was absent."]]

    kept = body_lines(pages)

    assert kept == [["In 7 of 9 mice the effect was absent."]]


def test_IN5_references_dropped_methods_after_them_kept():
    pages = [
        ["…memory was impaired.", "References", "1. Smith J. Neuron 2019;12:1–9."],
        ["2. Lee K. Cell 2020;3:4–8.", "Methods", "Mice were trained for 5 days."],
    ]
    
    kept = body_lines(pages)

    assert kept == [
        ["…memory was impaired."],
        ["Methods", "Mice were trained for 5 days."],
    ]


def test_IN6_lines_joined_keeping_hyphens():
    lines = ["regulates fates through m6A-", "specific binding proteins and ﬁne", "control of   long-", "term potentiation."]

    text = join_lines(lines)

    assert text == "regulates fates through m6A-specific binding proteins and fine control of long-term potentiation."


def test_IN7_pages_keep_their_numbers(tmp_path):
    pdf = tmp_path / "PMC0000007.pdf"
    doc = pymupdf.open()
    for text in ["Page 1", "Mice were trained for 5 days.", "Memory was impaired."]:
        doc.new_page().insert_text((72, 72), text)
    doc.save(pdf)
    doc.close()

    pages = parse_pdf(pdf, "PMC0000007")

    assert pages == [
        Page("PMC0000007", 2, "Mice were trained for 5 days."),
        Page("PMC0000007", 3, "Memory was impaired."),
    ]


def test_IN8_tokenizer_counts_real_tokens():
    count = TokenCounter()

    short = "m6A is abundant in the nervous system and modulates various neural functions6–11."
    long = (
        "Here we show that, through its binding protein Ythdf1, m6A promotes protein synthesis of target "
        "transcripts in response to neuronal stimuli in the adult mouse hippocampus, thereby facilitating "
        "learning and memory."
    )

    assert count(short) == 19
    assert count(long) == 46


def test_IN9_chunks_packed_from_sentences_with_overlap():
    tokens = [112, 50, 19, 35, 46, 43, 75, 31, 37, 32]
    sentences = [f"Sentence {i}." for i in range(len(tokens))]
    count = dict(zip(sentences, tokens)).get
    page = Page("PMC6226095", 2, " ".join(sentences))

    chunks = chunk_page(page, count, size=200, carry=50)

    assert [c.chunk_id for c in chunks[:3]] == ["PMC6226095-p2-c0", "PMC6226095-p2-c1", "PMC6226095-p2-c2"]
    assert chunks[0].text == " ".join(sentences[0:3])
    assert chunks[1].text == " ".join(sentences[2:6])
    assert chunks[2].text == " ".join(sentences[5:9])


def test_IN10_long_sentence_cut_between_words():
    count = TokenCounter()
    sentence = (
        "Here we show that, through its binding protein Ythdf1, m6A promotes protein synthesis of target "
        "transcripts in response to neuronal stimuli in the adult mouse hippocampus, thereby facilitating "
        "learning and memory."
    )

    chunks = chunk_page(Page("PMC6226095", 2, sentence), count, size=20)

    assert [c.text for c in chunks] == [
        "Here we show that, through its binding protein Ythdf1, m6A promotes protein synthesis",
        "of target transcripts in response to neuronal stimuli in the adult mouse hippocampus,",
        "thereby facilitating learning and memory.",
    ]


def test_IN11_same_pdf_same_chunks_and_ids():
    count = TokenCounter()

    def build():
        pages = parse_pdf(Path("data/raw/PMC6226095.pdf"), "PMC6226095")
        return [chunk for page in pages for chunk in chunk_page(page, count)]

    first, second = build(), build()

    assert [(c.chunk_id, c.text) for c in first] == [(c.chunk_id, c.text) for c in second]
    assert point_id("PMC6226095-p2-c0") == "002c0971-edeb-5036-86b6-779a589dc715"
