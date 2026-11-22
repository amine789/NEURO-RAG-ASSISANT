"""Row 9's corrective loop: retrieve → grade → (rewrite → retry)* → web → generate or "not covered".

Every step is a function passed in (search, grade, answer, rewrite, web), so the
tests drive every branch with fakes and no API call (spec CR-4 to CR-10). The real
functions are wired in by the API (app.py) and the eval (eval/run.py --crag).
See docs/specs/crag/spec.md, phase 2.
"""
import logging                                   # a failing rewrite, grade or web call is logged, then treated as weak (CR-8)
from dataclasses import dataclass                # CragResult: the answer plus the path taken

from langfuse import observe                     # each state is a step in the Langfuse trace (CR-11), as in app.py

from neuro_rag.config import GRADE_CUT, MAX_REWRITES          # 0.5 and 2 (choices 2 and 5)
from neuro_rag.generation.answer import NOT_FOUND, Answer     # "not covered" reuses row 3's message and Answer shape
from neuro_rag.retrieval.search import Hit                    # what search and the web return: .text is graded

log = logging.getLogger(__name__)

# the rewriter's instructions: v2's validated rewriter prompt (docs/specs/correction, v2),
# plus the last query, so a second rewrite tries other words; reply is plain text (no JSON)
REWRITE_PROMPT = """You rewrite a user's question into a search query for a collection of scientific papers on the hippocampus and memory.

Rules:
- Write the query in English, whatever language the question is in.
- Replace everyday words with the terms the papers would use (for example "fear center" becomes "amygdala").
- Keep every specific term from the question unchanged: gene and protein names, brain regions, species, methods.
- Keep the question's meaning. Don't answer it, don't add claims, and don't narrow it to one hypothesis.
- Write one line, at most 30 words: a short question or phrase. Reply with the query only.

Examples:
Question: why do I keep forgetting where I put my keys?
Query: everyday forgetting of object locations; spatial memory retrieval and the hippocampus

Question: Est-ce que le stress abîme la mémoire ?
Query: effects of chronic stress on memory and hippocampal function

Question: {question}{last}"""

# added only from the second rewrite on, when the last query was itself a rewrite
LAST_QUERY = """
This query was already tried and found nothing useful; write a different one: {query}"""

MAX_WORDS = 60       # a longer reply is not a query (the model answered or explained): treated as a failed rewrite


@dataclass(frozen=True)
class CragResult:
    """What run_loop returns: the answer, the states it went through, and whether the web was used.

    Fields:
      answer: the cited Answer from answer_fn (row 3's shape: text, sources,
        citations, input_tokens, output_tokens), or, when every grade was weak,
        Answer(NOT_FOUND, [], [], 0, 0): "not covered", with no Claude answer call.
      path: the states in the order they ran, each one string. The names are fixed,
        because the API returns them (CR-10) and the tests compare them exactly:
          "retrieve"                   a search (papers), with the question or a rewrite
          "grade:good" / "grade:weak"  the grader's decision on those hits (GRADE_CUT)
          "rewrite"                    a new search query written by Haiku
          "web"                        the web search on WEB_DOMAINS
          "generate"                   answer_fn wrote the answer
          "not_covered"                weak everywhere: NOT_FOUND, no answer call
        e.g. good at once:  ["retrieve", "grade:good", "generate"]
             one rewrite:   ["retrieve", "grade:weak", "rewrite", "retrieve", "grade:good", "generate"]
             the web:       [... 3 × retrieve/grade:weak, 2 × rewrite ..., "web", "grade:good", "generate"]
      used_web: True only when the answer was written from web hits (the API's
        "used_web"); False for answers from the papers and for "not covered", even
        if the web was searched (that shows in path as "web").

    frozen=True: a result is never changed after the loop returns it.
    """
    answer: Answer
    path: list[str]
    used_web: bool


