import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paper:
    pmcid: str
    title: str
    citation: str
    license: str


def load_catalog(path: Path) -> dict[str, Paper]:
    catalog = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["keep"].strip().lower() != "yes":
                continue
            pmcid = row["pmcid"].strip()
            catalog[pmcid] = Paper(
                pmcid=pmcid,
                title=row["title"].strip(),
                citation=row["citation"].strip(),
                license=row["license"].strip(),
            )
    return catalog


def select_papers(raw_dir: Path, catalog: dict[str, Paper]) -> list[tuple[Path, Paper]]:
    selected = []
    for pdf in sorted(raw_dir.glob("*.pdf")):
        if pdf.stem in catalog:
            selected.append((pdf, catalog[pdf.stem]))
    return selected
