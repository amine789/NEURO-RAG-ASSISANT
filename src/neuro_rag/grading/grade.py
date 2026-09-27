import re
import json
from langchain_core.documents import Document

from neuro_rag.config import llm

def grade_retrieval_results(
    query: str, results: list[tuple[Document, float]]
) -> list[tuple[Document, float]]:
    numbered = "\n\n".join(
    f"[{i + 1}] {chunk.page_content}"
    for i, (chunk, _score) in enumerate(results)
)
    prompt = f'''
    You grade search results for a neuroscience research assistant.

    Question: {query}

    Passages:
    {numbered}

    A passage is relevant if it is on-topic and contains findings, methods, or facts
    that help answer the question, even if it only answers part of it.
    It is not relevant if it is off-topic, only mentions the question's words in passing,
    or is boilerplate (journal headers, author lists, funding, references).
    Judge each passage on its own; do not answer the question.

    Return only a JSON array of the numbers of the relevant passages, e.g. [1, 3].
    If none are relevant, return [].
    '''
    response = llm.invoke(prompt)
    try:
        match = re.search(r"\[.*\]", response.content, re.DOTALL)
        relevant_indices = json.loads(match.group())
        return [results[i - 1] for i in relevant_indices if 1 <= i <= len(results)]
    except (json.JSONDecodeError, AttributeError, IndexError):
        return []  # grading failed