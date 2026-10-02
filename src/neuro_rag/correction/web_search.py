import json
import logging
import os
import re
import requests
from langchain_core.documents import Document

from neuro_rag.config import llm

logger = logging.getLogger(__name__)

FIRECRAWL_URL = "https://api.firecrawl.dev/v2/search"
REQUEST_TIMEOUT = 30  # seconds; scraping each result page takes longer than a plain search
MAX_RESULTS = 5
MAX_CONTENT_CHARS = 4000  # per page; keeps web Documents close to PDF chunk size
MIN_CONTENT_CHARS = 1000  # less than this after cleaning: CAPTCHA, paywall stub, or empty page


def clean_markdown(text: str) -> str:
    """Strip scraped-page clutter from markdown, keeping the readable text."""
    target = r"\((?:[^()]|\([^)]*\))*\)"  # (url "title"), allowing one level of nested parens
    text = re.sub(r"!\[[^\]]*\]" + target, "", text)  # images
    text = re.sub(r"\[([^\]]*)\]" + target, r"\1", text)  # links -> their text
    text = re.sub(r"https?://\S+", "", text)  # bare URLs
    text = re.sub(r"^[\s|:-]*$", "", text, flags=re.MULTILINE)  # empty table rows
    # Articles: skip the site header and menus before the abstract, if there is one.
    abstract = re.search(r"^#+\s*Abstract\b", text, re.MULTILINE | re.IGNORECASE)
    if abstract:
        text = text[abstract.start():]
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)  # collapse blank lines
    return text.strip()


def grade_web_results(query: str, results: list[dict]) -> list[dict]:
    numbered = "\n".join(
        f"{i + 1}. {r.get('title', '')} -- {r.get('description', '')[:200]}"
        for i, r in enumerate(results)
    )
    prompt = f'''
    You grade web search results for a neuroscience research assistant.

    Query: {query}

    Search results:
    {numbered}

    A result is relevant if it is on-topic and likely contains findings, methods,
    or facts that help answer the query, even if it only answers part of it.
    Older sources are fine: a well-established finding is still valid.
    Prefer scientific sources (journal articles, reviews, university or
    institute pages) over forums, ads, or pages that only mention the query's
    words in passing. Do not answer the query.

    Return only a JSON array of the numbers of the relevant results, e.g. [1, 3].
    If none are relevant, return [].
    '''
    response = llm.invoke(prompt)
    try:
        match = re.search(r"\[.*\]", response.content, re.DOTALL)
        relevant_indices = json.loads(match.group())
        return [results[i - 1] for i in relevant_indices if 1 <= i <= len(results)]
    except (json.JSONDecodeError, AttributeError, IndexError, TypeError):
        return results


def search_web(query: str) -> list[Document]:
    """Search the web with Firecrawl and return the relevant pages as Documents.

    Used as the fallback when local retrieval still grades poorly after
    rewriting. Results are filtered by grade_web_results on their title and
    snippet; each Document holds the cleaned page markdown, with source=url and
    title in its metadata so it can be cited like a PDF chunk. Pages with too
    little text after cleaning are dropped. Returns [] on any failure, so the
    pipeline can continue.
    """
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        logger.warning("FIRECRAWL_API_KEY is not set; skipping web search")
        return []

    payload = {
        "query": query,
        "limit": MAX_RESULTS,
        "scrapeOptions": {"formats": [{"type": "markdown"}]},
    }

    try:
        response = requests.post(
            FIRECRAWL_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning("Web search failed for %r: %s: %s", query, type(e).__name__, e)
        return []

    if not body.get("success"):
        logger.warning("Web search failed for %r: %s", query, body)
        return []

    results = body.get("data", {}).get("web", [])
    if not results:
        return []

    results = grade_web_results(query, results)

    documents = []
    for r in results:
        content = clean_markdown(r.get("markdown", ""))
        if len(content) < MIN_CONTENT_CHARS:
            logger.info("Dropping thin web page (%d chars): %s", len(content), r.get("url"))
            continue
        documents.append(
            Document(
                page_content=content[:MAX_CONTENT_CHARS],
                metadata={"source": r.get("url", ""), "title": r.get("title", "")},
            )
        )
    return documents