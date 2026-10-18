"""Small generated corpora for tests: PDFs made with PyMuPDF plus a matching catalog."""
import csv
import hashlib
from pathlib import Path

import pymupdf

from neuro_rag.ingest.catalog import Paper

CATALOG_FIELDS = ["keep", "pmcid", "title", "citation", "license", "pdf_url", "pdf_md5"]
BODY = (
    "Place cells in the hippocampus fire when the animal occupies a specific location. "
    "Their activity is thought to support spatial memory and navigation in rodents. "
)


def make_pdf(path: Path, pages: list[list[tuple[float, str]]], title: str = "") -> Path:
    """Each page is a list of (y position, text). Text below y=50 or above 792 lands in the margin bands."""
    doc = pymupdf.open()
    for blocks in pages:
        page = doc.new_page(width=595, height=842)
        for y, text in blocks:
            page.insert_textbox(pymupdf.Rect(50, y, 545, y + 200), text, fontsize=10)
    if title:
        doc.set_metadata({"title": title})
    doc.save(path)
    doc.close()
    return path


def body_pages(n: int, label: str = "") -> list[list[tuple[float, str]]]:
    """n pages of plain body text; each page mentions its own number so its text is unique."""
    return [[(100, f"{label} Page marker {i}. {BODY * 3}")] for i in range(1, n + 1)]


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def write_catalog(path: Path, rows: list[dict]) -> Path:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CATALOG_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({"keep": "yes", "title": f"Title of {row['pmcid']}", "citation": f"Citation of {row['pmcid']}",
                             "license": "CC BY", "pdf_url": "", **row})
    return path


def catalog_row(pdf: Path, **overrides) -> dict:
    """A keep=yes row for this PDF, with its real checksum."""
    return {"pmcid": pdf.stem, "pdf_md5": md5(pdf), **overrides}


def paper(pmcid: str = "PMC1", title: str = "Catalog title") -> Paper:
    return Paper(pmcid, title, "Citation", "CC BY", "")


def word_count(text: str) -> int:
    """A stand-in tokenizer for unit tests: one token per word."""
    return len(text.split())
