"""G1's training papers (row 9, CR-1): 40 new open-access hippocampus papers, none in the corpus.

Searches PubMed Central with NCBI's E-utilities, keeps CC BY / CC BY-NC papers with a PDF in
the PMC open-access bucket, skips every PMCID already in data/candidates.csv, downloads the
PDFs to data/grader/raw/ and writes data/grader/catalog.csv in candidates.csv's format.

    python scripts/fetch_grader_papers.py
"""
import csv
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from neuro_rag.config import CATALOG_PATH, DATA_DIR

GRADER_DIR = DATA_DIR / "grader"             # gitignored, like all of data/
RAW_DIR = GRADER_DIR / "raw"                 # the downloaded PDFs
OUT_CATALOG = GRADER_DIR / "catalog.csv"     # same columns as data/candidates.csv
COLUMNS = ["keep", "pmcid", "title", "citation", "license", "pdf_url", "pdf_md5"]

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
BUCKET = "https://pmc-oa-opendata.s3.amazonaws.com"   # PMC's open-access bucket: metadata and PDFs, as in candidates.csv

# hippocampus and memory in the title or abstract, open access, 2015 or later, no reviews
# (reviews summarise other papers: poor training chunks); as in the original scripts/collect_corpus.py
QUERY = ('hippocampus[Title/Abstract] AND memory[Title/Abstract] AND "open access"[filter] '
         'AND 2015:3000[pdat] NOT review[title]')
SEARCH_MAX = 400                             # candidates to look through; most are kept out by licence or overlap
N_PAPERS = 40
LICENSES = {"CC BY", "CC BY-NC"}             # reusable for training; ND and SA variants left out
PAUSE = 0.4                                  # seconds between NCBI calls: at most 3 a second without a key


def search(query: str = QUERY, limit: int = SEARCH_MAX) -> list[str]:
    """Asks NCBI which PubMed Central articles match `query`, and returns their PMCIDs.

    One GET to E-utilities' esearch with db=pmc (search PubMed Central, not PubMed),
    term=query (the same syntax as PMC's search box: field tags like [Title/Abstract],
    AND/NOT, the "open access" filter, a [pdat] date range), retmax=limit (at most that
    many ids), retmode=json, and sort=relevance (best matches first, so the 40 kept
    later are the most on-topic). NCBI answers {"esearchresult": {"idlist": ["3854211",
    ...]}}: numeric ids without the "PMC" prefix, which is added here.

    Returns: e.g. ["PMC10448394", "PMC9011342", ...], at most `limit` long, best first.
    Raises: requests.HTTPError on a non-200 answer (raise_for_status), so a failed
    search stops the script instead of quietly returning nothing.
    """
    response = requests.get(ESEARCH, params={"db": "pmc", "term": query, "retmax": limit, "retmode": "json",
                                             "sort": "relevance"}, timeout=30)
    response.raise_for_status()
    ids = response.json()["esearchresult"]["idlist"]   # PMC's numeric ids, without the "PMC" prefix
    return [f"PMC{i}" for i in ids]


def metadata(pmcid: str) -> dict | None:
    """Fetches the article's metadata JSON from PMC's open-access bucket, latest version.

    The bucket keeps one metadata file per article version: metadata/PMC3854211.1.json,
    metadata/PMC3854211.2.json if the article was corrected, and so on. Two requests:
      1. an S3 "list objects" call (list-type=2) with prefix "metadata/<pmcid>." lists
         those files as XML; the <Key> names are pulled out with a regex. The "." at the
         end of the prefix stops PMC3854211 from also matching PMC38542110.
      2. the file with the highest version number is downloaded and parsed.
    (Method taken from the original scripts/collect_corpus.py.)

    Returns: the JSON as a dict, with among others "pmcid", "version", "title",
    "citation", "license_code" (e.g. "CC BY"), "is_retracted" (bool) and "pdf_url"
    ("s3://pmc-oa-opendata/PMC123.1/PMC123.1.pdf?md5=..."); or None if the listing is
    empty, meaning the article is not in the open-access bucket (no free PDF).
    Raises: requests.HTTPError if either request fails.
    """
    # the "." after the PMCID stops PMC3854211 from also matching PMC38542110
    listing = requests.get(BUCKET, params={"list-type": "2", "prefix": f"metadata/{pmcid}."}, timeout=30)
    listing.raise_for_status()
    keys = re.findall(r"<Key>(metadata/[^<]+\.json)</Key>", listing.text)
    if not keys:
        return None
    latest = max(keys, key=lambda k: int(k.rsplit(".", 2)[1]))   # metadata/PMC123.2.json -> 2
    response = requests.get(f"{BUCKET}/{latest}", timeout=30)
    response.raise_for_status()
    return response.json()


