# Eval report: crag3

50 runs, 0 failed, 0 judge calls failed, $0.28 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.79 | 0.98 | 0.92 | 0.75 | 0.92 | 0.75 | 1.00 | 4.2 | 21.5 | 0.0056 |
| borderline | 6 | – | 1.00 | – | – | – | – | 1.00 | 20.7 | 22.7 | 0.0051 |
| broad_vague | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 4.2 | 4.2 | 0.0044 |
| casual | 3 | 0.83 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.9 | 3.9 | 0.0067 |
| casual_loose_terms | 4 | 0.88 | 1.00 | 0.75 | 0.75 | 0.75 | – | – | 4.1 | 5.1 | 0.0067 |
| casual_multi_paper | 1 | 0.50 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.3 | 4.3 | 0.0072 |
| casual_typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.1 | 3.1 | 0.0062 |
| clinical_loose | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.5 | 4.5 | 0.0072 |
| direct | 7 | 0.71 | 1.00 | 0.86 | 0.57 | 0.86 | – | – | 3.2 | 20.5 | 0.0061 |
| direct_computational | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 3.5 | 0.0067 |
| direct_human | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.6 | 4.3 | 0.0070 |
| false_premise | 2 | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 6.7 | 14.4 | 0.0062 |
| false_premise_casual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.3 | 3.3 | 0.0062 |
| false_premise_keywords | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 25.1 | 25.1 | 0.0060 |
| keywords | 1 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 5.0 | 5.0 | 0.0078 |
| keywords_typos | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 4.2 | 5.5 | 0.0080 |
| loose_terms | 2 | 0.75 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.1 | 4.3 | 0.0068 |
| multi_paper | 2 | 0.50 | 0.50 | 1.00 | 1.00 | 1.00 | – | – | 4.5 | 5.0 | 0.0081 |
| negative_result | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.8 | 3.8 | 0.0068 |
| non_native_grammar | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.6 | 3.6 | 0.0063 |
| off_domain | 5 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| off_domain_casual | 1 | – | – | – | – | – | 1.00 | – | 0.2 | 0.2 | 0.0000 |
| out_of_corpus | 1 | – | 1.00 | – | – | – | 0.00 | – | 15.8 | 15.8 | 0.0050 |
| out_of_corpus_casual | 1 | – | 1.00 | – | – | – | 0.00 | – | 19.3 | 19.3 | 0.0057 |
| rambling_personal | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.3 | 4.3 | 0.0069 |
| typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.0 | 0.0059 |

## Not correct

- q02 r1 partial: The answer correctly identifies that Ank2 deletion impairs remote memory while leaving recent memory intact and disrupts LTP maintenance, but it omits the mechanistic details about reduced astrocyte contacts with engram neurons and impaired astrocyte morphogenesis driven by BDNF signaling through TrkB.T1 and IP3R2.
- q06 r1 wrong: The answer claims the papers don't address spatial memory and the ventral hippocampus to lateral septum pathway, but the reference clearly demonstrates this pathway does have a role in selective forms of spatial memory (appetitive but not aversive), making this a case where the answerer failed to identify relevant content in the papers.
- q11 r1 partial: The answer correctly identifies that cofilin overactivation improves short-term memory in the object-location task and doesn't affect anxiety-like behavior, but it omits the key finding that AMPA receptor expression levels were not changed despite the memory improvement.
- q14 r1 partial: The answer correctly states that mice can form visuosocial memories from visual images of other mice and that they can generalize these memories across different stimuli, but it fails to mention the key mechanistic finding about PLCγ1 in hippocampal CA2 being required for this memory and misses the distinction that avoidance memory does not require this pathway.
- q15 r1 partial: The answer correctly describes the circadian oscillation of MAPK and cAMP signaling in the hippocampus and how interfering with these oscillations impairs memory, but it omits key evidence about Bmal1 knockout mice (impaired contextual fear and spatial memory, reduced Schaffer-collateral LTP, and loss of training-induced Erk1/2 MAPK activation), which is a central finding in the reference answer.
- q16 r1 partial: The answer correctly identifies astrocytic BDNF signaling, ankyrin-2, TrkB.T1, remote memory enhancement, and PLCγ1 as a downstream molecule, but fails to specify that PLCγ1 is required for visuosocial preference memory in CA2 neurons, missing a key cell-type-specific finding from the reference.
- q21 r1 partial: The answer correctly identifies object recognition memory deficits at 1 and 7 days post-irradiation and the connection to reduced hippocampal neurogenesis, but it misses the reference's finding about contextual fear conditioning deficits and incorrectly suggests the effects are temporary rather than what the reference implies about deficits at multiple timepoints.
- q25 r1 partial: The answer correctly captures that memory representations change across brain regions over time and mentions vmPFC becoming more evident, but it misses the key reference finding that newer rodent evidence contradicts the classic systems-consolidation view by showing the hippocampus still actively contributes to remote memories.
- q29 r1 partial: The answer correctly identifies the core finding about transferring firing patterns via electrical stimulation to enhance memory performance in naive recipients, but it omits the key reference answer detail that this facilitation occurred specifically on "difficult long-delay trials" in a short-term memory task.
- q30 r1 partial: The answer correctly identifies that the vmPFC controls memory integration versus separation in the hippocampus, but misses key mechanistic details provided in the reference: the dependence on spatial context, the timing requirement (7 days vs 5 hours), the role of medial entorhinal cortex projections, and the involvement of neurogliaform inhibitory neurons in dorsal CA1.
- q31 r1 partial: The answer correctly identifies the hippocampus's role in separating overlapping memories through relational information (via the dentate gyrus), but it fails to mention the neocortical GABAergic inhibition mechanism that the reference identifies as a key way to prevent interference between overlapping memories.
- q35 r1 partial: The answer correctly identifies that Ythdf1 depletion causes impaired synaptic transmission and LTP, which contributes to learning and memory defects, but it misses the key mechanism that Ythdf1 reads m6A marks and promotes stimulus-dependent translation of target mRNAs in hippocampal neurons, and does not mention that hippocampal re-expression rescues these deficits.
- q36 r1 wrong: The answer claims the papers don't cover the topic at all, but the reference explicitly states the corpus addresses parts of this question including specific mechanisms like astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal MAPK/cAMP signaling, and CA1 place cell stability that support memory persistence.

