# Eval report: topic

50 runs, 0 failed, 0 judge calls failed, $0.26 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.76 | 1.00 | 0.89 | 0.72 | 0.86 | 1.00 | 0.17 | 3.0 | 5.0 | 0.0051 |
| borderline | 6 | – | 1.00 | – | – | – | – | 0.17 | 1.7 | 2.7 | 0.0026 |
| broad_vague | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 2.0 | 2.0 | 0.0044 |
| casual | 3 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.4 | 0.0062 |
| casual_loose_terms | 4 | 0.62 | 1.00 | 0.50 | 0.50 | 0.50 | – | – | 3.5 | 4.7 | 0.0066 |
| casual_multi_paper | 1 | 0.50 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.5 | 4.5 | 0.0079 |
| casual_typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.9 | 3.9 | 0.0069 |
| clinical_loose | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.0 | 4.0 | 0.0071 |
| direct | 7 | 0.79 | 1.00 | 0.86 | 0.57 | 0.86 | – | – | 2.7 | 4.9 | 0.0060 |
| direct_computational | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.2 | 3.2 | 0.0068 |
| direct_human | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.4 | 4.3 | 0.0070 |
| false_premise | 2 | 1.00 | 1.00 | 1.00 | 0.50 | 0.50 | – | – | 1.7 | 3.1 | 0.0051 |
| false_premise_casual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.4 | 3.4 | 0.0067 |
| false_premise_keywords | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.4 | 2.4 | 0.0059 |
| keywords | 1 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 5.0 | 5.0 | 0.0076 |
| keywords_typos | 2 | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 4.5 | 4.7 | 0.0079 |
| loose_terms | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.7 | 4.1 | 0.0068 |
| multi_paper | 2 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.1 | 5.1 | 0.0081 |
| negative_result | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.6 | 3.6 | 0.0068 |
| non_native_grammar | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.0 | 0.0062 |
| off_domain | 5 | – | – | – | – | – | 1.00 | – | 0.3 | 0.6 | 0.0000 |
| off_domain_casual | 1 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| out_of_corpus | 1 | – | – | – | – | – | 1.00 | – | 1.7 | 1.7 | 0.0023 |
| out_of_corpus_casual | 1 | – | – | – | – | – | 1.00 | – | 2.0 | 2.0 | 0.0025 |
| rambling_personal | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 5.1 | 5.1 | 0.0076 |
| typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 2.6 | 2.6 | 0.0058 |

## Not correct

- q02 r1 partial: The answer correctly identifies that Ank2 deletion impairs remote memory while leaving recent memory intact and disrupts LTP maintenance, but misses the mechanistic findings about reduced astrocyte contacts with engram neurons and impaired astrocyte morphogenesis through BDNF-TrkB.T1-IP3R2 signaling.
- q06 r1 wrong: The answer claims the papers don't address this question, but the reference answer demonstrates that the papers do directly address this topic by showing the pathway is selectively needed for appetitive spatial memory but not for escape location memory or other learning types.
- q12 r1 wrong: The answer contradicts the reference by stating that the evidence includes human studies with specific outcomes (24-week resistance training improving explicit long-term memory, working memory, and executive function in elderly individuals), when the reference explicitly states "The evidence in the corpus is from an animal model" and only describes rat studies.
- q13 r1 partial: The answer correctly identifies the main findings about hippocampus-dependent contextual episodic memory impairments in rats and the persistence of these effects despite dietary intervention in adulthood, but it omits the specific mechanistic finding about dysregulated acetylcholine signaling/altered cholinergic tone in the dorsal hippocampus that was highlighted in the reference answer.
- q15 r1 partial: The answer correctly describes that MAPK and cAMP signaling oscillate with circadian rhythm and that interfering with these oscillations impairs memory persistence, and mentions time-of-day effects on LTP, but it does not address the reference's key finding that mice lacking Bmal1 have impaired contextual fear and spatial memory and reduced Schaffer-collateral LTP.
- q16 r1 partial: The answer correctly identifies that astrocytic BDNF signaling supports memory persistence and mentions its role in both recent and remote memory, but it fails to specify the key molecular mechanisms described in the reference (TrkB.T1, IP3R2, ankyrin-2) and completely omits the role of PLCγ1 in CA2 neurons for visuosocial preference memory.
- q21 r1 partial: The answer correctly identifies hippocampal neurogenesis inhibition (marked by Ki-67/DCX decline within 24h) as the likely mechanism for memory deficits in object recognition and contextual fear conditioning, but it claims the effects are "temporary rather than permanent," which is not supported by the reference answer and introduces an unsubstantiated claim about transience.
- q24 r1 partial: The answer correctly identifies that bilateral lesions cause spatial memory deficits while unilateral lesions do not, but it contradicts the reference by stating that unilateral lesions did not differ from bilateral lesions, when the reference clearly states bilateral lesions had worse memory than controls while unilateral lesions did not differ from either group—meaning unilateral and control were similar, but bilateral was worse.
- q25 r1 partial: The answer correctly captures that memories don't simply "move out" of the hippocampus and that neural patterns change over time, and mentions vmPFC's role, but crucially omits the reference's key point that newer rodent evidence shows the hippocampus still actively contributes to remote memories even after post-learning lesions.
- q30 r1 partial: The answer correctly identifies the vmPFC's role in controlling memory integration versus separation in the hippocampus, but misses critical details from the reference including: the dependence on spatial context sharing, the temporal requirement (7 days vs 5 hours apart), the specific pathway through medial entorhinal cortex, and the involvement of neurogliaform inhibitory neurons in dorsal CA1.
- q31 r1 partial: The answer correctly identifies the hippocampus's role in separating overlapping memories and provides specific details about the dentate gyrus, but it does not mention the neocortical GABA inhibition mechanism that the reference answer identifies as a key protection against memory interference.
- q33 r1 wrong: The answer claims the documents don't contain specific information about anterior vs. posterior hippocampal functions during pair memory, directly contradicting the reference answer which provides detailed findings about rostral encoding and caudal retrieval for associative memory pairs.
- q36 r1 wrong: The answer claims the papers don't address the question at all, but the reference explicitly states the corpus covers relevant mechanisms including astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal MAPK/cAMP signaling, and CA1 place cell stability that support memory persistence over weeks.

