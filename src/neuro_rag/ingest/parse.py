import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

PAGE_NUMBER = re.compile(r"^(page\s+)?\d{1,4}(\s+of\s+\d{1,4})?$", re.IGNORECASE)
REFERENCES_START = re.compile(r"^(\d+\.?\s*)?(references|bibliography|literature cited)$", re.IGNORECASE)
REFERENCES_END = re.compile(r"^(\d+\.?\s*)?(methods|online methods)$", re.IGNORECASE)
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


@dataclass(frozen=True)
class Page:
    pmcid: str
    page: int
    text: str


class ParseError(Exception):
    pass


def body_lines(pages: list[list[str]]) -> list[list[str]]:
    repeated = set()
    if len(pages) >= 3:
        counts = Counter(line for page in pages for line in set(page))
        repeated = {line for line, n in counts.items() if n > len(pages) / 2}

    kept = []
    in_references = False
    for page in pages:
        page_kept = []
        for line in page:
            if line in repeated or PAGE_NUMBER.match(line):
                continue
            if REFERENCES_START.match(line):
                in_references = True
                continue
            if in_references:
                if REFERENCES_END.match(line):
                    in_references = False
                else:
                    continue
            page_kept.append(line)
        kept.append(page_kept)
    return kept


def join_lines(lines: list[str]) -> str:
    text = ""
    for line in lines:
        if text == "":
            text = line
        elif len(text) >= 2 and text[-1] == "-" and text[-2].isalnum():
            text += line
        else:
            text += " " + line
    for ligature, letters in LIGATURES.items():
        text = text.replace(ligature, letters)
    return re.sub(r"\s+", " ", text).strip()


def parse_pdf(path: Path, pmcid: str) -> list[Page]:
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        raise ParseError(f"can't open {path.name}: {e}")

    with doc:
        raw = []
        for pdf_page in doc:
            lines = [line.strip() for line in pdf_page.get_text().split("\n")]
            raw.append([line for line in lines if line])

    pages = []
    for number, lines in enumerate(body_lines(raw), start=1):
        text = join_lines(lines)
        if text:
            pages.append(Page(pmcid, number, text))

    if not pages:
        raise ParseError(f"no text in {path.name}")
    return pages
