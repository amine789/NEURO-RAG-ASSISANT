import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import requests

from neuro_rag.config import GROBID_URL, TEI_DIR

TEI = "{http://www.tei-c.org/ns/1.0}"


@dataclass(frozen=True)
class Page:
    pmcid: str
    page: int
    text: str


class ParseError(Exception):
    pass


def grobid_tei(path: Path, tei_dir: Path = TEI_DIR) -> Path:
    tei = tei_dir / f"{path.stem}.tei.xml"
    if tei.exists() and tei.stat().st_size > 0:
        return tei
    with open(path, "rb") as f:
        response = requests.post(
            f"{GROBID_URL}/api/processFulltextDocument",
            files={"input": f},
            data={"teiCoordinates": ["p", "head", "figure"]},
            timeout=600,
        )
    if response.status_code != 200:
        raise ParseError(f"can't open {path.name}: GROBID returned {response.status_code} {response.text[:100]}")
    tei_dir.mkdir(parents=True, exist_ok=True)
    tei.write_text(response.text, encoding="utf-8")
    return tei


def kept_elements(root: ET.Element) -> list[tuple[ET.Element, str | None]]:
    kept = []
    for abstract in root.iter(TEI + "abstract"):
        kept += [(p, p.get("coords")) for p in abstract.iter(TEI + "p")]

    def walk(element):
        for child in element:
            if child.tag == TEI + "figure":
                kept.extend((d, child.get("coords")) for d in child.iter(TEI + "figDesc"))
            elif child.tag in (TEI + "p", TEI + "head"):
                kept.append((child, child.get("coords")))
            else:
                walk(child)

    for body in root.iter(TEI + "body"):
        walk(body)
    return kept


def tei_pages(tei: Path, pmcid: str) -> list[Page]:
    texts = {}
    page = 1
    for element, coords in kept_elements(ET.parse(tei).getroot()):
        if coords:
            page = int(coords.split(",")[0])
        text = re.sub(r"\s+", " ", "".join(element.itertext())).strip()
        if text:
            texts.setdefault(page, []).append(text)
    return [Page(pmcid, number, " ".join(parts)) for number, parts in sorted(texts.items())]


def parse_pdf(path: Path, pmcid: str, tei_dir: Path = TEI_DIR) -> list[Page]:
    pages = tei_pages(grobid_tei(path, tei_dir), pmcid)
    if not pages:
        raise ParseError(f"no text in {path.name}")
    return pages