## Unfaithful


## Loop

| kind | runs | declined | rewrites (mean) | web used | not covered |
|---|---|---|---|---|---|
| answer_from_corpus | 32 | 0 | 0.00 | 0 | 0 |
| correct_premise | 4 | 0 | 0.00 | 0 | 0 |
| decline | 6 | 6 | 0.00 | 0 | 0 |
| not_declined | 6 | 0 | 0.00 | 0 | 0 |
| web_fallback | 2 | 0 | 0.00 | 0 | 0 |

Paths:

- q01 answer_from_corpus: retrieve → generate
- q02 answer_from_corpus: retrieve → generate
- q03 answer_from_corpus: retrieve → generate
- q04 answer_from_corpus: retrieve → generate
- q05 answer_from_corpus: retrieve → generate
- q06 answer_from_corpus: retrieve → generate
- q07 answer_from_corpus: retrieve → generate
- q08 answer_from_corpus: retrieve → generate
- q09 answer_from_corpus: retrieve → generate
- q10 answer_from_corpus: retrieve → generate
- q11 answer_from_corpus: retrieve → generate
- q12 answer_from_corpus: retrieve → generate
- q13 answer_from_corpus: retrieve → generate
- q14 answer_from_corpus: retrieve → generate
- q15 answer_from_corpus: retrieve → generate
- q16 answer_from_corpus: retrieve → generate
- q17 correct_premise: retrieve → generate
- q18 correct_premise: retrieve → generate
- q19 web_fallback: retrieve → generate
- q20 decline: declined
- q21 answer_from_corpus: retrieve → generate
- q22 answer_from_corpus: retrieve → generate
- q23 answer_from_corpus: retrieve → generate
- q24 answer_from_corpus: retrieve → generate
- q25 answer_from_corpus: retrieve → generate
- q26 answer_from_corpus: retrieve → generate
- q27 answer_from_corpus: retrieve → generate
- q28 answer_from_corpus: retrieve → generate
- q29 answer_from_corpus: retrieve → generate
- q30 answer_from_corpus: retrieve → generate
- q31 answer_from_corpus: retrieve → generate
- q32 answer_from_corpus: retrieve → generate
- q33 answer_from_corpus: retrieve → generate
- q34 answer_from_corpus: retrieve → generate
- q35 answer_from_corpus: retrieve → generate
- q36 answer_from_corpus: retrieve → generate
- q41 correct_premise: retrieve → generate
- q42 correct_premise: retrieve → generate
- q43 web_fallback: retrieve → generate
- q44 decline: declined
- q45 not_declined: retrieve → generate
- q46 not_declined: retrieve → generate
- q47 not_declined: retrieve → generate
- q48 not_declined: retrieve → generate
- q49 not_declined: retrieve → generate
- q50 not_declined: retrieve → generate
- q51 decline: declined
- q52 decline: declined
- q53 decline: declined
- q54 decline: declined
