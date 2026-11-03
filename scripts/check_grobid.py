"""Check GROBID's output (data/tei/) against PMC's own XML (data/pmc_xml/).

    python scripts/check_grobid.py text              # whole-paper recall and precision, all 52 papers
    python scripts/check_grobid.py sections          # up to 3 random matched sections per paper, scored
    python scripts/check_grobid.py show 5            # 5 random matched sections, printed side by side
    python scripts/check_grobid.py show 5 --seed 7   # a different random set

PMC's XML is downloaded into data/pmc_xml/ when missing. GROBID's output is
made by the ingest build (data/tei/).
"""
import argparse
import csv
import random
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

TEI = "{http://www.tei-c.org/ns/1.0}"
CATALOG = Path("data/candidates.csv")
PMC_DIR = Path("data/pmc_xml")
TEI_DIR = Path("data/tei")


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def score(truth, output):
    a, b = Counter(words(truth)), Counter(words(output))
    common = sum((a & b).values())
    return common / max(sum(a.values()), 1), common / max(sum(b.values()), 1)


def text_of(elements):
    return " ".join("".join(e.itertext()) for e in elements)


def kept_papers():
    for row in csv.DictReader(open(CATALOG, encoding="utf-8")):
        if row["keep"].strip().lower() != "yes":
            continue
        pmc = PMC_DIR / f"{row['pmcid']}.pmc.xml"
        if not pmc.exists():
            PMC_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(row["pdf_url"].rsplit(".pdf", 1)[0] + ".xml", pmc)
        yield row["pmcid"], ET.parse(pmc).getroot(), ET.parse(TEI_DIR / f"{row['pmcid']}.tei.xml").getroot()


def pmc_text(root):
    parts = []
    for section in root.findall(".//abstract") + root.findall(".//body"):
        parts += list(section.iter("p")) + list(section.iter("title"))
    return text_of(parts)


def grobid_text(root):
    parts = []
    for section in root.iter(TEI + "abstract"):
        parts += section.iter(TEI + "p")
    for section in root.iter(TEI + "body"):
        parts += list(section.iter(TEI + "p")) + list(section.iter(TEI + "head")) + list(section.iter(TEI + "figDesc"))
    return text_of(parts)


def heading_key(title):
    return " ".join(words(re.sub(r"^[\d.\s]+", "", title)))


def pmc_sections(root):
    sections = {}
    for sec in root.iter("sec"):
        title = sec.find("title")
        text = text_of(sec.findall("p"))
        if title is not None and text.strip():
            sections.setdefault(heading_key("".join(title.itertext())), text)
    return sections


def grobid_sections(root):
    sections = {}
    for body in root.iter(TEI + "body"):
        for div in body.iter(TEI + "div"):
            head = div.find(TEI + "head")
            text = text_of(div.findall(TEI + "p"))
            if head is not None and text.strip():
                sections.setdefault(heading_key("".join(head.itertext())), text)
    return sections


def median(values):
    return sorted(values)[len(values) // 2]


def check_text():
    rows = []
    for pmcid, pmc, tei in kept_papers():
        recall, precision = score(pmc_text(pmc), grobid_text(tei))
        rows.append((pmcid, recall, precision))
        print(f"{pmcid:12} recall {recall:6.1%}  precision {precision:6.1%}")
    print(f"\n{len(rows)} papers: median recall {median([r[1] for r in rows]):.1%}, "
          f"median precision {median([r[2] for r in rows]):.1%}; "
          f"both >= 85%: {sum(r[1] >= 0.85 and r[2] >= 0.85 for r in rows)}")


def matched_sections():
    for pmcid, pmc, tei in kept_papers():
        a, b = pmc_sections(pmc), grobid_sections(tei)
        yield pmcid, a, b, sorted(set(a) & set(b))


def check_sections(seed):
    random.seed(seed)
    rows, found, total = [], 0, 0
    for pmcid, a, b, matched in matched_sections():
        found, total = found + len(matched), total + len(a)
        for title in random.sample(matched, min(3, len(matched))):
            recall, precision = score(a[title], b[title])
            rows.append((recall, precision))
            print(f"{pmcid:12} {title[:40]:40} recall {recall:6.1%}  precision {precision:6.1%}")
    print(f"\nheadings found in both: {found} of {total} PMC headings ({found / total:.0%})")
    print(f"{len(rows)} sampled sections: median recall {median([r[0] for r in rows]):.1%}, "
          f"median precision {median([r[1] for r in rows]):.1%}")


def show(n, seed):
    random.seed(seed)
    pairs = [(pmcid, t, a[t], b[t]) for pmcid, a, b, matched in matched_sections() for t in matched]
    for pmcid, title, truth, output in random.sample(pairs, n):
        recall, precision = score(truth, output)
        print(f"=== {pmcid} | {title} | recall {recall:.0%} precision {precision:.0%}")
        print("PMC:   ", " ".join(truth.split())[:300])
        print("GROBID:", " ".join(output.split())[:300])
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("check", choices=["text", "sections", "show"])
    parser.add_argument("n", nargs="?", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.check == "text":
        check_text()
    elif args.check == "sections":
        check_sections(args.seed)
    else:
        show(args.n, args.seed)