def corpus_pmcids(path: Path = CATALOG_PATH) -> set[str]:
    """Reads data/candidates.csv and returns every PMCID in it, as a set.

    Rows with keep=yes (the 52 indexed papers) and keep=no (the 14 excluded candidates)
    are both included: G1 must train on papers the system has never seen, and an excluded
    candidate was still read and judged once. Whitespace around a PMCID is stripped.

    Returns: e.g. {"PMC3854211", "PMC9011342", ...}, 66 PMCIDs.
    """
    with open(path, newline="", encoding="utf-8") as f:
        return {row["pmcid"].strip() for row in csv.DictReader(f)}


def keep(meta: dict | None, excluded: set[str]) -> bool:
    """Decides whether a candidate paper may be used for G1's training data.

    True only if all five hold:
      - meta is not None: the article is in the open-access bucket;
      - its PMCID is not in `excluded` (the corpus's 66 PMCIDs from corpus_pmcids());
      - license_code is "CC BY" or "CC BY-NC" (LICENSES): free to reuse; the ND
        ("no derivatives") and SA ("share alike") variants and missing licences are out;
      - is_retracted is false;
      - it has a pdf_url.
    Missing fields fail the check (meta.get with a default) instead of raising.
    drop_reason() says which condition failed, for the summary.
    """
    return (
        meta is not None
        and meta["pmcid"] not in excluded              # not one of the corpus's 52 or its 14 excluded candidates
        and meta.get("license_code") in LICENSES       # CC BY or CC BY-NC
        and not meta.get("is_retracted", False)
        and bool(meta.get("pdf_url"))
    )


def pdf_link(meta: dict) -> tuple[str, str]:
    """Turns the metadata's pdf_url into a downloadable https URL and the expected md5.

    The bucket gives "s3://pmc-oa-opendata/PMC123.1/PMC123.1.pdf?md5=abc...". urlparse
    splits it into a path ("/PMC123.1/PMC123.1.pdf") and a query ("md5=abc..."); the
    path is put after the bucket's https address, and the md5 is read from the query.

    Returns: ("https://pmc-oa-opendata.s3.amazonaws.com/PMC123.1/PMC123.1.pdf", "abc..."),
    the same URL and md5 format as data/candidates.csv's pdf_url and pdf_md5 columns.
    """
    link = urlparse(meta["pdf_url"])                     # s3://pmc-oa-opendata/PMC123.1/PMC123.1.pdf?md5=abc
    url = f"{BUCKET}{link.path}"                         # https://pmc-oa-opendata.s3.amazonaws.com/PMC123.1/PMC123.1.pdf
    return url, parse_qs(link.query)["md5"][0]