@observe(name="grade")
def grade(grade_fn, question: str, hits: list[Hit], path: list[str]) -> bool:
    """Grades the hits once, records the decision in path, and returns True if they are good.

    Steps:
      1. No hits (e.g. the web search failed or found nothing) → weak, and grade_fn
         is not called: there is nothing to grade.
      2. Otherwise score = grade_fn(question, hits), a P(yes) in [0, 1] (in the API,
         jev_grader). The ORIGINAL question is graded, never a rewrite: the chunks
         must answer what the user asked.
      3. good if score >= GRADE_CUT (0.5), else weak.
      4. Appends "grade:good" or "grade:weak" to path (the list is changed in place,
         so run_loop's path grows as the loop runs).

    Failures (CR-8): any exception from grade_fn (network, timeout, a 402 from
    OpenRouter, a missing key) is logged with the error and counts as weak, so the
    loop moves on (rewrite, then the web) instead of crashing. The cost of that
    choice: a grader outage makes every question take the slow path, ending in
    "not covered" if the web fails too; never a crash, never an answer from
    ungraded chunks.

    @observe(name="grade"): each call is one "grade" step in the Langfuse trace (CR-11).

    Args:
      grade_fn: (question, hits) -> float, e.g. graders.jev_grader; a fake in the tests.
      question: the user's question, as asked.
      hits: the Hits to grade (papers or web); only .text is read by the graders.
      path: run_loop's path so far; one entry is appended.
    Returns: True for good, False for weak.

    e.g. grade(lambda q, h: 0.91, "How does m6A ...", hits, path) → True, path ends with "grade:good"
         grade(lambda q, h: 0.12, ...) → False, path ends with "grade:weak"
         grade(grader_that_raises, ...) → False, "grade:weak", and a warning in the log
    """
    good = False
    if hits:
        try:
            good = grade_fn(question, hits) >= GRADE_CUT
        except Exception as e:                           # any grader failure is weak, never a crash (CR-8)
            log.warning("grader failed, treated as weak: %s", e)
    path.append("grade:good" if good else "grade:weak")
    return good


@observe(name="rewrite")
def rewrite(question: str, last_query: str, llm) -> str | None:
    """Rewrites the question into a cleaner search query with one Haiku call; None if that fails.

    Steps:
      1. Fills REWRITE_PROMPT with the question. If last_query differs from the
         question (it was itself a rewrite, i.e. this is the second rewrite), LAST_QUERY
         is added, so Haiku is told that wording failed and writes a different one.
      2. llm.invoke(prompt): one call to Haiku 4.5 through make_llm() (LangChain
         ChatAnthropic, as every v3 LLM call; with the Langfuse callback in the API).
      3. The reply text is cleaned: whitespace collapsed to single spaces, a leading
         "Query:" removed (the examples end with it, so the model may repeat it),
         surrounding quotes removed.
      4. Rejected (returns None) if empty or longer than MAX_WORDS (60) words: then
         the model answered or explained instead of writing a query.

    Failures (CR-8): any exception from the call (network, rate limit, missing key)
    is logged and returns None; run_loop then keeps the last query and moves on.

    @observe(name="rewrite"): one "rewrite" step in the Langfuse trace (CR-11).

    Args:
      question: the user's question, as asked.
      last_query: the query the last search used (the question itself on the first rewrite).
      llm: anything with .invoke(prompt) returning a message with .content (make_llm(); a fake in tests).
    Returns: the new query, e.g. "why do I keep forgetting where I put my keys?" →
      "everyday forgetting of object locations; spatial memory retrieval and the hippocampus";
      or None.
    Cost: about 400 tokens in, 20 out, about $0.0005 with Haiku 4.5; only after a weak grade.
    """
    last = LAST_QUERY.format(query=last_query) if last_query != question else ""
    try:
        reply = llm.invoke(REWRITE_PROMPT.format(question=question, last=last)).content
    except Exception as e:                               # a failed rewrite is not a crash (CR-8)
        log.warning("rewrite failed, last query kept: %s", e)
        return None
    query = " ".join(str(reply).split()).removeprefix("Query:").strip().strip('"\'')
    if not query or len(query.split()) > MAX_WORDS:
        log.warning("rewrite unusable, last query kept: %r", query[:100])
        return None
    return query


