"""PDF -> clean pages of body text, each with its page number and catalog metadata.

Covers IN-3 (unreadable PDFs), IN-4 (page numbers), IN-5 (catalog metadata) and
IN-6 (no running headers, footers, page numbers or reference lists).
"""
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from neuro_rag.ingest.catalog import Paper

MARGIN = 50  # points; blocks entirely inside the top or bottom band are running headers/footers
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
REFERENCES = re.compile(r"(\d+\.?\s*)?(references|bibliography|literature cited)\b", re.I)
# Sections that can follow a reference list (e.g. Nature: References -> Methods -> Extended Data).
RESUME = re.compile(r"(\d+\.?\s*)?(methods|online methods|materials and methods|extended data)\b", re.I)
CAPTION = re.compile(r"^\s*(fig\.|figure|table|tab\.|scheme)\s*S?\d+", re.I)


class ParseError(Exception):
    """The file couldn't be opened or read as a PDF."""


@dataclass(frozen=True)
class Page:
    paper: Paper
    page: int  # 1-based, as printed in citations
    text: str


def clean_text(text: str) -> str:
    """Fix ligatures, re-join words hyphenated at line ends, collapse whitespace."""
    for ligature, letters in LIGATURES.items():
        text = text.replace(ligature, letters)
    text = re.sub(r"(\w)-\n([a-z])", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip()


def is_caption(text: str) -> bool:
    return bool(CAPTION.match(text))


def _text_blocks(page) -> list[dict]:
    return [b for b in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"] if b["type"] == 0]


def _line_text(line: dict) -> str:
    return "".join(s["text"] for s in line["spans"])


def _body_font_size(doc) -> float:
    """Most common font size, weighted by characters."""
    sizes = Counter()
    for page in doc:
        for block in _text_blocks(page):
            for line in block["lines"]:
                for span in line["spans"]:
                    sizes[round(span["size"], 1)] += len(span["text"].strip())
    return sizes.most_common(1)[0][0] if sizes else 0


def _is_heading(line: dict, body_size: float) -> bool:
    """Short line set apart by style: all bold, or clearly larger than body text."""
    text = _line_text(line).strip()
    if len(text) > 60 or sum(c.isalpha() for c in text) < 3:
        return False
    spans = [s for s in line["spans"] if s["text"].strip()]
    bold = all(s["flags"] & 16 or "bold" in s["font"].lower() for s in spans)
    larger = min(s["size"] for s in spans) > body_size * 1.15
    return bold or larger


def _paragraphs(block: dict, body_size: float) -> list[str]:
    """A block's text, with each heading line as its own paragraph (so chunks split at sections)."""
    paragraphs, current = [], []
    for line in block["lines"]:
        if _is_heading(line, body_size):
            paragraphs += ["\n".join(current), _line_text(line)]
            current = []
        else:
            current.append(_line_text(line))
    paragraphs.append("\n".join(current))
    return [p for p in (clean_text(p) for p in paragraphs) if p]


def _page_paragraphs(page, body_size: float) -> list[str]:
    """Body paragraphs in reading order: no header/footer bands, no text inside tables or images."""
    width, height = page.rect.width, page.rect.height
    skip = [pymupdf.Rect(t.bbox) for t in page.find_tables().tables]
    skip += [pymupdf.Rect(img["bbox"]) for img in page.get_image_info()]
    blocks = [b for b in _text_blocks(page) if b["bbox"][3] > MARGIN and b["bbox"][1] < height - MARGIN]
    blocks = [
        b for b in blocks
        if is_caption("\n".join(_line_text(l) for l in b["lines"]))
        or not any(pymupdf.Rect(b["bbox"]).intersects(r) for r in skip)
    ]
    blocks.sort(key=lambda b: (b["bbox"][0] >= width / 2 - 10, b["bbox"][1]))  # left column, then right
    return [p for b in blocks for p in _paragraphs(b, body_size)]


def _repeated(pages: list[list[str]]) -> set[str]:
    """Paragraphs found on more than half the pages (running titles that sit below the margin band)."""
    if len(pages) < 3:
        return set()
    counts = Counter(p for paragraphs in pages for p in set(paragraphs))
    return {p for p, n in counts.items() if n > len(pages) / 2}


def parse_paper(path: Path, paper: Paper) -> list[Page]:
    """Clean pages of one paper; pages left with no text are dropped. Raises ParseError if unreadable."""
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        raise ParseError(f"can't open {path.name}: {e}") from e
    with doc:
        body_size = _body_font_size(doc)
        raw = [_page_paragraphs(page, body_size) for page in doc]
    repeated = _repeated(raw)
    pages, in_refs = [], False  # a reference list often spans several pages
    for number, paragraphs in enumerate(raw, start=1):
        kept = []
        for para in paragraphs:
            if para in repeated:
                continue
            if REFERENCES.match(para):
                in_refs = True
            elif in_refs and (RESUME.match(para) or is_caption(para)):
                in_refs = False
            if not in_refs:
                kept.append(para)
        text = "\n\n".join(kept)
        if text.strip():
            pages.append(Page(paper, number, text))
    return pages
