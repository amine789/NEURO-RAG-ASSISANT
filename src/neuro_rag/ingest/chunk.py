"""Pages -> chunks that fit the embedding model, with stable IDs (IN-4, IN-7, IN-8)."""
from collections.abc import Callable
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from neuro_rag.ingest.parse import Page


@dataclass(frozen=True)
class Chunk:
    chunk_id: str  # "<pmcid>-p<page>-c<n>"
    page: Page
    text: str


def chunk_pages(
    pages: list[Page],
    count_tokens: Callable[[str], int],
    max_tokens: int,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Split each page on its own, so a chunk never spans two pages.

    Sizes are counted with `count_tokens` (the dense model's tokenizer). The
    splitter prefers paragraph, then sentence, then word boundaries, but can
    still overshoot on long unbroken text, so any chunk over `max_tokens` is
    split again by words until it fits.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=count_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator="end",
    )
    chunks = []
    for page in pages:
        texts = [t for piece in splitter.split_text(page.text) for t in _fit(piece, count_tokens, max_tokens)]
        for n, text in enumerate(texts):
            chunks.append(Chunk(f"{page.paper.pmcid}-p{page.page}-c{n}", page, text))
    return chunks


def _fit(text: str, count_tokens: Callable[[str], int], max_tokens: int) -> list[str]:
    """`text` as one or more pieces of at most max_tokens, cut between words."""
    text = text.strip()
    if count_tokens(text) <= max_tokens:
        return [text] if text else []
    words = text.split(" ")
    if len(words) == 1:  # one huge "word" (e.g. a sequence string): cut by characters
        half = len(text) // 2
        return _fit(text[:half], count_tokens, max_tokens) + _fit(text[half:], count_tokens, max_tokens)
    half = len(words) // 2
    return (_fit(" ".join(words[:half]), count_tokens, max_tokens)
            + _fit(" ".join(words[half:]), count_tokens, max_tokens))
