# 006: Judge relevance with an LLM grader

- **Status:** accepted, 2026-10-20 (first proposed as a threshold on the
  reranker's score; rejected after that version's GR-3 and GR-4, see Evidence)
- **Evidence:** measured for the threshold; the LLM grader is checked by GR-10 and GR-11

## Context

The corrective loop (row 7) needs a yes/no after retrieval: do these chunks
answer the question, or should the question be rewritten and searched again?
v1 asked an LLM to grade each chunk; its free-text output failed to parse, and
the fallback treated "nothing relevant" as "all relevant".

Since row 6a every question already has a cross-encoder score per chunk, so
the first proposal reused that score with a threshold, like the CRAG paper's
retrieval evaluator. The latency budget is tight: generation p95 is about
4.4 s and reranking about 0.5 s, against 6 s.

## Options

| Option | For | Against |
|---|---|---|
| A. Threshold on the reranker's top score | free and instant | **measured: doesn't separate** (see Evidence) |
| **B. LLM grader: Haiku judges the chunks, structured output** | reads meaning: can tell "same words" from "answers the question"; structured output always parses | one more call on every question: about 1.5 s and $0.0002 |
| C. Two thresholds, LLM only between them (CRAG's three zones) | LLM cost only for unclear cases | two thresholds to calibrate on scores that already overlap; two mechanisms to explain |

## Decision

B. Claude Haiku 5.5, with thinking off, reads the question and the reranked chunks in one call and says,
for each chunk, whether it helps answer the question. The chunks pass if at
least one is relevant. How exactly: the grading spec.

## Consequences

- Every question pays one more Claude call, about $0.0002. A call takes about
  1.5 s whatever the model: Haiku 5.5 with its default thinking took p95
  2.5 s, Haiku 4.5 without thinking p95 1.77 s at 10× the price (2026-10-21).
  The grader uses Haiku 5.5 with thinking off.
- Run before generation, that would push answers to about 6.6 s p95, over the
  6 s target. So row 7 runs generation while grading runs: when the grade
  passes, the answer is already being written and grading adds no time; when
  it fails, that answer is discarded (about $0.0005 wasted). GR-11 only checks
  grading stays under 2 s.
- The grader is an LLM judging relevance, so it needs its own check against
  labelled questions (GR-10), like the eval judge (decision 004).
- The reranker stays: it still picks the best 5 of 20 (decision 005).
- If latency becomes the problem, option C is the next step: the reranker's
  score decides the clear cases and the LLM only the middle ones.

## Evidence

- 2026-10-20, option A, in the threshold version of the spec (its GR-3 and GR-4): keeping 90% of found questions passing needed
  T = -2.43. The separation check passed (at least 60% of missed and off-topic
  questions fell below T), but GR-4 failed: "How do the fear center and the
  memory center keep their rhythms in step when people form unpleasant
  memories?" scored above T, though its paper (PMC9613775) is never retrieved.
  A threshold low enough for the weak found questions also lets weak matches
  through.

## How it will be validated

- GR-10: the grader's verdicts agree with the eval labels (found should pass,
  missed and off-topic should fail).
- GR-11: the grading call's latency.
- The row 7 eval: whether routing on the grade improves correctness.
