import re
from dataclasses import dataclass

from tokenizers import Tokenizer

from neuro_rag.config import EMBED_MODEL
from neuro_rag.ingest.parse import Page


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    pmcid: str
    page: int
    text: str


class TokenCounter:
    def __init__(self, model: str = EMBED_MODEL):
        self.tokenizer = Tokenizer.from_pretrained(model)
        self.tokenizer.no_padding()
        self.tokenizer.no_truncation()

    def __call__(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False).ids)


def split_sentences(text: str) -> list[str]:
    return [sentence for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence]


def make_units(text: str, count: TokenCounter, size: int) -> list[tuple[str, int]]:
    units = []
    for sentence in split_sentences(text):
        tokens = count(sentence)
        if tokens <= size:
            units.append((sentence, tokens))
            continue
        piece = []
        for word in sentence.split():
            if piece and count(" ".join(piece + [word])) > size:
                units.append((" ".join(piece), count(" ".join(piece))))
                piece = []
            piece.append(word)
        if piece:
            units.append((" ".join(piece), count(" ".join(piece))))
    return units


def pack_units(units: list[tuple[str, int]], size: int, carry: int) -> list[str]:
    texts = []
    current = []
    total = 0
    for text, tokens in units:
        if current and total + tokens > size:
            texts.append(" ".join(t for t, _ in current))
            last_text, last_tokens = current[-1]
            if last_tokens <= carry and last_tokens + tokens <= size:
                current = [(last_text, last_tokens)]
                total = last_tokens
            else:
                current = []
                total = 0
        current.append((text, tokens))
        total += tokens
    if current:
        texts.append(" ".join(t for t, _ in current))
    return texts


def chunk_page(page: Page, count: TokenCounter, size: int = 200, carry: int = 50) -> list[Chunk]:
    units = make_units(page.text, count, size)
    texts = pack_units(units, size, carry)
    return [Chunk(f"{page.pmcid}-p{page.page}-c{n}", page.pmcid, page.page, text) for n, text in enumerate(texts)]
