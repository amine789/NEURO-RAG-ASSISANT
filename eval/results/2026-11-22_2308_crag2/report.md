# Eval report: crag2

50 runs, 0 failed, 0 judge calls failed, $0.27 total

| questions | runs | correctness | faithful | paper@5 | page@5 | cites expected | not covered | cites papers | p50 s | p95 s | $ per run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 50 | 0.71 | 0.97 | 0.94 | 0.81 | 0.89 | 0.75 | 0.67 | 4.2 | 20.7 | 0.0053 |
| borderline | 6 | – | 1.00 | – | – | – | – | 0.67 | 18.9 | 25.2 | 0.0041 |
| broad_vague | 1 | 0.00 | – | 0.00 | 0.00 | 0.00 | – | – | 3.5 | 3.5 | 0.0041 |
| casual | 3 | 0.33 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.0 | 4.0 | 0.0067 |
| casual_loose_terms | 4 | 0.75 | 1.00 | 0.75 | 0.75 | 0.75 | – | – | 4.0 | 4.9 | 0.0067 |
| casual_multi_paper | 1 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.8 | 4.8 | 0.0078 |
| casual_typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.5 | 3.5 | 0.0062 |
| clinical_loose | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.3 | 4.3 | 0.0068 |
| direct | 7 | 0.71 | 1.00 | 1.00 | 0.71 | 1.00 | – | – | 3.6 | 5.0 | 0.0063 |
| direct_computational | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.3 | 3.3 | 0.0067 |
| direct_human | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.9 | 4.5 | 0.0070 |
| false_premise | 2 | 0.50 | 1.00 | 1.00 | 1.00 | 0.50 | – | – | 6.6 | 14.0 | 0.0037 |
| false_premise_casual | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.3 | 3.3 | 0.0063 |
| false_premise_keywords | 1 | 0.00 | – | 1.00 | 1.00 | 0.00 | – | – | 16.6 | 16.6 | 0.0014 |
| keywords | 1 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | – | – | 4.7 | 4.7 | 0.0071 |
| keywords_typos | 2 | 0.75 | 1.00 | 1.00 | 0.50 | 1.00 | – | – | 4.9 | 5.0 | 0.0076 |
| loose_terms | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.2 | 4.6 | 0.0070 |
| multi_paper | 2 | 0.50 | 0.50 | 1.00 | 1.00 | 1.00 | – | – | 5.2 | 5.3 | 0.0084 |
| negative_result | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.8 | 3.8 | 0.0068 |
| non_native_grammar | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.7 | 3.7 | 0.0063 |
| off_domain | 5 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| off_domain_casual | 1 | – | – | – | – | – | 1.00 | – | 0.3 | 0.3 | 0.0000 |
| out_of_corpus | 1 | – | 1.00 | – | – | – | 0.00 | – | 16.6 | 16.6 | 0.0041 |
| out_of_corpus_casual | 1 | – | 1.00 | – | – | – | 0.00 | – | 20.7 | 20.7 | 0.0057 |
| rambling_personal | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 4.8 | 4.8 | 0.0073 |
| typos | 1 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | – | – | 3.0 | 3.0 | 0.0059 |

## Not correct

