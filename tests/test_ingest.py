from pathlib import Path

import pytest

from neuro_rag.ingest.catalog import Paper, select_papers
from neuro_rag.ingest.chunk import TokenCounter, chunk_page
from neuro_rag.ingest.index import point_id
from neuro_rag.ingest.parse import Page, ParseError, parse_pdf


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


TEI_HEAD = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text>'


def write_tei(folder, pmcid, inner):
    (folder / f"{pmcid}.tei.xml").write_text(TEI_HEAD + inner + "</text></TEI>", encoding="utf-8")


@pytest.mark.integration
def test_IN2_unreadable_pdf_raises_parse_error(tmp_path):
    bad = tmp_path / "PMC0000002.pdf"
    bad.write_bytes(b"not a pdf")

    with pytest.raises(ParseError, match=r"^can't open PMC0000002\.pdf"):
        parse_pdf(bad, "PMC0000002", tei_dir=tmp_path)


def test_IN3_body_and_captions_kept_references_and_back_matter_dropped(tmp_path):
    write_tei(tmp_path, "PMC0000003", """
        <front><abstract><p coords="1,0,0,0,0">Sleep helps memory.</p></abstract></front>
        <body><div>
            <head coords="2,0,0,0,0">Results</head>
            <p coords="2,0,0,0,0">Mice were trained for 5 days.</p>
            <figure coords="3,0,0,0,0"><head>Figure 1</head><label>0 20 40</label>
                <figDesc>Ythdf1-KO mice learn more slowly.</figDesc></figure>
        </div></body>
        <back><div type="acknowledgement"><p>We thank the lab.</p></div>
            <listBibl><biblStruct><title>Smith J. Neuron 2019</title></biblStruct></listBibl></back>""")

    pages = parse_pdf(tmp_path / "PMC0000003.pdf", "PMC0000003", tei_dir=tmp_path)

    assert pages == [
        Page("PMC0000003", 1, "Sleep helps memory."),
        Page("PMC0000003", 2, "Results Mice were trained for 5 days."),
        Page("PMC0000003", 3, "Ythdf1-KO mice learn more slowly."),
    ]


def test_IN4_page_from_coordinates(tmp_path):
    write_tei(tmp_path, "PMC0000004", """
        <body><div>
            <p coords="3,0,0,0,0;4,0,0,0,0">Starts on page 3.</p>
            <head>No coordinates.</head>
            <p coords="5,0,0,0,0">On page 5.</p>
        </div></body>""")

    pages = parse_pdf(tmp_path / "PMC0000004.pdf", "PMC0000004", tei_dir=tmp_path)

    assert pages == [
        Page("PMC0000004", 3, "Starts on page 3. No coordinates."),
        Page("PMC0000004", 5, "On page 5."),
    ]


def test_IN5_whitespace_squeezed_inline_tags_kept(tmp_path):
    write_tei(tmp_path, "PMC0000005", """
        <body><div><p coords="1,0,0,0,0">Learning   requires
            protein <ref type="bibr">[1]</ref> synthesis.</p></div></body>""")

    pages = parse_pdf(tmp_path / "PMC0000005.pdf", "PMC0000005", tei_dir=tmp_path)

    assert pages == [Page("PMC0000005", 1, "Learning requires protein [1] synthesis.")]


def test_IN6_saved_grobid_output_is_reused(tmp_path):
    write_tei(tmp_path, "PMC0000006", '<body><div><p coords="1,0,0,0,0">Saved.</p></div></body>')

    pages = parse_pdf(tmp_path / "PMC0000006.pdf", "PMC0000006", tei_dir=tmp_path)

    assert pages == [Page("PMC0000006", 1, "Saved.")]


def test_IN7_no_kept_text_raises_parse_error(tmp_path):
    write_tei(tmp_path, "PMC0000007", "<back><listBibl><biblStruct><title>Only references</title></biblStruct></listBibl></back>")

    with pytest.raises(ParseError, match=r"^no text in PMC0000007\.pdf"):
        parse_pdf(tmp_path / "PMC0000007.pdf", "PMC0000007", tei_dir=tmp_path)


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
