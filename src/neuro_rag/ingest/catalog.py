"""Which PDFs get built: only catalogued, kept papers whose file is intact (IN-1, IN-2)."""
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paper:
    """One catalog row: the source of truth for citing a paper (IN-5)."""

    pmcid: str
    title: str
    citation: str
    license: str
    pdf_md5: str


@dataclass(frozen=True)
class Skipped:
    name: str
    reason: str


def load_catalog(path: Path) -> dict[str, Paper]:
    """pmcid -> Paper, for rows marked keep=yes."""
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["pmcid"]: Paper(row["pmcid"], row["title"], row["citation"], row["license"], row["pdf_md5"])
            for row in csv.DictReader(f)
            if row["keep"].strip().lower() == "yes"
        }


def file_md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_papers(raw_dir: Path, catalog: dict[str, Paper]) -> tuple[list[tuple[Path, Paper]], list[Skipped]]:
    """Split the PDFs in raw_dir into those to build and those skipped, with the reason."""
    pdfs = sorted(p for p in raw_dir.iterdir() if p.suffix.lower() == ".pdf")
    selected, skipped = [], []
    for path in pdfs:
        paper = catalog.get(path.stem)
        if paper is None:
            skipped.append(Skipped(path.name, "not in the catalog with keep=yes, so it can't be cited"))
        elif file_md5(path) != paper.pdf_md5:
            skipped.append(Skipped(path.name, "checksum doesn't match the catalog"))
        else:
            selected.append((path, paper))
    found = {path.stem for path in pdfs}
    for pmcid in sorted(set(catalog) - found):
        skipped.append(Skipped(f"{pmcid}.pdf", "in the catalog but the PDF is missing"))
    return selected, skipped
