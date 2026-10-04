import re

from langchain_core.documents import Document
from neuro_rag.config import llm


def generate_answer(question: str, docs: list[Document])->str:
    if not docs:
        return "I couldn't find sources that answer this question"

    # Number the chunks for the prompt; the tag tells the model which to hedge on.
    numbered = "\n\n".join(
        f"[{i + 1}] ({'paper' if 'pmcid' in doc.metadata else 'web'}) {doc.page_content}"
        for i, doc in enumerate(docs)
    )

    prompt = f'''
    You are a neuroscience research assistant. Answer the question using only
    the numbered sources below.

    Question: {question}

    Sources:
    {numbered}

    Rules:
    - Use only facts stated in the sources. Do not add anything from your own
      knowledge, even if you are confident it is true.
    - Cite every claim inline with its source number, e.g. [2]. If several
      sources support a claim, cite them all, e.g. [1][3]. Only use numbers
      that appear in the list above.
    - If the sources only partly answer the question, answer what they cover
      and say clearly what they do not cover. If they do not answer it at all,
      say so in one sentence instead of answering.
    - If sources disagree, say so and cite each side.
    - Sources marked (paper) are peer-reviewed articles from the curated
      corpus; sources marked (web) are web pages and less vetted. When a claim
      rests only on (web) sources, say so.
    - Be concise: a direct answer first, then the supporting detail, in a few
      short paragraphs for a reader with some neuroscience background.
      Do not add a list of sources at the end; it is added separately.
    '''
    response = llm.invoke(prompt)
    answer = response.content.strip()

    # List only the sources the answer cites, keeping the prompt's numbering.
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer)})
    sources = [f"[{n}] {format_source(docs[n - 1])}" for n in cited if 1 <= n <= len(docs)]
    if not sources:
        return answer
    return answer + "\n\nSources:\n" + "\n".join(sources)


def format_source(doc: Document) -> str:
    """Readable citation: title, page and PMC link for papers; title and URL for web pages."""
    meta = doc.metadata
    if "pmcid" in meta:
        return f"{meta['title']}, p. {meta['page']}, https://pmc.ncbi.nlm.nih.gov/articles/{meta['pmcid']}/"
    return f"{meta.get('title') or meta['source']}, {meta['source']}"
