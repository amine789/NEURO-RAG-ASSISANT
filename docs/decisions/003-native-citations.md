# 003: Use the Claude API's native citations, not citation markers in the text

- **Status:** accepted, 2026-10-18
- **Evidence:** design constraint, plus v1 measurement

## Context

Every claim in an answer must cite the paper and page it comes from. v1 asked the
model to write `[n]` markers in its text, then checked them in code: markers
that pointed at no source were removed. The v1 eval measured that the model did
write invalid markers, so the code check was needed, and it could only remove a
bad marker, not find the right one.

The Claude Messages API has a citations feature: each retrieved chunk is sent as
a document, and the response says, for each cited passage, which document it
comes from and the exact text it quotes.

## Options

| Option | For | Against |
|---|---|---|
| A. `[n]` markers in the text (v1) | works with any model and any output format | the model can write markers that point nowhere; the code can only delete them |
| **B. Native citations** | every citation is guaranteed to point at a real passage of a supplied chunk; the quoted text comes back exactly and costs no output tokens | can't be combined with structured outputs (JSON); the answer arrives as several text blocks to assemble |

## Decision

Send each retrieved chunk as one document with citations enabled, titled with
its paper and page. Build the `[n]` markers and the source list in code from the
citations the API returns, so a marker can only ever point at a supplied chunk.

## Consequences

- Invalid citations can't happen by construction, instead of being cleaned up.
- The generation step can't also ask for JSON output; any flags it needs (for
  example "the papers don't cover this") must come from the text or a separate call.
- Tests can check citations exactly: every `cited_text` must appear in the chunk
  it points at.

## Evidence so far

- v1 eval: the model wrote invalid `[n]` markers, which the code removed before
  returning (v1 gate 3 was met only because of that cleanup).
- The citations documentation states that citations are guaranteed to contain
  valid pointers to the provided documents.
- Row 3 (2026-10-18): every citation in the Claude tests pointed at a sent chunk
  and quoted it exactly (GN-1).

## How it will be validated

Row 3's tests check that every citation points at a supplied chunk and that its
quoted text appears in that chunk; the eval (row 4) measures answer faithfulness.
