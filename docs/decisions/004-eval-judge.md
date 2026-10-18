# 004: Which model judges the eval

- **Status:** accepted, 2026-10-18
- **Evidence:** assumption, to be checked by EV-11

## Context

The eval needs an LLM to judge correctness (against a reference answer) and
faithfulness (against the cited chunks). The system itself uses Claude Haiku 5.5
for every call. A model judging answers written by itself tends to be lenient
with them. v1 used a stronger model (Sonnet 5) as judge but never checked its
verdicts against a person.

## Options

| Option | For | Against |
|---|---|---|
| A. Claude Haiku 5.5, the system's model | cheapest ($0.10 / $0.50 per 1M tokens); one model everywhere | judges its own answers: likely lenient, shares the same blind spots |
| B. Claude Sonnet 5.5 | a different, stronger model, so less self-leniency | 20 times Haiku's price ($2 / $10); still the same model family |
| C. Claude Opus 5.5 | strongest judgement | 40 times Haiku's price ($4 / $20) |

Rough cost of one baseline run (162 answers, two judge calls each, about 4,000
tokens per call): A about $0.15, B about $3, C about $6.

## Decision

Claude Haiku 5.5 (`claude-haiku-5-5`) judges correctness and faithfulness,
the same model the system uses: one model everywhere, and a full judge run costs
about $0.15.

## Consequences

- The risk is a lenient judge, since it grades answers written by the same
  model. EV-11 is what catches that: if Haiku agrees with a person on fewer than
  16 of 20 runs, the judge prompt is revised or this decision is reopened.
- Changing the judge later makes earlier scores incomparable: reports must name
  the judge model.

## How it will be validated

EV-11: the judge's verdicts must match a person's on at least 16 of 20 runs.

## Evidence so far

- 2026-10-18, baseline run: 162 runs, 0 judge errors. A spot check of 3 of the
  19 "unfaithful" verdicts against the cited chunks found one wrong (q06 #1:
  the flagged sentence is almost word for word in chunk [2]) and two right
  (q16 #1, q09 #3). So the judge is not only lenient: it can also be too strict.
- EV-11 is not done: no grader with the domain knowledge was available. Until
  it is, every score is the judge's opinion, unchecked. The fallback considered
  was checking Haiku against Opus 5.5 on the same 20 runs, which shows
  agreement with a stronger model, not with a person.
