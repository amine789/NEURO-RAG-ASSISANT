
def rewrite_query(llm, query:str)->str:
    prompt = (
        "You rewrite questions into search queries for a corpus of hippocampus "
        "neuroscience research papers. The corpus is searched with both keyword "
        "(BM25) and embedding search, so the query must use the exact technical "
        "terms these papers use.\n\n"
        "Rewrite the question below into one search query:\n"
        "- Replace everyday words with scientific terms "
        "(e.g. 'remembering places' -> 'spatial memory, place cells').\n"
        "- Name a brain region, cell type, or mechanism only if the question "
        "is clearly about it; do not list regions or mechanisms just because "
        "they are common in hippocampus research.\n"
        "- Write out abbreviations once alongside the short form "
        "(e.g. 'LTP long-term potentiation').\n"
        "- Add one or two close synonyms for the key concept.\n"
        "- Keep every key term from the original question; fix typos; "
        "drop filler words.\n"
        "- Do not answer the question or add facts that are not implied by it.\n\n"
        "- Keep it focused: about 5 to 12 words. A short query with the right "
        "terms beats a long list of loosely related ones.\n\n"
        "Return only the query, on one line, with no quotes or labels.\n\n"
        f"Question: {query}"
    )
    response = llm.invoke(prompt)
    text = getattr(response, "content", response).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rewritten = lines[-1] if lines else ""  # skip any "Here is..." line before it
    rewritten = rewritten.removeprefix("Query:").strip().strip("\"'")
    return rewritten or query  # empty -> keep the original question