# Retrieval: spec

What this module must do. Written when its row in [ROADMAP.md](../../ROADMAP.md)
starts.

## Goal

Given a question, return the most relevant chunks, using dense and keyword search together.

## In and out

- **In:** a question (text), and how many chunks to return.
- **Out:** the chunks, best first. Each has its text, chunk ID, `pmcid`, `title`,
  `citation`, `license`, `page` and its fused score.
- **Reads:** the `hippocampus` alias in Qdrant, built by [ingest](../ingest/spec.md).

```
question ──► dense encoder  ──► Qdrant: top 20 by meaning  ─┐
         └─► sparse encoder ──► Qdrant: top 20 by keywords ─┴─► RRF fusion ──► top 5
```

Both searches and the fusion run in one Qdrant query
([decision 002](../../decisions/002-keyword-search-in-qdrant.md)).

## Settings

Starting values, revisited once the eval can measure them (roadmap row 4).

| Setting | Start | Why |
|---|---|---|
| chunks returned | 5 | enough to answer from; few enough to read and cite |
| candidates per search | 20 | wide enough that a chunk ranked low by one search can still be lifted by the other |
| fusion | reciprocal rank fusion (Qdrant's built-in) | uses ranks only, so dense and BM25 scores, which are on different scales, never have to be compared |

## Acceptance criteria

Each criterion is one concrete example, written so it can be read on its own:

- **Given** describes the data that is in Qdrant before the test starts.
- **When** is the exact call that is made.
- **Then** is what must be true afterwards.
- **Why** explains what is broken if it fails.

How each one is run is in [validation.md](validation.md).

### The small test collection

Most examples below use the same small collection of six chunks. The test builds
it with ingest's own code (`create_collection` and `write_chunks`) and the real
encoders, so retrieval is tested against exactly what ingest writes. The six
chunks are:

1. "Place cells in the hippocampus fire when the animal is at a specific location."
2. "Grid cells in the entorhinal cortex fire in a hexagonal pattern across space."
3. "The protein zqx-17 is required for memory consolidation during sleep."
4. "Sleep spindles coordinate the replay of recent experiences."
5. "Chronic stress shrinks dendrites in the CA3 region."
6. "Exercise increases the birth of new neurons in the dentate gyrus."

The word "zqx-17" in chunk 3 is made up. It appears in no other chunk, and no
model has ever seen it.

### Results

**RT-1: results are sorted, limited to the number asked for, and complete.**
- **Given** the small test collection of six chunks.
- **When** the code calls `retrieve("where are place cells?", k=3)`, asking for
  the 3 best chunks.
- **Then** it returns no more than 3 chunks. They are sorted from the highest
  score to the lowest. Every returned chunk has all of these fields filled in:
  `text`, `chunk_id`, `pmcid`, `title`, `citation`, `license` and `page`.
- **Why:** the answer step (row 3) builds its citations from these fields. If
  one is missing or empty, a citation in the answer would be broken.

**RT-2: a chunk found by both searches appears only once, and comes first.**
- **Given** the small test collection of six chunks.
- **When** the code calls `retrieve("place cells hippocampus location", k=5)`.
- **Then** the first result is the chunk "Place cells in the hippocampus fire
  when the animal is at a specific location.", and that chunk appears only once
  in the results.
- **Why:** that chunk matches the question in both ways: by meaning, and by the
  exact words "place", "cells" and "hippocampus". The meaning search and the
  keyword search both return it. Fusion must merge the two lists into one, so a
  chunk found by both appears once and ranks highest. If it appears twice, the
  two lists were simply joined together instead of being fused.

**RT-3: a rare exact term is found by keyword search.**
- **Given** the small test collection of six chunks, where only the chunk "The
  protein zqx-17 is required for memory consolidation during sleep." contains
  the made-up word "zqx-17".
- **When** the code calls `retrieve("what does zqx-17 do?", k=5)`.
- **Then** the chunk "The protein zqx-17 is required for memory consolidation
  during sleep." is among the 5 results.
- **Why:** the meaning model has never seen the word "zqx-17", so it can't tell
  that this chunk is the right one. Only the keyword search, which matches the
  exact word, can find it. If this test fails, the keyword search isn't running.

**RT-4: a chunk is found by its meaning, even when it shares no words with the question.**
- **Given** the real `hippocampus` index with all 52 papers.
- **When** the code calls `retrieve("how do animals remember where things are?", k=5)`.
- **Then** at least one of the 5 results is about place cells or spatial memory.
- **Why:** the question uses everyday words and none of the technical terms
  ("place cells", "spatial memory", "hippocampus"), so keyword search can't
  match it. Only the meaning search can. If this test fails, the meaning search
  isn't running.

**RT-5: a question made only of unknown words still gets results.**
- **Given** the small test collection of six chunks.
- **When** the code calls `retrieve("blorf snazzle quimp", k=5)`. These are
  made-up words that appear in no chunk.
- **Then** the call returns some chunks. It doesn't raise an error and doesn't
  return an empty list.
- **Why:** the keyword search finds nothing here, because none of the words
  exists in the collection. The meaning search always returns its closest
  chunks, so the results must come from it. If this fails, an empty keyword
  result is breaking the whole query.

**RT-6: asking the same question twice gives the same results.**
- **Given** the small test collection of six chunks.
- **When** the code calls `retrieve("where are place cells?", k=5)` twice in a row.
- **Then** both calls return the same chunks, in the same order.
- **Why:** the eval compares one run with another. If retrieval gave different
  results each time, those comparisons would mean nothing.

**RT-7: the right paper is found for questions about it.**
- **Given** the real `hippocampus` index with all 52 papers, and a list of 20
  questions. Each question is about the main finding of one paper, and is worded
  differently from that paper's title. For example, for the paper "Resistance
  exercise improves hippocampus-dependent memory", the question is "Can lifting
  weights make you better at remembering?"
- **When** the code asks each of the 20 questions with `k=5`.
- **Then** for at least 18 of the 20 questions, at least one of the 5 results
  comes from the paper the question is about.
- **Why:** this is a sanity check on real data. It catches a broken index or a
  wrong encoder. The test also reports how many questions found their paper
  anywhere among the 40 candidates (before fusion keeps the top 5). That number
  says whether a reranker would help: if the paper was found but ranked too
  low, a reranker can fix it.

### Consistency with ingest

**RT-8: retrieval uses the same encoders as ingest.**
- **Given** the retrieval code.
- **When** a person reads its imports.
- **Then** it gets both encoders from `neuro_rag.encoders`, the same module
  ingest uses, and creates no model of its own.
- **Why:** the question must be turned into vectors the same way the chunks were.
  If it were encoded differently, the search would quietly return worse results
  without any error.

**RT-9: a new build is picked up without changing any code.**
- **Given** a retriever that was created while the `hippocampus` alias pointed
  at the small test collection of six chunks.
- **When** a second collection is built containing only the chunk "Dopamine
  signals reward prediction errors.", the alias is moved to it, and then the
  same retriever (not a new one) is asked `retrieve("dopamine reward", k=5)`.
- **Then** the chunk "Dopamine signals reward prediction errors." is returned.
- **Why:** the retriever must look up the alias on every question. If it
  remembered the collection it saw when it was created, it would keep searching
  the old index forever after a rebuild.

**RT-10: the encoders are loaded only once.**
- **Given** one retriever, using encoders that count how many times they load
  their model.
- **When** the retriever is asked two different questions.
- **Then** each encoder has loaded its model exactly once.
- **Why:** loading a model takes several seconds. Doing it for every question
  would make every answer several seconds slower.

### Failures

**RT-11: an empty question is rejected before anything is sent to Qdrant.**
- **Given** a fake Qdrant that records every call made to it.
- **When** the code calls `retrieve("")`, and then `retrieve("   ")` (only spaces).
- **Then** each call raises a `ValueError`, and the fake Qdrant recorded no calls.
- **Why:** an empty question can't be answered. Sending it to Qdrant wastes a
  call and fails later with an error that's hard to understand.

**RT-12: problems with Qdrant give a clear error.**
- **Given** two situations: (a) a fake Qdrant that fails as if the server were
  down; (b) a real Qdrant where the `hippocampus` alias doesn't exist.
- **When** the code asks a question in each situation.
- **Then** both raise a `RetrievalError`. In (a) its message says "Qdrant is
  unreachable". In (b) it says "alias 'hippocampus' not found".
- **Why:** in row 5 the API turns a `RetrievalError` into an HTTP `503`
  ("service unavailable"). A raw error trace would tell the user nothing about
  what went wrong.

### Speed

**RT-13: one retrieval takes at most 500 ms.**
- **Given** the real `hippocampus` index, with the encoders already loaded.
- **When** the code asks 50 different questions, one after another, and times
  each one.
- **Then** 95% of them take 500 ms or less.
- **Why:** an answer must take at most 6 s in total, and most of that time goes
  to the LLM calls. Retrieval has to stay a small part of it.

## Reranking (row 6a)

An optional last step. Fusion ranks chunks by their positions in two lists; it
never reads the question and the chunk together. A cross-encoder does: it reads
each (question, chunk) pair and scores how well the chunk answers the question.
That is slower, so it only reorders the best fused chunks.

```
… RRF fusion ──► top 20 fused ──► cross-encoder scores each (question, chunk) ──► top 5
```

The reranker is off unless one is passed to the retriever, so everything above
works unchanged without it, and the eval can run both ways.

| Setting | Start | Why |
|---|---|---|
| model | `cross-encoder/ms-marco-MiniLM-L6-v2`, run locally on ONNX through FastEmbed (`Xenova/ms-marco-MiniLM-L-6-v2`) | small, free, no new dependency; on PyTorch the same model took p95 701 ms (RT-17 failed), so it runs on ONNX; a bigger one (`BAAI/bge-reranker-v2-m3`) only if the eval says this one isn't enough |
| chunks reranked | the top 20 after fusion | RT-7 showed the missed paper was among the candidates but below the top 5; 10 was tried to save time and lost most of the correctness gain ([decision 005](../../decisions/005-reranker.md)) |
| chunks returned | 5 | unchanged |

**RT-14: with a reranker, its scores decide the final order.**
- **Given** a fake Qdrant whose fused query returns 20 chunks, named c1 to c20
  in fused order, and a fake reranker that scores c20 highest, then c19, and
  so on down to c1.
- **When** a retriever built with that reranker is called with
  `retrieve("where are place cells?", k=5)`.
- **Then** the fake Qdrant was asked for 20 fused chunks; the fake reranker
  received the question and the texts of all 20; the result is c20, c19, c18,
  c17, c16 in that order, and each chunk's `score` is the reranker's score.
- **Why:** if the reranker saw only the top 5, it could reorder them but never
  lift a better chunk from position 12 into the answer, which is the whole
  point of adding it.

**RT-15: the real reranker keeps the right paper in the top 5.**
- **Given** the real `hippocampus` index and the same 20 known-paper questions
  as RT-7.
- **When** each question is asked with `k=5`, once without the reranker and
  once with it.
- **Then** with the reranker, at least 18 of the 20 find their paper in the top
  5. The test also reports both counts and which papers moved in or out of the
  top 5.
- **Why:** a reranker trained on web search (MS MARCO) may score neuroscience
  text badly. This catches it making known questions worse before the full eval
  is paid for.

**RT-16: the reranker loads its model only once.**
- **Given** one retriever with a reranker that counts how many times it loads
  its model.
- **When** the retriever is asked two different questions.
- **Then** the reranker has loaded its model exactly once.
- **Why:** like the encoders (RT-10), loading takes seconds; doing it per
  question would slow every answer.

**RT-17: one retrieval with reranking takes at most 750 ms.**
- **Given** the real `hippocampus` index, with the encoders and the reranker
  already loaded.
- **When** the code asks the same 50 questions as RT-13, with the reranker, one
  after another, and times each one.
- **Then** 95% of them take 750 ms or less.
- **Why:** retrieval must stay a small part of the 6 s answer. The reranker
  scores 20 chunks with a model, which RT-13's 500 ms can't fit on a 4-core
  CPU (561 ms measured); 750 ms leaves the answer under 6 s with generation's
  p95 of about 4.5 s ([decision 005](../../decisions/005-reranker.md)).

## Out of scope

- Judging whether the chunks are good enough to answer (grading, row 6).
- Rewriting the question (row 7).
- Filtering by paper, year or license.