## Unfaithful

- q16 r1: "BDNF is crucial for both recent and remote memory formation, with a particularly important role in supporting memory persistence through its activity around 12 h after learning [2]."

## Loop

| kind | runs | declined | rewrites (mean) | web used | not covered |
|---|---|---|---|---|---|
| answer_from_corpus | 32 | 0 | 0.12 | 1 | 0 |
| correct_premise | 4 | 0 | 1.50 | 0 | 0 |
| decline | 6 | 6 | 0.00 | 0 | 0 |
| not_declined | 6 | 0 | 1.67 | 5 | 0 |
| web_fallback | 2 | 0 | 2.00 | 2 | 0 |

Paths:

- q01 answer_from_corpus: retrieve → grade:good → generate
- q02 answer_from_corpus: retrieve → grade:good → generate
- q03 answer_from_corpus: retrieve → grade:good → generate
- q04 answer_from_corpus: retrieve → grade:good → generate
- q05 answer_from_corpus: retrieve → grade:good → generate
- q06 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q07 answer_from_corpus: retrieve → grade:good → generate
- q08 answer_from_corpus: retrieve → grade:good → generate
- q09 answer_from_corpus: retrieve → grade:good → generate
- q10 answer_from_corpus: retrieve → grade:good → generate
- q11 answer_from_corpus: retrieve → grade:good → generate
- q12 answer_from_corpus: retrieve → grade:good → generate
- q13 answer_from_corpus: retrieve → grade:good → generate
- q14 answer_from_corpus: retrieve → grade:good → generate
- q15 answer_from_corpus: retrieve → grade:good → generate
- q16 answer_from_corpus: retrieve → grade:good → generate
- q17 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → fallback → generate
- q18 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q19 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q20 decline: declined
- q21 answer_from_corpus: retrieve → grade:good → generate
- q22 answer_from_corpus: retrieve → grade:good → generate
- q23 answer_from_corpus: retrieve → grade:good → generate
- q24 answer_from_corpus: retrieve → grade:good → generate
- q25 answer_from_corpus: retrieve → grade:good → generate
- q26 answer_from_corpus: retrieve → grade:good → generate
- q27 answer_from_corpus: retrieve → grade:good → generate
- q28 answer_from_corpus: retrieve → grade:good → generate
- q29 answer_from_corpus: retrieve → grade:good → generate
- q30 answer_from_corpus: retrieve → grade:good → generate
- q31 answer_from_corpus: retrieve → grade:good → generate
- q32 answer_from_corpus: retrieve → grade:good → generate
- q33 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q34 answer_from_corpus: retrieve → grade:good → generate
- q35 answer_from_corpus: retrieve → grade:good → generate
- q36 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
- q41 correct_premise: retrieve → grade:good → generate
- q42 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → fallback → generate
- q43 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q44 decline: declined
- q45 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q46 not_declined: retrieve → grade:good → generate
- q47 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q48 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q49 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q50 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q51 decline: declined
- q52 decline: declined
- q53 decline: declined
- q54 decline: declined