@observe(name="crag")
def run_loop(question: str, search_fn, grade_fn, answer_fn, rewrite_fn, web_fn) -> CragResult:
    """The corrective loop for one question: answer from good hits, else rewrite and retry, then the web.

    Steps (spec phase 2, "The loop"):
      1. Up to MAX_REWRITES + 1 = 3 attempts on the papers. Each attempt:
         - "retrieve": hits = search_fn(query); the first query is the question itself;
         - grade() on the ORIGINAL question: good → answer_fn(question, hits),
           "generate", return (used_web False);
         - weak, and rewrites left → "rewrite": query = rewrite_fn(question, query).
           The rewriter sees the question and the last query, so a second rewrite
           can try something different. If it fails it returns None and the last
           query is kept (the retry then repeats the same search: wasted, not wrong).
      2. Weak after the last attempt → "web": hits = web_fn(query), with the last
         query (the cleanest wording so far); [] if the web call failed.
      3. grade() on the web hits: good → answer_fn(question, web hits), "generate",
         return (used_web True).
      4. Weak again → "not_covered": Answer(NOT_FOUND, [], [], 0, 0), no answer call.
    The question answered is always the user's own; a rewrite only changes what is
    searched.

    Every step is passed in, so tests drive each branch with fakes (CR-4 to CR-8):
      search_fn(query) -> list[Hit]              row 8's search (dense top 20, reranked, top 5)
      grade_fn(question, hits) -> float          the grader, P(yes); jev_grader in the API
      answer_fn(question, hits) -> Answer        row 3's cited answer (one Claude call)
      rewrite_fn(question, last_query) -> str | None   one Haiku call; None on failure
      web_fn(query) -> list[Hit]                 vetted-site search; [] on failure
    Failures (CR-8): grade_fn errors are caught in grade(); rewrite_fn and web_fn
    errors are caught here too (even though rewrite() already catches its own), so
    any rewriter or web tool, real or fake, degrades instead of crashing: a failed
    rewrite keeps the last query, a failed web call counts as no hits (weak).
    search_fn and answer_fn errors are not caught: they propagate as today (the
    API answers 503).

    @observe(name="crag"): the loop is one step in the Langfuse trace, with each
    retrieve, grade, rewrite, web and generate inside it (CR-11).

    Returns: CragResult(answer, path, used_web), e.g.
      good at once:     path ["retrieve", "grade:good", "generate"], used_web False
      weak everywhere:  path ["retrieve", "grade:weak", "rewrite", "retrieve", "grade:weak",
                              "rewrite", "retrieve", "grade:weak", "web", "grade:weak",
                              "not_covered"], answer.text NOT_FOUND, used_web False
    """
    path, query = [], question
    for attempt in range(MAX_REWRITES + 1):
        path.append("retrieve")
        hits = search_fn(query)
        if grade(grade_fn, question, hits, path):
            return CragResult(answer_fn(question, hits), path + ["generate"], False)
        if attempt < MAX_REWRITES:
            path.append("rewrite")
            try:
                query = rewrite_fn(question, query) or query # None (failed rewrite) keeps the last query
            except Exception as e:                           # any rewriter, not only ours, degrades (CR-8)
                log.warning("rewrite failed, last query kept: %s", e)
    path.append("web")
    try:
        hits = web_fn(query)                                 # [] if the web found nothing
    except Exception as e:                                   # a failed web call is weak, never a crash (CR-8)
        log.warning("web search failed, treated as weak: %s", e)
        hits = []
    if grade(grade_fn, question, hits, path):
        return CragResult(answer_fn(question, hits), path + ["generate"], True)
    return CragResult(Answer(NOT_FOUND, [], [], 0, 0), path + ["not_covered"], False)