- q02 r1 partial: The answer correctly identifies that ankyrin-2 deletion impairs remote memory while leaving recent memory intact and disrupts LTP maintenance, but it omits the mechanistic details about reduced astrocyte contacts with engram neurons and impaired astrocyte morphogenesis driven by BDNF signaling.
- q05 r1 partial: The answer correctly identifies that GHS-R1a elevation impairs memory formation by suppressing neuronal excitability, blocking memory allocation, hampering spatial coding, and reducing engram size, but it omits the key finding that the endogenous antagonist LEAP2 abolishes the impairment and that chemogenetic activation of high-GHS-R1a neurons rescues the deficit.
- q06 r1 partial: The answer correctly identifies that the ventral hippocampus-to-lateral septum pathway is selective and not needed for escape/aversive spatial memory, but it omits the reference's key finding that the pathway also does not affect food intake or social/olfactory appetitive learning, only describing it as selective for "appetitive spatial memory" generally.
- q11 r1 partial: The answer correctly captures the main finding that cofilin overactivation improves short-term memory in the object-location memory task and does not affect anxiety-like behavior, but it omits the reference answer's notable detail that cofilin overactivation surprisingly does not change AMPA receptor expression levels.
- q12 r1 wrong: The answer contradicts the reference by claiming evidence from human studies when the reference explicitly states "The evidence in the corpus is from an animal model" and only describes rat studies.
- q13 r1 partial: The answer correctly identifies the main rat study findings (cafeteria-style diet causing persistent hippocampus-dependent contextual episodic memory impairments that persist despite diet intervention), but omits the specific mechanistic detail about dysregulated acetylcholine signaling in the dorsal hippocampus that was mentioned in the reference answer.
- q14 r1 partial: The answer correctly identifies that mice can form visuosocial memories and remember other mice from pictures, and discusses preference/avoidance learning, but it focuses primarily on avoidance memory and fails to mention the key finding about preference memory, the role of PLCγ1 in hippocampal CA2, and the distinction between preference and avoidance memory mechanisms.
- q15 r1 partial: The answer correctly identifies the MAPK and cAMP oscillations and their role in memory persistence, and mentions hippocampal LTP's time-of-day dependence, but fails to address the reference's key finding that mice lacking Bmal1 have impaired contextual fear and spatial memory with reduced Schaffer-collateral LTP and loss of training-induced Erk1/2 MAPK activation.
- q16 r1 partial: The answer correctly identifies BDNF's role in memory persistence through astrocytic TrkB.T1 signaling and ankyrin-2, as well as optogenetic activation enhancing remote memory, but it fails to mention the critical finding that PLCγ1 in CA2 neurons is required for visuosocial preference memory, which is a main specific finding in the reference answer.
- q17 r1 wrong: The answer fails to engage with the question and doesn't correct the false premise that CPEB4 knockout abolishes LTP and memory, which the reference answer identifies as incorrect.
- q21 r1 partial: The answer correctly identifies that fast neutron irradiation causes object recognition memory deficits measured at 1 and 7 days post-irradiation and mentions reduced hippocampal neurogenesis as a potential mechanism, but it adds an unsupported claim that "the effects are temporary rather than permanent" which is not established in the reference answer.
- q30 r1 partial: The answer correctly identifies the ventromedial PFC's role in controlling memory integration versus separation in the hippocampus, but misses key details from the reference about the conditions (shared spatial context, 7-day but not 5-hour intervals) and the specific neural mechanisms (projections to medial entorhinal cortex, effects on hippocampal neuron recruitment and neurogliaform inhibitory neurons in dorsal CA1).
- q31 r1 partial: The answer correctly identifies hippocampal mechanisms (specifically the dentate gyrus) for separating similar memories and discusses pattern separation, but misses the reference's key finding about neocortical GABAergic inhibition as a mechanism that protects overlapping memories from interference, and explicitly states that modulation mechanisms are "poorly understood" rather than presenting the established neocortical mechanism.
- q33 r1 partial: The answer correctly identifies that the rostral hippocampus is active during encoding and the caudal hippocampus during retrieval for associative memory, matching the reference's main findings, but misses other important details from the reference such as recognition memory encoding selectively activating the rostral hippocampus, gamma power increases, and congruence modulating low-frequency activity in the caudal hippocampus.
- q35 r1 partial: The answer correctly identifies key consequences (impaired LTP, reduced synaptic protein synthesis, learning defects) but misses the reference's core mechanistic finding that Ythdf1 reads m6A marks to promote stimulus-dependent translation of target mRNAs.
- q36 r1 wrong: The answer incorrectly claims the papers don't cover this topic, when the reference indicates the corpus does address parts of it, including specific mechanisms like astrocytic ankyrin-2, BDNF/TrkB.T1 signaling, circadian oscillations of hippocampal MAPK/cAMP signaling, and CA1 place cell stability.
- q42 r1 wrong: The answer claims the papers don't cover PDE1B and memory, but the reference answer directly addresses the question with specific findings from the literature showing that blocking PDE1B enhances (not worsens) memory and that the question's premise is incorrect.

## Unfaithful

- q16 r1: "BDNF is crucial for both recent and remote memory formation, with a particularly important role in supporting memory persistence through its activity around 12 h after learning"

## Loop

| kind | runs | declined | rewrites (mean) | web used | not covered |
|---|---|---|---|---|---|
| answer_from_corpus | 32 | 0 | 0.09 | 0 | 0 |
| correct_premise | 4 | 0 | 1.50 | 0 | 2 |
| decline | 6 | 6 | 0.00 | 0 | 0 |
| not_declined | 6 | 0 | 1.67 | 4 | 1 |
| web_fallback | 2 | 0 | 2.00 | 2 | 0 |

Paths:

- q01 answer_from_corpus: retrieve → grade:good → generate
- q02 answer_from_corpus: retrieve → grade:good → generate
- q03 answer_from_corpus: retrieve → grade:good → generate
- q04 answer_from_corpus: retrieve → grade:good → generate
- q05 answer_from_corpus: retrieve → grade:good → generate
- q06 answer_from_corpus: retrieve → grade:weak → rewrite → retrieve → grade:good → generate
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
- q17 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
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
- q42 correct_premise: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q43 web_fallback: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q44 decline: declined
- q45 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q46 not_declined: retrieve → grade:good → generate
- q47 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:weak → not_covered
- q48 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q49 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q50 not_declined: retrieve → grade:weak → rewrite → retrieve → grade:weak → rewrite → retrieve → grade:weak → web → grade:good → generate
- q51 decline: declined
- q52 decline: declined
- q53 decline: declined
- q54 decline: declined
