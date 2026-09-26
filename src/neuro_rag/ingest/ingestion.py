import csv
import json
import re
from collections import Counter
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import pymupdf
from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CATALOG_PATH = PROJECT_ROOT / "data" / "candidates.csv"  # written by collect_corpus.py
PAGES_PATH = PROJECT_ROOT / "data" / "pages.jsonl"
LIGATURES = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl"}
REFERENCES = re.compile(r"(\d+\.?\s*)?(references|bibliography|literature cited)\b", re.I)
# Sections that can follow a reference list (e.g. Nature: References -> Methods -> Extended Data).
# Not "supplementary": in Frontiers papers that heading sits inside the reference list.
RESUME = re.compile(r"(\d+\.?\s*)?(methods|online methods|materials and methods|extended data)\b", re.I)
CAPTION = re.compile(r"^\s*(fig\.|figure|table|tab\.|scheme)\s*S?\d+", re.I)


def is_caption(text):
    """True for blocks like 'Figure 3: ...', 'Fig. 2. ...', 'TABLE 1 ...', 'Table S4 ...'."""
    return bool(CAPTION.match(text))


def clean_block(text):
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    text = re.sub(r"(\w)-\n([a-z])", r"\1\2", text)  # re-join words hyphenated at line ends
    text = re.sub(r"\s*\n\s*", " ", text)             # lines inside a block -> one paragraph
    return re.sub(r"\s+", " ", text).strip()


def skip_regions(page):
    """Areas to ignore: detected tables and embedded images (text inside them is noise)."""
    regions = [pymupdf.Rect(t.bbox) for t in page.find_tables().tables]
    regions += [pymupdf.Rect(img["bbox"]) for img in page.get_image_info()]
    return regions

def text_blocks(page):
    """Text blocks with their lines, as PyMuPDF's dict output (no image data)."""
    return [b for b in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"] if b["type"] == 0]


def line_text(line):
    return "".join(s["text"] for s in line["spans"])


def body_font_size(doc):
    """Most common font size in the paper, weighted by characters (superscripts don't count much)."""
    sizes = Counter()
    for page in doc:
        for block in text_blocks(page):
            for line in block["lines"]:
                for s in line["spans"]:
                    sizes[round(s["size"], 1)] += len(s["text"].strip())
    return sizes.most_common(1)[0][0] if sizes else 0


def is_heading(line, body_size):
    """Short line set apart by style: every span bold, or clearly larger than body text."""
    text = line_text(line).strip()
    if len(text) > 60 or sum(c.isalpha() for c in text) < 3:  # also skips panel labels "A", "B"
        return False
    spans = [s for s in line["spans"] if s["text"].strip()]
    bold = all(s["flags"] & 16 or "bold" in s["font"].lower() for s in spans)
    larger = min(s["size"] for s in spans) > body_size * 1.15
    return bold or larger


def block_paragraphs(block, body_size):
    """Split a block into paragraphs, giving each heading line a paragraph of its own."""
    paragraphs, current = [], []
    for line in block["lines"]:
        if is_heading(line, body_size):
            paragraphs += ["\n".join(current), line_text(line)]
            current = []
        else:
            current.append(line_text(line))
    paragraphs.append("\n".join(current))
    return [clean_block(p) for p in paragraphs]


def extract_page(page, body_size, margin=50):
    w, h = page.rect.width, page.rect.height
    regions = skip_regions(page)
    blocks = [b for b in text_blocks(page)
              if b["bbox"][3] > margin and b["bbox"][1] < h - margin]  # drop blocks entirely in header/footer bands
    blocks = [b for b in blocks
              if is_caption("\n".join(line_text(l) for l in b["lines"]))
              or not any(pymupdf.Rect(b["bbox"]).intersects(r) for r in regions)]
    blocks.sort(key=lambda b: (b["bbox"][0] >= w / 2 - 10, b["bbox"][1]))  # left column, then right
    paragraphs = [p for b in blocks for p in block_paragraphs(b, body_size)]
    return "\n\n".join(p for p in paragraphs if p)

def load_catalog(csv_path):
    """pmcid -> row of candidates.csv (title, citation, license, ...)."""
    with open(csv_path, newline="") as f:
        return {row["pmcid"]: row for row in csv.DictReader(f)}


def load_paper(path, info):
    """`info` is the paper's candidates.csv row; PDF metadata titles are often empty or junk."""
    doc = pymupdf.open(path)
    meta = {k: info[k] for k in ("pmcid", "title", "citation", "license")}
    body_size = body_font_size(doc)
    pages = []
    in_refs = False  # carried across pages: a reference list often spans several
    for page in doc:
        kept = []
        for para in extract_page(page, body_size).split("\n\n"):
            if REFERENCES.match(para):
                in_refs = True        # heading (and any entry glued to it) is dropped
            elif in_refs and (RESUME.match(para) or is_caption(para)):
                in_refs = False       # useful section after the references
            if not in_refs:
                kept.append(para)
        text = "\n\n".join(kept)
        if text.strip():
            pages.append(Document(
                page_content=text,
                metadata={**meta, "source": str(path), "page": page.number + 1},
            ))
    doc.close()
    if not pages:
        print(f"Warning: no text in {path} (scanned PDF? needs OCR)")
    return pages


def load_folder(folder, recursive=False, max_workers=None, catalog_path=CATALOG_PATH):
    """Parse every PDF in `folder`, one paper per worker process (max_workers=1 to debug)."""
    folder = Path(folder).expanduser()
    if not folder.is_dir():
        raise NotADirectoryError(f"{folder} is not a folder")
    pattern = "**/*" if recursive else "*"  # filter below so .PDF files are found too
    paths = sorted(p for p in Path(folder).glob(pattern) if p.suffix.lower() == ".pdf")
    if not paths:
        print(f"No PDFs found in {folder}")
    catalog = load_catalog(catalog_path)
    unknown = [p for p in paths if p.stem not in catalog]
    for p in unknown:
        print(f"Skipping {p.name}: not in {Path(catalog_path).name}, so it can't be cited")
    paths = [p for p in paths if p.stem in catalog]
    docs = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(load_paper, path, catalog[path.stem]): path for path in paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                docs.extend(future.result())
            except Exception as e:
                print(f"Skipping {path.name}: {e}")
    # papers finish in any order; sort so every run gives the same output
    docs.sort(key=lambda d: (d.metadata["source"], d.metadata["page"]))
    return docs


def save_pages(pages, path=PAGES_PATH):
    """One JSON object per line: {"page_content": ..., "metadata": {...}}."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for d in pages:
            f.write(json.dumps({"page_content": d.page_content, "metadata": d.metadata}, ensure_ascii=False) + "\n")


def load_pages(path=PAGES_PATH):
    """Read pages saved by save_pages back as Documents, without touching the PDFs."""
    with Path(path).open(encoding="utf-8") as f:
        return [Document(**json.loads(line)) for line in f if line.strip()]


def main():
    """PDFs in data/raw -> data/pages.jsonl. Run: python -m neuro_rag.ingest.ingestion"""
    pages = load_folder(RAW_DIR)
    save_pages(pages)
    print(f"wrote {len(pages)} pages from {len({d.metadata['pmcid'] for d in pages})} papers "
          f"to {PAGES_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":  # also required by ProcessPoolExecutor on macOS
    main()