def download(meta: dict, raw_dir: Path = RAW_DIR) -> tuple[str, str]:
    """Downloads the paper's PDF to raw_dir/<pmcid>.pdf and checks it arrived intact.

    The file name follows row 1's data/raw/<pmcid>.pdf, so parse_pdf() can read it
    unchanged (it takes the PMCID from the file name). Steps:
      1. if the file already exists and its md5 matches the expected one, nothing is
         downloaded: a rerun after a crash doesn't fetch everything again;
      2. otherwise the PDF is fetched (120 s timeout: some are tens of MB);
      3. its md5 is computed and compared with the one in the metadata: a mismatch means
         a corrupt or partial download, and nothing is written;
      4. the folder is created if needed and the file written.

    Returns: (url, md5) for the catalog row.
    Raises: requests.HTTPError if the download fails; ValueError on an md5 mismatch.
    main() catches both and skips that paper.
    """
    url, expected = pdf_link(meta)
    path = raw_dir / f"{meta['pmcid']}.pdf"
    if path.exists() and hashlib.md5(path.read_bytes()).hexdigest() == expected:
        return url, expected
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    got = hashlib.md5(response.content).hexdigest()
    if got != expected:
        raise ValueError(f"{meta['pmcid']}: md5 {got} != {expected}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return url, got


def drop_reason(meta: dict | None, excluded: set[str]) -> str:
    """Names the first condition keep() failed, for main()'s summary line.

    Checked in keep()'s order: not in the bucket, already in the corpus, wrong or missing
    licence (the licence is named, e.g. "licence CC BY-NC-ND"), retracted, no PDF.
    Only called after keep() returned False, so one of these always applies.
    """
    if meta is None:
        return "not in the open-access bucket"
    if meta["pmcid"] in excluded:
        return "already in the corpus"
    if meta.get("license_code") not in LICENSES:
        return f"licence {meta.get('license_code') or 'none'}"
    if meta.get("is_retracted", False):
        return "retracted"
    return "no PDF"


def main():
    """Builds data/grader/: 40 new papers and their catalog.

    1. Reads the corpus PMCIDs to exclude, and runs the one NCBI search (up to 400
       candidates, most relevant first).
    2. Walks the candidates in that order until 40 are kept. A corpus PMCID is skipped
       without asking the bucket; otherwise metadata() then keep(); a rejected paper is
       counted under its drop_reason(); a kept one is downloaded, and a failed or corrupt
       download is counted and skipped rather than stopping the run.
    3. Writes data/grader/catalog.csv with data/candidates.csv's columns (keep=yes on
       every row), so row 1's load_catalog() and parse_pdf() can read it.
    4. Prints how many were kept and why the others were dropped, and a warning if fewer
       than 40 were found (then raise SEARCH_MAX or widen QUERY).
    """
    excluded = corpus_pmcids()
    candidates = search()
    time.sleep(PAUSE)                                  # the one NCBI call; the rest go to the bucket
    print(f"{len(candidates)} candidates from NCBI; {len(excluded)} corpus PMCIDs excluded")

    rows, dropped = [], {}
    for pmcid in candidates:
        if len(rows) == N_PAPERS:
            break
        meta = None if pmcid in excluded else metadata(pmcid)
        if pmcid in excluded or not keep(meta, excluded):
            reason = "already in the corpus" if pmcid in excluded else drop_reason(meta, excluded)
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        try:
            url, md5 = download(meta)
        except (requests.RequestException, ValueError) as e:  # a failed or corrupt download: skip that paper
            dropped["download failed"] = dropped.get("download failed", 0) + 1
            print(f"  {pmcid}: {e}")
            continue
        rows.append({"keep": "yes", "pmcid": pmcid, "title": meta["title"], "citation": meta["citation"],
                     "license": meta["license_code"], "pdf_url": url, "pdf_md5": md5})
        print(f"{len(rows):>2}/{N_PAPERS} {pmcid} {meta['license_code']:<8} {meta['title'][:60]}")

    GRADER_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_CATALOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"kept {len(rows)}; dropped: " + ", ".join(f"{n} {r}" for r, n in sorted(dropped.items())))
    print(f"wrote {OUT_CATALOG} and {len(rows)} PDFs in {RAW_DIR}")
    if len(rows) < N_PAPERS:
        print(f"only {len(rows)} of {N_PAPERS}: raise SEARCH_MAX or widen QUERY")


if __name__ == "__main__":
    main()
