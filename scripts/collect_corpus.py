"""Collect the hippocampus/memory corpus from the PMC Open Access Subset.

Two phases, with a human check in between:

    python scripts/collect_corpus.py search     # -> data/candidates.csv
    (open the CSV, set keep=no on off-topic rows)
    python scripts/collect_corpus.py download   # keep=yes rows -> data/raw/PMCxxxx.pdf

Search uses NCBI E-utilities. Files come from PMC's open-data bucket on S3,
where each article has a metadata JSON (title, citation, license, pdf_url, md5).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_CSV = PROJECT_ROOT / "data" / "candidates.csv"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
BUCKET_URL = "https://pmc-oa-opendata.s3.amazonaws.com"

DEFAULT_QUERY = (
    'hippocampus[title] AND memory[title] AND "open access"[filter] NOT review[title]'
)
TIMEOUT = 30

CSV_FIELDS = ["keep", "pmcid", "title", "citation", "license", "pdf_url", "pdf_md5"]


def search_pmc(query: str, n: int) -> list[str]:
    """Return up to n PMC IDs (with 'PMC' prefix), most relevant first."""
    response = requests.get(
        ESEARCH_URL,
        params={"db": "pmc", "term": query, "retmax": n, "retmode": "json", "sort": "relevance"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return ["PMC" + uid for uid in response.json()["esearchresult"]["idlist"]]


def fetch_metadata(pmcid: str) -> dict | None:
    """Latest-version metadata for an article, or None if it's not in the OA bucket."""
    # Keys look like metadata/PMC3854211.1.json; the trailing '.' in the prefix
    # stops PMC3854211 from also matching PMC38542110.
    listing = requests.get(
        BUCKET_URL,
        params={"list-type": "2", "prefix": f"metadata/{pmcid}."},
        timeout=TIMEOUT,
    )
    listing.raise_for_status()
    keys = re.findall(r"<Key>(metadata/[^<]+\.json)</Key>", listing.text)
    if not keys:
        return None
    latest = max(keys, key=lambda k: int(k.rsplit(".", 2)[1]))  # highest version number
    response = requests.get(f"{BUCKET_URL}/{latest}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def s3_to_https(s3_url: str) -> tuple[str, str | None]:
    """Split 's3://bucket/key?md5=abc' into (https URL, md5)."""
    path, _, query = s3_url.removeprefix("s3://pmc-oa-opendata/").partition("?md5=")
    return f"{BUCKET_URL}/{path}", query or None


def cmd_search(query: str, n: int) -> None:
    ids = search_pmc(query, n)
    print(f"search returned {len(ids)} IDs; fetching metadata...")

    rows, skipped = [], []
    for pmcid in ids:
        meta = fetch_metadata(pmcid)
        if meta is None:
            skipped.append((pmcid, "not in OA bucket"))
        elif meta.get("is_retracted"):
            skipped.append((pmcid, "retracted"))
        elif not meta.get("pdf_url"):
            skipped.append((pmcid, "no PDF"))
        else:
            pdf_url, md5 = s3_to_https(meta["pdf_url"])
            rows.append({
                "keep": "yes",
                "pmcid": pmcid,
                "title": meta["title"],
                "citation": meta["citation"],
                "license": meta["license_code"],
                "pdf_url": pdf_url,
                "pdf_md5": md5,
            })

    CANDIDATES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CANDIDATES_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    for pmcid, reason in skipped:
        print(f"  skipped {pmcid}: {reason}")
    print(f"wrote {len(rows)} candidates to {CANDIDATES_CSV.relative_to(PROJECT_ROOT)}")
    print("next: set keep=no on off-topic rows, then run `download`")


def cmd_download(target: int) -> None:
    if not CANDIDATES_CSV.is_file():
        sys.exit(f"{CANDIDATES_CSV} not found; run `search` first")
    with CANDIDATES_CSV.open(newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["keep"].strip().lower() == "yes"]

    if len(rows) != target:
        print(f"warning: {len(rows)} rows marked keep=yes, target is {target}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, row in enumerate(rows, 1):
        dest = RAW_DIR / f"{row['pmcid']}.pdf"
        if dest.exists():
            print(f"[{i}/{len(rows)}] {dest.name} already present")
            continue
        response = requests.get(row["pdf_url"], timeout=TIMEOUT)
        response.raise_for_status()
        if row["pdf_md5"] and hashlib.md5(response.content).hexdigest() != row["pdf_md5"]:
            failed.append(row["pmcid"])
            print(f"[{i}/{len(rows)}] {dest.name} checksum mismatch, not saved")
            continue
        dest.write_bytes(response.content)
        print(f"[{i}/{len(rows)}] {dest.name} ({len(response.content) // 1024} KB)")

    if failed:
        sys.exit(f"{len(failed)} downloads failed: {failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="find candidates and write data/candidates.csv")
    search.add_argument("--query", default=DEFAULT_QUERY)
    search.add_argument("-n", type=int, default=70, help="how many search hits to consider")

    download = sub.add_parser("download", help="download PDFs for keep=yes rows")
    download.add_argument("--target", type=int, default=50, help="expected corpus size")

    args = parser.parse_args()
    if args.command == "search":
        cmd_search(args.query, args.n)
    else:
        cmd_download(args.target)


if __name__ == "__main__":
    main()
